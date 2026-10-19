"""
test_persistent_storage.py - Multi-Backend Storage & Production Persistence Tests
===================================================================================

Tests verified:
  1. LocalStorageProvider: file saving, content byte retrieval, existence check, deletion.
  2. LocalStorageProvider: path traversal rejection and safe resolution.
  3. LocalStorageProvider: oversized (>15MB) and empty (0-byte) file rejection.
  4. S3StorageProvider: object storage lifecycle (put, get_bytes, head, delete) with mock S3 client.
  5. S3StorageProvider: handles missing S3 bucket or invalid credentials via StorageConfigurationError.
  6. Production Safety Guard: Running in production without configured persistent storage
     raises StorageConfigurationError and refuses silent fallback to ephemeral disk.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock

from app.services.storage import (
    LocalStorageProvider,
    S3StorageProvider,
    FileValidationError,
    StorageError,
    StorageConfigurationError,
    get_storage_provider,
)


def test_local_storage_lifecycle(tmp_path):
    """Test standard save, read, exists, and delete operations on local storage."""
    storage = LocalStorageProvider(upload_dir=str(tmp_path))
    content = b"PDF-1.4 simulated medical laboratory report bytes"

    # Save
    storage_name, storage_path, size = storage.save_file(content, "quarterly_labs.pdf")
    assert size == len(content)
    assert storage.file_exists(storage_name) is True
    assert Path(storage_path).exists()

    # Read bytes
    retrieved = storage.get_file_bytes(storage_name)
    assert retrieved == content

    # Delete
    assert storage.delete_file(storage_name) is True
    assert storage.file_exists(storage_name) is False

    # Reading deleted file raises StorageError
    with pytest.raises(StorageError):
        storage.get_file_bytes(storage_name)


def test_local_storage_path_traversal_defense(tmp_path):
    """Test that directory traversal attempts are safely sanitized or rejected."""
    storage = LocalStorageProvider(upload_dir=str(tmp_path))
    content = b"sample content"

    # Save file with traversal characters in filename
    storage_name, storage_path, _ = storage.save_file(content, "../../../evil.pdf")

    # The stored path must resolve strictly inside tmp_path
    resolved = Path(storage_path).resolve()
    assert tmp_path.resolve() in resolved.parents


def test_local_storage_file_validations(tmp_path):
    """Test rejection of unsupported extensions, empty files, and oversized files."""
    storage = LocalStorageProvider(upload_dir=str(tmp_path))

    # 1. Unsupported extension (.exe)
    with pytest.raises(FileValidationError) as exc:
        storage.save_file(b"bad", "malicious.exe")
    assert "Unsupported file extension" in str(exc.value)

    # 2. Empty file
    with pytest.raises(FileValidationError) as exc:
        storage.save_file(b"", "empty.pdf")
    assert "empty (0 bytes)" in str(exc.value)

    # 3. Oversized file (> 15MB)
    oversized = b"X" * (15 * 1024 * 1024 + 10)
    with pytest.raises(FileValidationError) as exc:
        storage.save_file(oversized, "huge.pdf")
    assert "exceeds the 15MB upload limit" in str(exc.value)


def test_s3_storage_provider_lifecycle():
    """Test S3StorageProvider operations using a mocked S3 client."""
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {
        "Body": MagicMock(read=lambda: b"S3 object medical bytes content")
    }

    provider = S3StorageProvider(
        bucket_name="my-medical-bucket",
        client=mock_s3,
    )
    content = b"S3 object medical bytes content"

    # Save to S3
    storage_name, storage_uri, size = provider.save_file(content, "patient_report.pdf")
    assert size == len(content)
    assert storage_uri.startswith("s3://my-medical-bucket/")
    assert mock_s3.put_object.called

    # Get from S3
    retrieved = provider.get_file_bytes(storage_name)
    assert retrieved == content
    assert mock_s3.get_object.called

    # File exists check
    mock_s3.head_object.return_value = {}
    assert provider.file_exists(storage_name) is True

    # Delete from S3
    assert provider.delete_file(storage_name) is True
    assert mock_s3.delete_object.called


def test_s3_storage_missing_bucket_raises_config_error(monkeypatch):
    """Verify that specifying provider='s3' without GLUCOTWIN_S3_BUCKET raises an explicit error."""
    monkeypatch.setenv("GLUCOTWIN_STORAGE_PROVIDER", "s3")
    monkeypatch.delenv("GLUCOTWIN_S3_BUCKET", raising=False)

    with pytest.raises(StorageConfigurationError) as exc:
        get_storage_provider()
    assert "GLUCOTWIN_S3_BUCKET is missing" in str(exc.value)


def test_production_ephemeral_storage_refusal(monkeypatch):
    """
    CRITICAL SAFETY GUARD:
    Verify that running in production mode (ENVIRONMENT=production) with default local storage
    and no persistent volume mount directory explicitly raises StorageConfigurationError,
    preventing silent patient document loss on ephemeral container restarts.
    """
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("GLUCOTWIN_STORAGE_PROVIDER", "local")
    monkeypatch.delenv("GLUCOTWIN_UPLOAD_DIR", raising=False)

    with pytest.raises(StorageConfigurationError) as exc:
        get_storage_provider()
    assert "CRITICAL DEPLOYMENT SAFETY ERROR" in str(exc.value)
    assert "Ephemeral container disk storage will lose uploaded patient documents" in str(exc.value)


def test_production_storage_fails_closed_without_silent_fallback(monkeypatch):
    """Verify that in production mode, initialization does not swallow StorageConfigurationError."""
    import app.services.storage as st_mod
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("GLUCOTWIN_STORAGE_PROVIDER", "local")
    monkeypatch.delenv("GLUCOTWIN_UPLOAD_DIR", raising=False)

    with pytest.raises(StorageConfigurationError):
        st_mod.get_storage_provider()
