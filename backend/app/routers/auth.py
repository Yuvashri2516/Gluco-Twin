"""
routers/auth.py - Authentication Endpoints (Login, Registration, Session Context)
==================================================================================

Provides endpoints for:
  POST  /api/auth/login     -> Authenticate credentials and receive Bearer JWT token
  POST  /api/auth/register  -> Register a new user account (with server-side validation)
  GET   /api/auth/me        -> Retrieve profile and permissions of authenticated user
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Patient
from app.schemas import UserCreate, UserLogin, UserRead, Token
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    require_clinician,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate user credentials (username and password) and issue a signed JWT.
    Rejects invalid credentials with HTTP 401 Unauthorized.
    """
    clean_username = payload.username.strip()
    user = db.query(User).filter(User.username == clean_username).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This user account has been deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
            "patient_id": user.patient_id,
        },
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=token,
        token_type="bearer",
        user=user,
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    current_user: User = Depends(require_clinician),
    db: Session = Depends(get_db),
):
    """
    Provision a new user account.
    - Public self-registration is disabled for safety.
    - Requires authenticated clinician privileges.
    - Prevents unauthorized creation of clinician accounts.
    - Prevents arbitrary patient-account hijacking and duplicate patient associations.
    """
    clean_username = payload.username.strip()
    if len(clean_username) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be at least 3 characters long.",
        )

    existing = db.query(User).filter(User.username == clean_username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{clean_username}' is already registered.",
        )

    role_clean = payload.role.strip().lower()
    if role_clean not in ["clinician", "patient"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role must be either 'clinician' or 'patient'.",
        )

    assigned_patient_id = None
    if role_clean == "patient" and payload.patient_id is not None:
        patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cannot associate account with non-existent patient ID #{payload.patient_id}.",
            )

        # Prevent duplicate patient-account associations / account hijacking
        existing_patient_user = db.query(User).filter(User.patient_id == payload.patient_id).first()
        if existing_patient_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Patient ID #{payload.patient_id} is already linked to another user account.",
            )
        assigned_patient_id = payload.patient_id

    hashed_pw = get_password_hash(payload.password)
    user = User(
        username=clean_username,
        email=payload.email.strip() if payload.email else None,
        hashed_password=hashed_pw,
        role=role_clean,
        patient_id=assigned_patient_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Return the profile, role, and bound patient_id of the authenticated caller."""
    return current_user
