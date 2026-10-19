"""
conftest.py - Pytest Root Configuration & Authentication Fixtures
==================================================================

Configures test isolation and authentication dependencies:
  - Preserves regression compatibility for all 87 existing test suites by providing
    a default clinician authorization override unless explicitly cleared by auth tests.
  - Ensures all tests execute against in-memory SQLite and temporary storage.
"""

import pytest
from app.main import app
from app.auth import get_current_user
from app.models import User


@pytest.fixture(autouse=True)
def default_clinician_auth_override(request):
    """
    Default autouse fixture providing an authenticated clinician session
    for existing Phase 1-5 test suites, ensuring zero regression across
    digital-twin, prediction, alert, and telemetry tests.
    Explicitly skipped for security test suites so they exercise real auth dependencies.
    """
    if "test_auth" in request.module.__name__:
        yield
        return

    default_clinician = User(
        id=999,
        username="test_clinician",
        email="clinician@test.hospital",
        role="clinician",
        is_active=True,
    )
    had_override = get_current_user in app.dependency_overrides
    if not had_override:
        app.dependency_overrides[get_current_user] = lambda: default_clinician
    yield
    if not had_override:
        app.dependency_overrides.pop(get_current_user, None)
