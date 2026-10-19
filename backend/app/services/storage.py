"""
services/storage.py - Multi-Backend Medical Document Storage Service
======================================================================

Provides an abstracted storage interface with implementations for:
  1. LocalStorageProvider: Local filesystem storage for development and persistent disk mounts.
  2. S3StorageProvider: Private S3-compatible object storage (AWS S3, Cloudflare R2, MinIO, Wasabi).
  3. Pluggable BaseStorageProvider: Clean abstraction preventing filesystem path leakage to clients.
  4. Production Safety Guard: Refuses to silently use ephemeral container storage in production.

Security Controls:
  - Non-guessable UUID tokens prefixed to storage keys.
  - Strict path traversal defense (canonical relative path verification).
  - Allowed extension whitelist (.pdf, .png, .jpg, .jpeg, .csv, .xlsx).
  - 15MB file size limit enforced before disk write or S3 upload.
  - Zero exposure of local paths or public object URLs.
"""

import os
import uuid
import re
import io
import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Optional

# Supported extensions and default max size (15MB)
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".csv", ".xlsx"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB

DEFAULT_UPLOAD_DIR = os.environ.get(
    "GLUCOTWIN_UPLOAD_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "uploads")
)


def sanitize_filename(filename: str) -> str:
    """Sanitize the original filename to prevent path traversal or special characters."""
    base = os.path.basename(filename)
    clean = re.sub(r"[^A-Za-z0-9_.-]", "_", base)
    return clean[:120] if len(clean) > 120 else clean


class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class FileValidationError(StorageError):
    """Raised when an uploaded file violates size, extension, or safety rules."""
    pass


class StorageConfigurationError(StorageError):
    """Raised when storage configuration is invalid or missing required credentials/buckets."""
    pass


class BaseStorageProvider(ABC):
    """Abstract storage provider interface."""

    @abstractmethod
    def save_file(self, file_bytes: bytes, original_filename: str) -> Tuple[str, str, int]:
        """
        Saves bytes and returns:
          (storage_filename, storage_path_or_uri, file_size_bytes)
        """
        pass

    @abstractmethod
    def get_file_bytes(self, storage_filename: str) -> bytes:
        """Retrieves file content as bytes for preview, parsing, or streaming download."""
        pass

    @abstractmethod
    def get_file_path(self, storage_filename: str) -> Optional[Path]:
        """Resolves local filesystem path if available, or None for pure remote storage."""
        pass

    @abstractmethod
    def delete_file(self, storage_filename: str) -> bool:
        """Deletes a file if present. Returns True if deleted, False otherwise."""
        pass

    @abstractmethod
    def file_exists(self, storage_filename: str) -> bool:
        """Checks if a storage file exists."""
        pass


class LocalStorageProvider(BaseStorageProvider):
    """
    Local filesystem storage provider for development and persistent disk mounts.
    In cloud environments (e.g. Render Persistent Disk), upload_dir points to the mounted volume.
    """

    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = Path(os.path.abspath(upload_dir or DEFAULT_UPLOAD_DIR)).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _validate_file(self, original_filename: str, file_bytes: bytes) -> str:
        size = len(file_bytes)
        if size > MAX_FILE_SIZE_BYTES:
            raise FileValidationError(
                f"File size {size / (1024 * 1024):.2f}MB exceeds the 15MB upload limit."
            )
        if size == 0:
            raise FileValidationError("Uploaded file is empty (0 bytes).")

        ext = Path(original_filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise FileValidationError(
                f"Unsupported file extension '{ext}'. Supported formats: {allowed_str}"
            )
        return ext

    def _resolve_safe_path(self, storage_filename: str) -> Path:
        """Ensure no path traversal occurs."""
        candidate = (self.upload_dir / storage_filename).resolve()
        try:
            candidate.relative_to(self.upload_dir)
        except ValueError:
            raise FileValidationError("Invalid filename: path traversal attempted.")
        return candidate

    def save_file(self, file_bytes: bytes, original_filename: str) -> Tuple[str, str, int]:
        size = len(file_bytes)
        ext = self._validate_file(original_filename, file_bytes)
        safe_name = sanitize_filename(original_filename)
        unique_token = uuid.uuid4().hex
        storage_filename = f"{unique_token}_{safe_name}"

        target_path = self._resolve_safe_path(storage_filename)
        with open(target_path, "wb") as f:
            f.write(file_bytes)

        return storage_filename, str(target_path), size

    def get_file_bytes(self, storage_filename: str) -> bytes:
        target_path = self._resolve_safe_path(storage_filename)
        if not target_path.exists() or not target_path.is_file():
            raise StorageError(f"Stored file '{storage_filename}' does not exist on disk.")
        with open(target_path, "rb") as f:
            return f.read()

    def get_file_path(self, storage_filename: str) -> Optional[Path]:
        target_path = self._resolve_safe_path(storage_filename)
        if not target_path.exists() or not target_path.is_file():
            raise StorageError(f"Stored file '{storage_filename}' does not exist on disk.")
        return target_path

    def delete_file(self, storage_filename: str) -> bool:
        try:
            target_path = self._resolve_safe_path(storage_filename)
            if target_path.exists() and target_path.is_file():
                target_path.unlink()
                return True
        except Exception:
            return False
        return False

    def file_exists(self, storage_filename: str) -> bool:
        try:
            target_path = self._resolve_safe_path(storage_filename)
            return target_path.exists() and target_path.is_file()
        except Exception:
            return False


class S3StorageProvider(BaseStorageProvider):
    """
    Private S3-compatible object storage provider for production environments.
    Works with AWS S3, Cloudflare R2, MinIO, Wasabi, or Backblaze B2.
    """

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
        endpoint_url: Optional[str] = None,
        client=None,
    ):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.region_name = region_name

        if client is not None:
            self.s3_client = client
        else:
            try:
                import boto3
                session = boto3.session.Session()
                self.s3_client = session.client(
                    "s3",
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name,
                    endpoint_url=endpoint_url,
                )
            except ImportError:
                raise StorageConfigurationError(
                    "boto3 library is required for S3StorageProvider. Install via `pip install boto3`."
                )
            except Exception as e:
                raise StorageConfigurationError(f"Failed to initialize S3 client: {str(e)}")

    def _validate_file(self, original_filename: str, file_bytes: bytes) -> str:
        size = len(file_bytes)
        if size > MAX_FILE_SIZE_BYTES:
            raise FileValidationError(
                f"File size {size / (1024 * 1024):.2f}MB exceeds the 15MB upload limit."
            )
        if size == 0:
            raise FileValidationError("Uploaded file is empty (0 bytes).")

        ext = Path(original_filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise FileValidationError(
                f"Unsupported file extension '{ext}'. Supported formats: {allowed_str}"
            )
        return ext

    def save_file(self, file_bytes: bytes, original_filename: str) -> Tuple[str, str, int]:
        size = len(file_bytes)
        ext = self._validate_file(original_filename, file_bytes)
        safe_name = sanitize_filename(original_filename)
        unique_token = uuid.uuid4().hex
        storage_filename = f"{unique_token}_{safe_name}"

        content_type, _ = mimetypes.guess_type(original_filename)
        content_type = content_type or "application/octet-stream"

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_filename,
                Body=file_bytes,
                ContentType=content_type,
            )
        except Exception as e:
            raise StorageError(f"Failed to persist document to S3 bucket '{self.bucket_name}': {str(e)}")

        storage_uri = f"s3://{self.bucket_name}/{storage_filename}"
        return storage_filename, storage_uri, size

    def get_file_bytes(self, storage_filename: str) -> bytes:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=storage_filename)
            return response["Body"].read()
        except Exception as e:
            raise StorageError(f"Failed to retrieve document '{storage_filename}' from S3: {str(e)}")

    def get_file_path(self, storage_filename: str) -> Optional[Path]:
        # S3 storage does not provide local path directly
        return None

    def delete_file(self, storage_filename: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=storage_filename)
            return True
        except Exception:
            return False

    def file_exists(self, storage_filename: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=storage_filename)
            return True
        except Exception:
            return False


def get_storage_provider() -> BaseStorageProvider:
    """
    Factory function resolving storage provider with environment guards.
    Refuses to silently fall back to ephemeral local storage in production.
    """
    provider_type = os.environ.get("GLUCOTWIN_STORAGE_PROVIDER", "local").strip().lower()
    environment = os.environ.get("ENVIRONMENT", "development").strip().lower()

    if provider_type in ("s3", "aws_s3", "s3_compatible"):
        bucket = os.environ.get("GLUCOTWIN_S3_BUCKET")
        if not bucket:
            raise StorageConfigurationError(
                "GLUCOTWIN_STORAGE_PROVIDER='s3' is configured, but GLUCOTWIN_S3_BUCKET is missing."
            )
        return S3StorageProvider(
            bucket_name=bucket,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            endpoint_url=os.environ.get("GLUCOTWIN_S3_ENDPOINT_URL"),
        )

    # In production, local storage must use an explicitly mounted persistent volume
    if environment in ("production", "prod"):
        persistent_dir = os.environ.get("GLUCOTWIN_UPLOAD_DIR")
        if not persistent_dir:
            raise StorageConfigurationError(
                "CRITICAL DEPLOYMENT SAFETY ERROR: Running in production mode (ENVIRONMENT=production), "
                "but no persistent storage backend is configured! Ephemeral container disk storage will lose "
                "uploaded patient documents on restart or redeploy. Set GLUCOTWIN_STORAGE_PROVIDER='s3' or "
                "specify a persistent volume mount path via GLUCOTWIN_UPLOAD_DIR."
            )
        return LocalStorageProvider(upload_dir=persistent_dir)

    return LocalStorageProvider()


# Resolve active storage provider with fail-closed production safety
_env = os.environ.get("ENVIRONMENT", "development").strip().lower()
if _env in ("production", "prod"):
    # In production, never swallow configuration errors or silently fall back
    storage_provider = get_storage_provider()
else:
    # In development/test mode, fall back safely to local storage
    try:
        storage_provider = get_storage_provider()
    except Exception:
        storage_provider = LocalStorageProvider()
