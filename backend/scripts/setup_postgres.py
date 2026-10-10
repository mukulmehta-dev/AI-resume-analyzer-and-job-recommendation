import os
import sys
import shutil
import zipfile
import urllib.request
import subprocess
import time

PG_URL = "https://sbp.enterprisedb.com/getfile.jsp?fileid=1260623"
ZIP_PATH = r"C:\dev\postgresql-16-binaries.zip"
TARGET_DIR = r"C:\dev\pgsql"
DATA_DIR = os.path.join(TARGET_DIR, "data")
LOG_FILE = os.path.join(TARGET_DIR, "logfile.log")

def download_archive(url: str, dest: str):
    if os.path.exists(dest) and os.path.getsize(dest) > 100000000:
        print(f"Archive already downloaded: {dest}")
        return
    print(f"Downloading PostgreSQL archive to {dest}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as out_file:
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 2 * 1024 * 1024
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = (downloaded / total) * 100
                print(f"Progress: {downloaded / (1024*1024):.1f}MB / {total / (1024*1024):.1f}MB ({pct:.1f}%)", end="\r")
    print(f"\nDownload finished: {dest}")

def extract_archive(zip_path: str, extract_root: str):
    initdb_exe = os.path.join(TARGET_DIR, "bin", "initdb.exe")
    if os.path.exists(initdb_exe):
        print("PostgreSQL binaries already extracted.")
        return
    print(f"Extracting {zip_path} to {extract_root}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_root)
    print("Extraction finished.")

def init_db():
    initdb_exe = os.path.join(TARGET_DIR, "bin", "initdb.exe")
    if os.path.exists(os.path.join(DATA_DIR, "PG_VERSION")):
        print(f"Data directory already initialized at {DATA_DIR}")
        return
    print(f"Initializing database cluster in {DATA_DIR}...")
    os.makedirs(DATA_DIR, exist_ok=True)
    cmd = [initdb_exe, "-D", DATA_DIR, "-U", "postgres", "-A", "trust", "-E", "UTF8"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        raise RuntimeError(f"initdb failed with exit code {res.returncode}")

def start_server():
    pg_ctl_exe = os.path.join(TARGET_DIR, "bin", "pg_ctl.exe")
    pg_isready_exe = os.path.join(TARGET_DIR, "bin", "pg_isready.exe")
    ready_chk = subprocess.run([pg_isready_exe, "-h", "localhost", "-p", "5432", "-U", "postgres"], capture_output=True, text=True)
    if ready_chk.returncode == 0:
        print("PostgreSQL is already running on localhost:5432")
        return
    print("Starting PostgreSQL server...")
    start_cmd = [pg_ctl_exe, "-D", DATA_DIR, "-l", LOG_FILE, "-o", "-p 5432", "start"]
    res = subprocess.run(start_cmd, capture_output=True, text=True)
    print(res.stdout)
    for _ in range(20):
        time.sleep(1)
        chk = subprocess.run([pg_isready_exe, "-h", "localhost", "-p", "5432", "-U", "postgres"], capture_output=True, text=True)
        if chk.returncode == 0:
            print("PostgreSQL is running and accepting connections on localhost:5432")
            return
    raise RuntimeError("PostgreSQL did not start in time.")

def create_dbs():
    createdb_exe = os.path.join(TARGET_DIR, "bin", "createdb.exe")
    for db in ["resume_analyzer", "resume_analyzer_test"]:
        cmd = [createdb_exe, "-h", "localhost", "-p", "5432", "-U", "postgres", db]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Created database {db}")
        elif "already exists" in res.stderr:
            print(f"Database {db} already exists")
        else:
            print(f"createdb {db}: {res.stderr.strip()}")

def main():
    download_archive(PG_URL, ZIP_PATH)
    extract_archive(ZIP_PATH, r"C:\dev")
    init_db()
    start_server()
    create_dbs()
    print("Setup completed successfully.")

if __name__ == "__main__":
    main()
