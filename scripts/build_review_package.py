import os
import sys
import zipfile
import shutil

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "backend/.venv",
    "node_modules",
    "uploads",
    "data/uploads",
    "__pycache__",
    ".pytest_cache",
    ".vite",
    ".react-router",
    ".agents",
    "frontend/build",
    "build",
    "%SystemDrive%",
}

EXCLUDE_EXTS = {
    ".exe",
    ".db",
    ".pyc",
    ".pyo",
    ".zip",
}

EXCLUDE_FILES = {
    ".env",
}


def should_exclude(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/").strip("/")
    parts = normalized.split("/")
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
        if "%SystemDrive%" in part:
            return True
        if part == ".agents" or part.startswith(".agents"):
            return True
        if part == "build" and "frontend" in parts:
            return True

    base = os.path.basename(normalized)
    if base in EXCLUDE_FILES:
        return True
    name_lower = base.lower()
    for ext in EXCLUDE_EXTS:
        if name_lower.endswith(ext):
            return True

    return False


def create_zip(source_dir: str, output_zip_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_zip_path)), exist_ok=True)
    if os.path.exists(output_zip_path):
        os.remove(output_zip_path)

    total_files = 0
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [
                d for d in dirs
                if d not in EXCLUDE_DIRS and "%SystemDrive%" not in d and d != ".agents"
            ]
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                if should_exclude(rel_path):
                    continue
                zf.write(full_path, rel_path)
                total_files += 1

    zip_size = os.path.getsize(output_zip_path)
    print(f"Total files packaged: {total_files}")
    print(f"Created {output_zip_path} with {total_files} files ({zip_size} bytes)")


if __name__ == "__main__":
    out_path = os.path.abspath("review-package/AI-Resume-Analyzer-Review.zip")
    create_zip(os.path.abspath("."), out_path)
    alt_out = r"C:\dev\AI-resume-analyzer\review-package\AI-Resume-Analyzer-Review.zip"
    if os.path.abspath(out_path) != os.path.abspath(alt_out):
        os.makedirs(os.path.dirname(alt_out), exist_ok=True)
        shutil.copyfile(out_path, alt_out)
        print(f"Copied package to {alt_out}")
