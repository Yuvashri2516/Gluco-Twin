"""
routers/auth.py - Authentication Endpoints (Login, Registration, Doctor Approval, RBAC)
========================================================================================

Provides endpoints for:
  POST  /api/auth/login                  -> Authenticate credentials and receive Bearer JWT token
  POST  /api/auth/register-patient       -> Public self-registration for new patients
  POST  /api/auth/register-doctor        -> Public registration request for doctors (pending approval)
  GET   /api/auth/doctor-requests        -> List pending doctor registration requests (clinician only)
  POST  /api/auth/doctor-requests/{id}/approve -> Approve pending doctor account (clinician only)
  POST  /api/auth/doctor-requests/{id}/reject  -> Reject pending doctor account (clinician only)
  POST  /api/auth/assign-patient         -> Assign a patient to a doctor's care scope (clinician only)
  GET   /api/auth/doctor-patients        -> List patient IDs assigned to active doctor
  POST  /api/auth/register               -> Provision user accounts (clinician only legacy endpoint)
  GET   /api/auth/me                     -> Retrieve profile and permissions of authenticated user
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Patient, DoctorPatientAssignment
from app.schemas import (
    UserCreate,
    UserLogin,
    UserRead,
    Token,
    PatientRegisterRequest,
    DoctorRegisterRequest,
    DoctorApprovalAction,
    DoctorAssignmentCreate,
    DoctorAssignmentRead,
)
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
    Enforces server-side checks for inactive accounts, pending clinician approvals,
    and optional portal affinity checks without leaking sensitive internal details.
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

    # Check clinician approval status
    user_approval = getattr(user, "approval_status", "approved")
    if user.role == "clinician" and user_approval == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor account is pending approval. An authorized clinician or administrator must approve your account before access is granted.",
        )
    if user.role == "clinician" and user_approval == "rejected":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor account request has been rejected. Please contact support.",
        )

    # Optional portal role affinity validation
    if payload.portal:
        portal_clean = payload.portal.strip().lower()
        if portal_clean == "patient" and user.role != "patient":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has clinician privileges. Please sign in via the Doctor Portal.",
            )
        if portal_clean in ["doctor", "clinician"] and user.role != "clinician":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is a patient account. Please sign in via the Patient Portal.",
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


@router.post("/register-patient", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_patient(
    payload: PatientRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Public self-registration for new patients.
    - Strictly assigns 'patient' role on the server.
    - Never trusts role or patient_id from client request.
    - Transactionally provisions Patient profile and User account together.
    - Hashes password securely via bcrypt.
    - Preserves existing patients and prevents duplicate usernames/emails.
    """
    clean_username = payload.username.strip()
    clean_email = payload.email.strip().lower()
    raw_name = payload.full_name or payload.name or ""
    clean_name = raw_name.strip()

    if len(clean_username) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be at least 3 characters long.",
        )

    if not re.match(r"^[a-zA-Z0-9_.-]+$", clean_username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username may only contain letters, numbers, underscores, periods, and hyphens.",
        )

    if len(clean_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Full name must be at least 2 characters long.",
        )

    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long.",
        )

    if payload.confirm_password is not None and payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password and confirm password do not match.",
        )

    # Check for existing username or email
    existing_user = db.query(User).filter(User.username == clean_username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username is already registered.",
        )

    existing_email = db.query(User).filter(User.email == clean_email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address is already registered.",
        )

    try:
        # 1. Create Patient profile
        new_patient = Patient(
            name=clean_name,
            age=payload.age if payload.age is not None else 35,
            gender=payload.gender.strip() if payload.gender else "Other",
            diabetes_type=payload.diabetes_type.strip() if payload.diabetes_type else "Type 2",
            years_since_diagnosis=0,
            historical_diagnoses="None",
            medical_history="",
            created_at=datetime.now(timezone.utc),
        )
        db.add(new_patient)
        db.flush()  # obtains new_patient.id

        # 2. Create User account bound to new_patient.id
        hashed_pw = get_password_hash(payload.password)
        new_user = User(
            username=clean_username,
            email=clean_email,
            full_name=clean_name,
            hashed_password=hashed_pw,
            role="patient",
            approval_status="approved",
            patient_id=new_patient.id,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception:
        db.rollback()
        raise


@router.post("/register-doctor", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_doctor(
    payload: DoctorRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Public registration request for new doctor / clinician accounts.
    - Strictly sets role='clinician' and approval_status='pending' on the server.
    - Does NOT grant immediate clinician privileges.
    - Pending doctors cannot access patient data or clinician endpoints.
    - Approval requires an existing authorized clinician.
    """
    clean_username = payload.username.strip()
    clean_email = payload.email.strip().lower()
    clean_name = payload.full_name.strip()

    if len(clean_username) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be at least 3 characters long.",
        )

    if not re.match(r"^[a-zA-Z0-9_.-]+$", clean_username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username may only contain letters, numbers, underscores, periods, and hyphens.",
        )

    if len(clean_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Full name must be at least 2 characters long.",
        )

    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long.",
        )

    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password and confirm password do not match.",
        )

    existing_user = db.query(User).filter(User.username == clean_username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username is already registered.",
        )

    existing_email = db.query(User).filter(User.email == clean_email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address is already registered.",
        )

    license_num = payload.medical_license_number.strip() if payload.medical_license_number else None
    hashed_pw = get_password_hash(payload.password)

    doctor_user = User(
        username=clean_username,
        email=clean_email,
        full_name=clean_name,
        medical_license_number=license_num,
        hashed_password=hashed_pw,
        role="clinician",
        approval_status="pending",
        patient_id=None,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(doctor_user)
    db.commit()
    db.refresh(doctor_user)
    return doctor_user


@router.get("/doctor-requests", response_model=List[UserRead])
def list_doctor_requests(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_clinician),
    db: Session = Depends(get_db),
):
    """
    List doctor account requests. Requires server-validated approved clinician role.
    """
    query = db.query(User).filter(User.role == "clinician")
    if status_filter:
        query = query.filter(User.approval_status == status_filter.strip().lower())
    return query.order_by(User.created_at.desc()).all()


@router.post("/doctor-requests/{user_id}/approve", response_model=UserRead)
def approve_doctor_request(
    user_id: int,
    current_user: User = Depends(require_clinician),
    db: Session = Depends(get_db),
):
    """
    Approve a pending doctor account.
    - Requires authenticated approved clinician.
    - Clinicians cannot approve their own account.
    """
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clinicians cannot approve their own account.",
        )

    target_user = db.query(User).filter(User.id == user_id, User.role == "clinician").first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor account with user ID #{user_id} not found.",
        )

    target_user.approval_status = "approved"
    db.commit()
    db.refresh(target_user)
    return target_user


@router.post("/doctor-requests/{user_id}/reject", response_model=UserRead)
def reject_doctor_request(
    user_id: int,
    current_user: User = Depends(require_clinician),
    db: Session = Depends(get_db),
):
    """
    Reject a pending doctor account.
    - Requires authenticated approved clinician.
    - Clinicians cannot reject their own account.
    """
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clinicians cannot reject their own account.",
        )

    target_user = db.query(User).filter(User.id == user_id, User.role == "clinician").first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor account with user ID #{user_id} not found.",
        )

    target_user.approval_status = "rejected"
    db.commit()
    db.refresh(target_user)
    return target_user


@router.post("/assign-patient", response_model=DoctorAssignmentRead, status_code=status.HTTP_201_CREATED)
def assign_doctor_patient(
    payload: DoctorAssignmentCreate,
    current_user: User = Depends(require_clinician),
    db: Session = Depends(get_db),
):
    """
    Assign a patient to a doctor's permitted care scope.
    Requires clinician privileges.
    """
    doctor = db.query(User).filter(User.id == payload.doctor_id, User.role == "clinician").first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with user ID #{payload.doctor_id} not found.",
        )

    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID #{payload.patient_id} not found.",
        )

    existing = (
        db.query(DoctorPatientAssignment)
        .filter(
            DoctorPatientAssignment.doctor_id == payload.doctor_id,
            DoctorPatientAssignment.patient_id == payload.patient_id,
        )
        .first()
    )
    if existing:
        return existing

    assignment = DoctorPatientAssignment(
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
        assigned_at=datetime.now(timezone.utc),
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/doctor-patients", response_model=List[int])
def list_doctor_assigned_patients(
    current_user: User = Depends(require_clinician),
    db: Session = Depends(get_db),
):
    """
    Return patient IDs assigned to the calling clinician.
    If no specific assignments exist, returns empty list (indicating broad cohort access in demo mode).
    """
    assignments = db.query(DoctorPatientAssignment).filter(
        DoctorPatientAssignment.doctor_id == current_user.id
    ).all()
    return [a.patient_id for a in assignments]


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    current_user: User = Depends(require_clinician),
    db: Session = Depends(get_db),
):
    """
    Provision a new user account (clinician-managed endpoint).
    - Requires authenticated clinician privileges.
    - Prevents duplicate patient associations.
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
        email=payload.email.strip().lower() if payload.email else None,
        full_name=payload.full_name.strip() if payload.full_name else None,
        medical_license_number=payload.medical_license_number.strip() if payload.medical_license_number else None,
        hashed_password=hashed_pw,
        role=role_clean,
        approval_status="approved",
        patient_id=assigned_patient_id,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Return the profile, role, approval status, and bound patient_id of the authenticated caller."""
    return current_user
