import os
import sys
import time
import shutil
from playwright.sync_api import sync_playwright

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.app.db.session import SessionLocal
from backend.app.models.analysis import Analysis

SCREENSHOT_DIR = os.path.abspath("review-package/screenshots")
ALT_SCREENSHOT_DIR = r"C:\dev\AI-resume-analyzer\review-package\screenshots"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(ALT_SCREENSHOT_DIR, exist_ok=True)


def save_and_copy(page, filename: str):
    target_path = os.path.join(SCREENSHOT_DIR, filename)
    page.screenshot(path=target_path, full_page=True)
    alt_path = os.path.join(ALT_SCREENSHOT_DIR, filename)
    if os.path.abspath(target_path) != os.path.abspath(alt_path):
        shutil.copyfile(target_path, alt_path)
    print(f"[PASS] Saved screenshot {filename} ({os.path.getsize(target_path)} bytes)")


def main():
    db = SessionLocal()
    from backend.app.models.user import User
    demo_user = db.query(User).filter(User.email == 'demo@example.com').first()
    user_id_filter = demo_user.id if demo_user else None
    analysis_no_jd = db.query(Analysis).filter(Analysis.user_id == user_id_filter, Analysis.job_description.is_(None)).first()
    analysis_with_jd = db.query(Analysis).filter(Analysis.user_id == user_id_filter, Analysis.job_description.isnot(None), Analysis.resume_score > 0).first()
    no_jd_id = str(analysis_no_jd.id) if analysis_no_jd else ""
    with_jd_id = str(analysis_with_jd.id) if analysis_with_jd else ""
    db.close()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("Navigating to auth page...")
        page.goto("http://localhost:5173/auth")
        page.wait_for_selector('input[type="email"]')
        time.sleep(1)
        save_and_copy(page, "auth.png")

        print("Logging in as demo user...")
        page.fill('input[type="email"]', "demo@example.com")
        page.fill('input[type="password"]', "DemoPassword123!")
        page.click('button[type="submit"]')
        page.wait_for_url("http://localhost:5173/", timeout=10000)
        time.sleep(2)
        save_and_copy(page, "dashboard.png")

        print("Capturing upload page...")
        page.goto("http://localhost:5173/upload")
        time.sleep(2)
        save_and_copy(page, "upload.png")

        if no_jd_id:
            print(f"Capturing results without JD ({no_jd_id})...")
            page.goto(f"http://localhost:5173/analysis/{no_jd_id}")
            time.sleep(2)
            save_and_copy(page, "results_without_jd.png")

        if with_jd_id:
            print(f"Capturing results with JD ({with_jd_id})...")
            page.goto(f"http://localhost:5173/analysis/{with_jd_id}")
            time.sleep(2)
            save_and_copy(page, "results_with_jd.png")

        print("Capturing history page...")
        page.goto("http://localhost:5173/history")
        time.sleep(2)
        save_and_copy(page, "history.png")

        print("Capturing resumes page...")
        page.goto("http://localhost:5173/resumes")
        time.sleep(2)
        save_and_copy(page, "resumes.png")

        context.close()

        print("Logging in as admin user...")
        admin_context = browser.new_context(viewport={"width": 1440, "height": 900})
        admin_page = admin_context.new_page()
        admin_page.goto("http://localhost:5173/auth")
        admin_page.wait_for_selector('input[type="email"]')
        admin_page.fill('input[type="email"]', "admin@example.com")
        admin_page.fill('input[type="password"]', "adminpassword123")
        admin_page.click('button[type="submit"]')
        admin_page.wait_for_url("http://localhost:5173/", timeout=10000)
        time.sleep(1)

        print("Capturing admin dashboard...")
        admin_page.goto("http://localhost:5173/admin")
        time.sleep(2)
        save_and_copy(admin_page, "admin.png")

        admin_context.close()
        browser.close()

    print("\nALL 8 SCREENSHOTS CAPTURED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
