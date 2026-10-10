import os
import sys
import time
import shutil
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.abspath("review-package/screenshots")
ALT_SCREENSHOT_DIR = r"C:\dev\AI-resume-analyzer\review-package\screenshots"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(ALT_SCREENSHOT_DIR, exist_ok=True)


def save_and_copy(page, filename: str):
    target_path = os.path.join(SCREENSHOT_DIR, filename)
    page.screenshot(path=target_path, full_page=True)
    alt_path = os.path.join(ALT_SCREENSHOT_DIR, filename)
    shutil.copyfile(target_path, alt_path)
    print(f"[PASS] Saved screenshot {filename} ({os.path.getsize(target_path)} bytes)")


def main():
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

        print("Capturing results without JD...")
        page.goto("http://localhost:5173/analysis/38c21713-2784-4e7b-823a-d0e53fb4a872")
        time.sleep(2)
        save_and_copy(page, "results_without_jd.png")

        print("Capturing results with JD...")
        page.goto("http://localhost:5173/analysis/a682f59a-9268-4349-915e-a8e076db3bb8")
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
