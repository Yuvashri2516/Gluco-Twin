"""
scripts/manage_doctor_approval.py - Secure CLI Workflow for Doctor Account Approvals
=====================================================================================

Provides direct server/administrator command-line management for doctor account approval requests.
Ensures approvals require explicit server access without public bypass endpoints.

Usage:
  # List all doctor account requests and current approval status:
  python backend/scripts/manage_doctor_approval.py list

  # Approve a pending doctor account:
  python backend/scripts/manage_doctor_approval.py approve <username_or_id>

  # Reject a pending doctor account:
  python backend/scripts/manage_doctor_approval.py reject <username_or_id>
"""

import sys
import os
import argparse

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User


def list_doctor_requests():
    db = SessionLocal()
    try:
        doctors = db.query(User).filter(User.role == "clinician").order_by(User.id.asc()).all()
        if not doctors:
            print("No clinician or doctor accounts found in database.")
            return

        print("\n" + "=" * 90)
        print(f"{'ID':<5} {'Username':<18} {'Full Name':<22} {'Approval Status':<18} {'License #':<16} {'Active':<8}")
        print("=" * 90)
        for doc in doctors:
            approval = getattr(doc, "approval_status", "approved")
            name = doc.full_name or "N/A"
            lic = doc.medical_license_number or "N/A"
            print(f"{doc.id:<5} {doc.username:<18} {name:<22} {approval:<18} {lic:<16} {str(doc.is_active):<8}")
        print("=" * 90 + "\n")
    finally:
        db.close()


def set_doctor_approval(identifier: str, new_status: str):
    db = SessionLocal()
    try:
        query = db.query(User).filter(User.role == "clinician")
        if identifier.isdigit():
            user = query.filter(User.id == int(identifier)).first()
        else:
            user = query.filter(User.username == identifier.strip()).first()

        if not user:
            print(f"[ERROR] Clinician account matching identifier '{identifier}' was not found.")
            sys.exit(1)

        prev_status = getattr(user, "approval_status", "approved")
        user.approval_status = new_status
        db.commit()
        db.refresh(user)

        print(f"[SUCCESS] Clinician '{user.username}' (ID #{user.id}) status transitioned: '{prev_status}' -> '{new_status}'.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="GlucoTwin Clinician Account Approval Management Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: list
    subparsers.add_parser("list", help="List all doctor account requests and approval statuses")

    # Subcommand: approve
    approve_parser = subparsers.add_parser("approve", help="Approve a pending doctor account")
    approve_parser.add_argument("identifier", help="Doctor username or user ID")

    # Subcommand: reject
    reject_parser = subparsers.add_parser("reject", help="Reject a pending doctor account")
    reject_parser.add_argument("identifier", help="Doctor username or user ID")

    args = parser.parse_args()

    if args.command == "list":
        list_doctor_requests()
    elif args.command == "approve":
        set_doctor_approval(args.identifier, "approved")
    elif args.command == "reject":
        set_doctor_approval(args.identifier, "rejected")


if __name__ == "__main__":
    main()
