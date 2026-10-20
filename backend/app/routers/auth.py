"""
routers/auth.py - Authentication Endpoints
===========================================

Endpoints:
  POST /api/auth/login
      Authenticate user credentials and issue a JWT.

  POST /api/auth/register
      Create a user account through an authenticated clinician.

  POST /api/auth/register-patient
      Allow a new patient to create their own patient account.

  GET /api/auth/me
      Retrieve the authenticated user's profile.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User, Patient
from app.schemas import (
    UserCreate,
    UserLogin,
    UserRead,
    Token,
    PatientSignupRequest,
)
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    require_clinician,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# ============================================================
# LOGIN
# ============================================================

@router.post("/login", response_model=Token)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate using username and password.

    Returns:
        JWT access token and authenticated user details.

    Raises:
        401: Invalid credentials or deactivated account.
    """

    clean_username = payload.username.strip()

    user = (
        db.query(User)
        .filter(User.username == clean_username)
        .first()
    )

    if not user or not verify_password(
        payload.password,
        user.hashed_password,
    ):
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

    access_token_expires = timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

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


# ============================================================
# CLINICIAN-ONLY USER REGISTRATION
# ============================================================

@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserCreate,
    current_user: User = Depends(require_clinician),
    db: Session = Depends(get_db),
):
    """
    Provision a user account through an authenticated clinician.

    Public users cannot use this endpoint.

    Security:
        - Requires clinician privileges.
        - Allows only clinician or patient roles.
        - Prevents duplicate usernames.
        - Prevents linking an existing patient to multiple accounts.
    """

    clean_username = payload.username.strip()

    if len(clean_username) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be at least 3 characters long.",
        )

    existing_user = (
        db.query(User)
        .filter(User.username == clean_username)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{clean_username}' is already registered.",
        )

    role_clean = payload.role.strip().lower()

    if role_clean not in {"clinician", "patient"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role must be either 'clinician' or 'patient'.",
        )

    assigned_patient_id = None

    if role_clean == "patient" and payload.patient_id is not None:

        patient = (
            db.query(Patient)
            .filter(Patient.id == payload.patient_id)
            .first()
        )

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Cannot associate account with non-existent "
                    f"patient ID #{payload.patient_id}."
                ),
            )

        existing_patient_user = (
            db.query(User)
            .filter(User.patient_id == payload.patient_id)
            .first()
        )

        if existing_patient_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Patient ID #{payload.patient_id} is already "
                    "linked to another user account."
                ),
            )

        assigned_patient_id = payload.patient_id

    user = User(
        username=clean_username,
        email=payload.email.strip() if payload.email else None,
        hashed_password=get_password_hash(payload.password),
        role=role_clean,
        patient_id=assigned_patient_id,
        is_active=True,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The username or email is already registered.",
        )

    return user


# ============================================================
# PUBLIC PATIENT SELF-REGISTRATION
# ============================================================

@router.post(
    "/register-patient",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_patient_account(
    payload: PatientSignupRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new patient and create a linked user account.

    This endpoint is intended for the login page's
    'Create an account' option.

    Security:
        - Creates patient accounts only.
        - Does not accept a user-selected role.
        - Does not accept a user-selected patient_id.
        - Hashes the password before storing it.
        - Rejects duplicate usernames and email addresses.
        - Creates the patient and user in one transaction.
    """

    clean_username = payload.username.strip()
    clean_email = payload.email.strip().lower()
    clean_name = payload.name.strip()
    clean_gender = payload.gender.strip()
    clean_diabetes_type = payload.diabetes_type.strip()

    # --------------------------------------------------------
    # Validate required text fields
    # --------------------------------------------------------

    if len(clean_username) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be at least 3 characters long.",
        )

    if len(clean_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please enter a valid full name.",
        )

    if not clean_email or "@" not in clean_email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please enter a valid email address.",
        )

    # --------------------------------------------------------
    # Check duplicate username
    # --------------------------------------------------------

    existing_username = (
        db.query(User)
        .filter(User.username == clean_username)
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already registered.",
        )

    # --------------------------------------------------------
    # Check duplicate email, ignoring case
    # --------------------------------------------------------

    existing_email = (
        db.query(User)
        .filter(
            User.email.isnot(None),
            User.email.ilike(clean_email),
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered.",
        )

    # --------------------------------------------------------
    # Create patient and linked account atomically
    # --------------------------------------------------------

    try:
        patient = Patient(
            name=clean_name,
            age=payload.age,
            gender=clean_gender,
            diabetes_type=clean_diabetes_type,
            years_since_diagnosis=0,
        )

        db.add(patient)

        # Obtain the new patient ID without committing yet.
        db.flush()

        user = User(
            username=clean_username,
            email=clean_email,
            hashed_password=get_password_hash(payload.password),
            role="patient",
            patient_id=patient.id,
            is_active=True,
        )

        db.add(user)

        # Commit both records together.
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The username or email may already be registered. "
                "Please try different details."
            ),
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Registration could not be completed. "
                "Please try again."
            ),
        )

    return user


# ============================================================
# CURRENT USER PROFILE
# ============================================================

@router.get(
    "/me",
    response_model=UserRead,
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Return the authenticated user's profile,
    role, and associated patient ID.
    """

    return current_user