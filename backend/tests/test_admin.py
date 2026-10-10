import uuid
import pytest
from backend.app.models.user import User, UserRole
from backend.app.models.resume import Resume
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.core.security import hash_password


def _create_user(db_session, email, role=UserRole.user, is_active=True):
    user = User(
        name="Test User",
        email=email,
        password_hash=hash_password("password123"),
        role=role,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client, email, password="password123"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200


def test_admin_endpoints_require_admin_role_403_for_normal_user(client, db_session):
    user = _create_user(db_session, "normal@example.com", role=UserRole.user)
    _login(client, "normal@example.com")

    res_stats = client.get("/api/admin/stats")
    assert res_stats.status_code == 403

    res_users = client.get("/api/admin/users")
    assert res_users.status_code == 403

    res_patch = client.patch(f"/api/admin/users/{user.id}", json={"is_active": False})
    assert res_patch.status_code == 403


def test_admin_self_demotion_and_deactivation_blocked(client, db_session):
    admin = _create_user(db_session, "admin1@example.com", role=UserRole.admin)
    _login(client, "admin1@example.com")

    res_demote = client.patch(f"/api/admin/users/{admin.id}", json={"role": "user"})
    assert res_demote.status_code == 400
    assert "cannot deactivate or demote their own account" in res_demote.json()["detail"].lower()

    res_deactivate = client.patch(f"/api/admin/users/{admin.id}", json={"is_active": False})
    assert res_deactivate.status_code == 400
    assert "cannot deactivate or demote their own account" in res_deactivate.json()["detail"].lower()


def test_last_admin_protection(client, db_session):
    admin1 = _create_user(db_session, "admin_one@example.com", role=UserRole.admin)
    admin2 = _create_user(db_session, "admin_two@example.com", role=UserRole.admin)
    _login(client, "admin_one@example.com")

    res_demote_two = client.patch(f"/api/admin/users/{admin2.id}", json={"role": "user"})
    assert res_demote_two.status_code == 200

    admin3 = _create_user(db_session, "admin_three@example.com", role=UserRole.admin)
    _login(client, "admin_three@example.com")

    res_deactivate_one = client.patch(f"/api/admin/users/{admin1.id}", json={"is_active": False})
    assert res_deactivate_one.status_code == 200

    other_user = _create_user(db_session, "actor@example.com", role=UserRole.admin)
    _login(client, "actor@example.com")

    res_last = client.patch(f"/api/admin/users/{admin3.id}", json={"role": "user"})
    assert res_last.status_code == 200

    res_fail = client.patch(f"/api/admin/users/{other_user.id}", json={"role": "user"})
    assert res_fail.status_code == 400


def test_admin_stats_counts_correct(client, db_session):
    admin = _create_user(db_session, "stats_admin@example.com", role=UserRole.admin)
    user = _create_user(db_session, "user1@example.com", role=UserRole.user)
    _login(client, "stats_admin@example.com")

    resume = Resume(
        user_id=user.id,
        filename="test.pdf",
        stored_path="/tmp/test.pdf",
        mime="application/pdf",
        size=500,
        extracted_text="Resume text content",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    analysis_done = Analysis(
        user_id=user.id,
        resume_id=resume.id,
        resume_score=85,
        status=AnalysisStatus.done,
        detected_skills=["Python"],
        matching_skills=[],
        missing_skills=[],
        sections={},
        strengths=[],
        weaknesses=[],
        recommendations=[],
    )
    analysis_failed = Analysis(
        user_id=user.id,
        resume_id=resume.id,
        resume_score=0,
        status=AnalysisStatus.failed,
        error="Extraction crashed",
        detected_skills=[],
        matching_skills=[],
        missing_skills=[],
        sections={},
        strengths=[],
        weaknesses=[],
        recommendations=[],
    )
    db_session.add(analysis_done)
    db_session.add(analysis_failed)
    db_session.commit()

    res = client.get("/api/admin/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["users"] >= 2
    assert data["resumes"] >= 1
    assert data["analyses"] >= 2
    assert data["failed_analyses"] >= 1
    assert len(data["analyses_last_7_days"]) == 7
    assert len(data["recent_failures"]) >= 1
    assert data["recent_failures"][0]["error"] == "Extraction crashed"


def test_admin_users_pagination_and_search(client, db_session):
    admin = _create_user(db_session, "search_admin@example.com", role=UserRole.admin)
    u1 = _create_user(db_session, "alice@targetdomain.com", role=UserRole.user)
    u2 = _create_user(db_session, "bob@otherdomain.com", role=UserRole.user)
    _login(client, "search_admin@example.com")

    res_all = client.get("/api/admin/users?page=1&page_size=2")
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["total"] >= 3
    assert len(data_all["items"]) == 2

    res_search = client.get("/api/admin/users?search=targetdomain")
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert data_search["total"] == 1
    assert data_search["items"][0]["email"] == "alice@targetdomain.com"
