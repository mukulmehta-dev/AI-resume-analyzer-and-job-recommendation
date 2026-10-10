import os
import sys
import subprocess
import shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(REPO_ROOT)

env_moved = False
if os.path.exists(".env"):
    shutil.move(".env", ".env.ci_bak")
    env_moved = True

backend_env_moved = False
if os.path.exists("backend/.env"):
    shutil.move("backend/.env", "backend/.env.ci_bak")
    backend_env_moved = True

try:
    print("=== TEST 1: RUNNING WITH CURRENT WORKFLOW VARS ONLY (NO JWT_SECRET) ===")
    workflow_env = {
        "DATABASE_URL": "postgresql+psycopg2://postgres:postgres@localhost:5432/resume_analyzer",
        "TEST_DATABASE_URL": "postgresql+psycopg2://postgres:postgres@localhost:5432/resume_analyzer_test",
        "PYTHONPATH": ".",
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    }
    r1 = subprocess.run(
        ["backend\\.venv\\Scripts\\alembic.exe", "upgrade", "head"],
        env=workflow_env,
        capture_output=True,
        text=True,
    )
    print("Alembic Returncode:", r1.returncode)
    print("Alembic Stderr:", r1.stderr[:300])

    r2 = subprocess.run(
        ["backend\\.venv\\Scripts\\pytest.exe", "-v", "-rs", "backend/tests/test_auth.py"],
        env=workflow_env,
        capture_output=True,
        text=True,
    )
    print("Pytest Returncode:", r2.returncode)
    print("Pytest Stderr/Stdout:", (r2.stderr + r2.stdout)[:400])

    print("\n=== TEST 2: RUNNING WITH MISSING CI VARS ADDED (JWT_SECRET, ENV=test, etc.) ===")
    complete_ci_env = {
        "DATABASE_URL": "postgresql+psycopg2://postgres:postgres@localhost:5432/resume_analyzer",
        "TEST_DATABASE_URL": "postgresql+psycopg2://postgres:postgres@localhost:5432/resume_analyzer_test",
        "JWT_SECRET": "ci_test_super_secret_jwt_key_resume_analyzer_2026",
        "ENV": "test",
        "ADMIN_PASSWORD": "adminpassword123",
        "UPLOAD_DIR": "data/uploads",
        "PYTHONPATH": ".",
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    }
    r3 = subprocess.run(
        ["backend\\.venv\\Scripts\\alembic.exe", "upgrade", "head"],
        env=complete_ci_env,
        capture_output=True,
        text=True,
    )
    print("Alembic Upgrade Returncode:", r3.returncode)

    r4 = subprocess.run(
        ["backend\\.venv\\Scripts\\alembic.exe", "downgrade", "base"],
        env=complete_ci_env,
        capture_output=True,
        text=True,
    )
    print("Alembic Downgrade Returncode:", r4.returncode)

    r5 = subprocess.run(
        ["backend\\.venv\\Scripts\\alembic.exe", "upgrade", "head"],
        env=complete_ci_env,
        capture_output=True,
        text=True,
    )
    print("Alembic Upgrade Returncode:", r5.returncode)

    r6 = subprocess.run(
        ["backend\\.venv\\Scripts\\pytest.exe", "-v", "-rs"],
        env=complete_ci_env,
        capture_output=True,
        text=True,
    )
    print("Pytest Returncode:", r6.returncode)
    summary_line = [l for l in r6.stdout.splitlines() if "passed" in l or "failed" in l]
    print("Pytest Summary:", summary_line[-1] if summary_line else "No summary")

finally:
    if env_moved and os.path.exists(".env.ci_bak"):
        shutil.move(".env.ci_bak", ".env")
    if backend_env_moved and os.path.exists("backend/.env.ci_bak"):
        shutil.move("backend/.env.ci_bak", "backend/.env")
