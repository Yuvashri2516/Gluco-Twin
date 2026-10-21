"""
auth.py - Authentication, Password Security, JWT Tokens, and Authorization
===========================================================================

Provides security functions and dependencies for:
  - Cryptographic password hashing & verification via bcrypt.
  - JWT token generation & payload verification via PyJWT.
  - Strict server-side role-based access control (RBAC):
      * 'clinician': Authorized across all cohort patients and clinical actions.
      * 'patient': Strictly isolated to their own records and documents.
  - Non-trusting validation of patient IDs and document IDs against the caller's identity.
"""

import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Patient, MedicalDocument

# ---------------------------------------------------------------------------
# Configuration from environment variables
# ---------------------------------------------------------------------------
DEFAULT_DEV_SECRET = "glucotwin-development-insecure-secret-key-change-in-production-2026"


class AuthConfigurationError(RuntimeError):
    """Raised when authentication security configuration is invalid or missing."""
    pass


def resolve_jwt_secret() -> str:
    """
    Resolves and validates the JWT signing secret with production safety enforcement.
    In production mode:
      - Requires GLUCOTWIN_JWT_SECRET to be explicitly set.
      - Strictly forbids the default development secret.
      - Requires minimum 32 characters.
    """
    env = os.environ.get("ENVIRONMENT", "development").strip().lower()
    secret = os.environ.get("GLUCOTWIN_JWT_SECRET")

    if env in ("production", "prod"):
        if not secret or not secret.strip():
            raise AuthConfigurationError(
                "CRITICAL SECURITY CONFIGURATION ERROR: Running in production mode (ENVIRONMENT=production), "
                "but GLUCOTWIN_JWT_SECRET is not set. A cryptographically strong secret (at least 32 characters) "
                "must be configured."
            )
        clean = secret.strip()
        if clean == DEFAULT_DEV_SECRET:
            raise AuthConfigurationError(
                "CRITICAL SECURITY CONFIGURATION ERROR: The known development JWT secret cannot be used in production. "
                "Please configure a unique, private GLUCOTWIN_JWT_SECRET."
            )
        if len(clean) < 32:
            raise AuthConfigurationError(
                f"CRITICAL SECURITY CONFIGURATION ERROR: Production GLUCOTWIN_JWT_SECRET is too short "
                f"(length {len(clean)} < 32 characters minimum required)."
            )
        return clean

    return secret.strip() if secret and secret.strip() else DEFAULT_DEV_SECRET


def get_jwt_secret() -> str:
    """Return the active JWT signing key."""
    return resolve_jwt_secret()


# Validate at import if in production
env_init = os.environ.get("ENVIRONMENT", "development").strip().lower()
if env_init in ("production", "prod"):
    JWT_SECRET_KEY = resolve_jwt_secret()
else:
    JWT_SECRET_KEY = os.environ.get("GLUCOTWIN_JWT_SECRET", DEFAULT_DEV_SECRET)

JWT_ALGORITHM = os.environ.get("GLUCOTWIN_JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("GLUCOTWIN_ACCESS_TOKEN_EXPIRE_MINUTES", "180"))

# OAuth2 bearer token scheme (points to login endpoint for OpenAPI docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ---------------------------------------------------------------------------
# Password Security (Bcrypt)
# ---------------------------------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generates a secure bcrypt salt and hash for a password."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# ---------------------------------------------------------------------------
# JWT Token Management
# ---------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Encodes a signed JWT token with expiration timestamp and user claims."""
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    expire = now_utc + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now_utc.timestamp()),
    })
    return jwt.encode(to_encode, get_jwt_secret(), algorithm=JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Authentication Dependencies
# ---------------------------------------------------------------------------
def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validates the Bearer token in the request and returns the authenticated User.
    Raises HTTP 401 Unauthorized if the token is missing, invalid, expired,
    or belongs to an inactive user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials. Bearer token required.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_approval = getattr(user, "approval_status", None)
    if user_approval is not None and user_approval != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is pending approval. Please contact a clinical administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ---------------------------------------------------------------------------
# Authorization Checks (Server-Side Enforced)
# ---------------------------------------------------------------------------
def require_clinician(current_user: User = Depends(get_current_user)) -> User:
    """
    Enforces that the current authenticated user has an explicit, server-validated
    'clinician' role and approved status. Does not trust any role supplied by frontend headers.
    """
    if current_user.role != "clinician":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access forbidden: User '{current_user.username}' does not hold required "
                f"clinician privileges (current role: '{current_user.role}')."
            ),
        )
    clinician_approval = getattr(current_user, "approval_status", None)
    if clinician_approval is not None and clinician_approval != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Clinician account is pending approval.",
        )
    return current_user


def check_patient_authorization(
    patient_id: int,
    current_user: User,
    db: Optional[Session] = None,
) -> None:
    """
    Ensures that a user cannot access another patient's records by guessing
    or altering patient IDs.
    - Clinicians must be approved. If doctor-patient assignments exist in the DB,
      clinicians can only access patients assigned to them.
    - Patients are strictly authorized ONLY for their bound patient_id.
    """
    if current_user.role == "clinician":
        clinician_approval = getattr(current_user, "approval_status", None)
        if clinician_approval is not None and clinician_approval != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clinician account is pending approval.",
            )
        if db is not None:
            try:
                from app.models import DoctorPatientAssignment
                has_assignments = db.query(DoctorPatientAssignment).filter(
                    DoctorPatientAssignment.doctor_id == current_user.id
                ).first()
                if has_assignments:
                    is_assigned = db.query(DoctorPatientAssignment).filter(
                        DoctorPatientAssignment.doctor_id == current_user.id,
                        DoctorPatientAssignment.patient_id == patient_id,
                    ).first()
                    if not is_assigned:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=(
                                f"Access forbidden: Clinician '{current_user.username}' is not authorized "
                                f"to access patient #{patient_id} outside their assigned clinical scope."
                            ),
                        )
            except HTTPException:
                raise
            except Exception:
                pass
        return

    if current_user.role == "patient" and current_user.patient_id == patient_id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            f"Access forbidden: User '{current_user.username}' is not authorized to "
            f"view or modify records for patient #{patient_id}."
        ),
    )


def check_document_authorization(
    document: MedicalDocument,
    current_user: User,
    db: Optional[Session] = None,
) -> None:
    """
    Ensures that a user cannot access or download another patient's medical document
    by guessing or altering document IDs.
    - Clinicians are authorized across cohort documents / assigned scope.
    - Patients are strictly authorized ONLY if document.patient_id matches their patient_id.
    """
    if current_user.role == "clinician":
        clinician_approval = getattr(current_user, "approval_status", None)
        if clinician_approval is not None and clinician_approval != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clinician account is pending approval.",
            )
        if db is not None:
            check_patient_authorization(document.patient_id, current_user, db)
        return

    if current_user.role == "patient" and current_user.patient_id == document.patient_id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            f"Access forbidden: User '{current_user.username}' is not authorized to "
            f"access or download document #{document.id} (associated with patient #{document.patient_id})."
        ),
    )
