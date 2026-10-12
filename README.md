# AI Resume Analyzer and Job Recommendation System

Full-stack enterprise application for ATS-aligned resume analysis, deterministic scoring, semantic skill matching, and AI advisory feedback.

Requirement IDs follow the project SRS (FR-1 to FR-39, NFR-1 to NFR-16).

---

## ATS Compatibility & Scoring Logic

When a job description is provided, compatibility between the candidate and position is evaluated using deterministic heuristics combining weighted keyword overlap and TF-IDF cosine similarity:

```
compatibility = round_half_up(100*(0.75*overlap + 0.25*min(1, tfidf_cosine/0.2)))
```

- **`overlap`**: Weighted skill overlap ratio where required skills receive double weight compared to preferred skills: `(2 * required_overlap + 1 * preferred_overlap) / 3`.
- **`tfidf_cosine`**: Raw TF-IDF cosine similarity between resume text and job description.
- Clamped between `0` and `100`. Resumes with no job description return `None` for compatibility.

---

## 1. Prerequisites

- **Python**: 3.13+
- **Node.js**: 20+ and npm
- **Database**: PostgreSQL 16+ (or Docker)
- **Container Runtime**: Docker Desktop 24+ and Docker Compose v2+ (for containerized deployment)

---

## 2. Environment Variables

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Yes | `postgresql+psycopg2://postgres:postgres@localhost:5432/resume_analyzer` | Main PostgreSQL connection URI |
| `TEST_DATABASE_URL` | No | `sqlite:///./test_runner.db` | Test database URI; required for full PostgreSQL test runs |
| `JWT_SECRET` | Yes | None | Cryptographic secret for signing auth session tokens |
| `ENV` | No | `development` | Environment mode (`development` or `production`) |
| `ADMIN_EMAIL` | No | `admin@example.com` | Initial administrator email seeded on first startup |
| `ADMIN_PASSWORD` | No | `change_this_secure_admin_password` | Initial administrator password seeded on first startup |
| `TRUSTED_PROXY` | No | `false` | When `true`, honors `X-Forwarded-For` header behind reverse proxy |
| `UPLOAD_DIR` | No | `data/uploads` | Local disk directory for storing uploaded PDF and DOCX files |
| `MAX_UPLOAD_MB` | No | `5` | Maximum upload size threshold in megabytes |
| `GEMINI_API_KEY` | No | None | Google Gemini API key for optional LLM executive feedback |
| `GEMINI_MODEL` | No | `gemini-3.8-flash` | Primary Gemini model variant used for enrichment |
| `GEMINI_MODEL_FALLBACKS` | No | `gemini-3.5-flash,gemini-3.1-flash-lite,gemini-2.5-flash` | Comma-separated fallback models on 404/403/429 errors |
| `CORS_ORIGIN` | No | `http://localhost:5173` | Allowed origin for CORS headers |
| `USE_EMBEDDINGS` | No | `false` | Enable vector embeddings for semantic similarity |

---

## Gemini AI Integration & Model Fallback

### Obtaining an API Key
Generate an API key from [Google AI Studio](https://aistudio.google.com/apikey).
New keys start with the `AQ.` prefix (Google Authentication Key format), while legacy keys start with `AIza`. Both formats are supported.

### Model Discovery
To discover models supported by your key and SDK:

```powershell
python scripts/discover_models.py
```

Or programmatically:

```python
from google import genai
client = genai.Client(api_key="YOUR_KEY")
for model in client.models.list():
    if "generateContent" in getattr(model, "supported_actions", []):
        print(model.name)
```

### Multi-Model Fallback Resilience
When `GEMINI_API_KEY` is configured:
1. The backend attempts analysis with `GEMINI_MODEL` (30s timeout, up to 1 retry on transient error).
2. If the model returns 404 (retired model), 403 (unauthorized model), or 429 (quota exhausted), the pipeline automatically cascades to each model in `GEMINI_MODEL_FALLBACKS`.
3. The server logs the specific model that satisfied the request (`Analysis served by Gemini model: <name>`).
4. If all models fail, or if `GEMINI_API_KEY` is unset, the application falls back to rule-based analysis, returns status `done` with `ai_unavailable=true`, and displays the AI-unavailable banner.

---

## Run locally without Docker (Windows)

### Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Configure Environment

```powershell
Copy-Item ..\.env.example .\.env
```

### Apply Migrations and Seed

```powershell
$env:PYTHONPATH = ".."
alembic upgrade head
python -m backend.app.db.seed_demo
```

### Start Backend Server

```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Setup and Run

Open a new PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` with proxy requests routed to `http://localhost:8000/api`.

---

## 4. Container Deployment with Docker Compose

Build and launch all services (`db`, `api`, `web`, `proxy`):

```bash
docker compose up --build -d
```

- Web UI & Unified API: `http://localhost`
- Healthcheck Endpoint: `http://localhost/api/health`
- Database: Managed PostgreSQL 16 on port 5432 with persistent volume `postgres_data`
- Uploads: Persistent volume `uploads_data` mounted at `/app/data/uploads`

To inspect container logs:

```bash
docker compose logs -f
```

To stop and remove containers:

```bash
docker compose down
```

---

## 5. Cloud Deployment Guide

### Option A: Single VPS (Ubuntu / Debian)

1. Provision an Ubuntu 24.04 LTS instance with at least 2 GB RAM.
2. Install Docker and Docker Compose:
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose-plugin
   ```
3. Clone repository and configure `.env`:
   ```bash
   git clone <repo-url> /opt/resume-analyzer
   cd /opt/resume-analyzer
   cp .env.example .env
   ```
4. Set production secrets in `.env`:
   - Generate strong `JWT_SECRET`: `openssl rand -hex 32`
   - Set `ENV=production` (enforces Secure cookies)
   - Set `TRUSTED_PROXY=true`
5. Start services:
   ```bash
   docker compose up --build -d
   ```
6. Configure TLS certificates with Certbot:
   ```bash
   sudo apt-get install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

### Option B: Render or Railway (Managed PostgreSQL & Persistent Disk)

1. **Database**: Create a Managed PostgreSQL 16 database. Copy the connection string to `DATABASE_URL`.
2. **API Service**:
   - Create a Web Service from `backend/Dockerfile`.
   - Set environment variables (`DATABASE_URL`, `JWT_SECRET`, `ENV=production`, `TRUSTED_PROXY=true`).
   - Attach a Persistent Disk mounted at `/app/data/uploads`.
   - Build Command: `python -m spacy download en_core_web_sm`
   - Start Command: `alembic upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
3. **Frontend Service**:
   - Create a Web Service pointing to `frontend/Dockerfile` or static site deployment.
   - Configure reverse proxy routing `/api/*` to the Backend Service.

---

## 6. Troubleshooting

- **PostgreSQL Connection Refused**:
  Ensure PostgreSQL is running and accepting TCP/IP connections on port 5432. For Docker, ensure the `db` service healthcheck has passed before `api` boots.
- **spaCy Model Missing**:
  Run `python -m spacy download en_core_web_sm` inside your active virtual environment.
- **Cookie Authentication Fails on Localhost**:
  If `ENV=production`, session cookies require HTTPS (`Secure=true`). Keep `ENV=development` when running on plain `http://localhost`.
- **File Upload 422 Rejections**:
  The system enforces strict magic-byte signatures and rejects files exceeding 5 MB, PDFs exceeding 30 pages, or DOCX archives with suspicious zip-bomb compression ratios.
