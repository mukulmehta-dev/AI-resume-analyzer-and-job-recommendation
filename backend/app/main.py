from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.db.session import engine, Base, SessionLocal
from backend.app.db.seed import seed_admin
from backend.app.core.logging import setup_logging
from backend.app.routers import auth, resumes, analyses, admin
from backend.app.models.analysis import Analysis, AnalysisStatus
import backend.app.models


def _mark_stale_pending_failed(db) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    stale = (
        db.query(Analysis)
        .filter(
            Analysis.status == AnalysisStatus.pending,
            Analysis.created_at < cutoff,
        )
        .all()
    )
    for a in stale:
        a.status = AnalysisStatus.failed
        a.error = "Analysis timed out before completing."
    if stale:
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_admin(db)
        _mark_stale_pending_failed(db)
    yield



app = FastAPI(
    title="AI Resume Analyzer API",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    settings.CORS_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(resumes.router, prefix="/api")
app.include_router(analyses.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
