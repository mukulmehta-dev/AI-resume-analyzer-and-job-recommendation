import os
import sys
import zipfile
import shutil

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "uploads",
    "__pycache__",
    ".pytest_cache",
    ".vite",
    ".react-router",
}

EXCLUDE_FILES = {
    ".env",
    "resume_analyzer.db",
    "test_runner.db",
}


def should_exclude(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/").strip("/")
    parts = normalized.split("/")
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
        if part.endswith(".pyc") or part.endswith(".pyo"):
            return True
    base = os.path.basename(normalized)
    if base in EXCLUDE_FILES or base.endswith(".zip"):
        return True
    return False


def create_zip(source_dir: str, output_zip_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_zip_path)), exist_ok=True)
    if os.path.exists(output_zip_path):
        os.remove(output_zip_path)

    total_files = 0
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                if should_exclude(rel_path):
                    continue
                zf.write(full_path, rel_path)
                total_files += 1

    zip_size = os.path.getsize(output_zip_path)
    print(f"Created {output_zip_path} with {total_files} files ({zip_size} bytes)")


if __name__ == "__main__":
    out_path = os.path.abspath("review-package/AI-Resume-Analyzer-Review.zip")
    create_zip(os.path.abspath("."), out_path)
    alt_out = r"C:\dev\AI-resume-analyzer\review-package\AI-Resume-Analyzer-Review.zip"
    if os.path.abspath(out_path) != os.path.abspath(alt_out):
        os.makedirs(os.path.dirname(alt_out), exist_ok=True)
        shutil.copyfile(out_path, alt_out)
        print(f"Copied package to {alt_out}")
