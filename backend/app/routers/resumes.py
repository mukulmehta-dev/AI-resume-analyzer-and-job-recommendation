import uuid
import re
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.resume import Resume
from backend.app.models.analysis import Analysis
from backend.app.schemas.resume import ResumeResponse, ResumeDetailResponse
from backend.app.core.deps import get_current_user
from backend.app.core.config import settings
from backend.app.services.extractor import validate_file_content, extract_resume_text
from backend.app.services.storage import storage_service

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeDetailResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_resume_count = db.query(Resume).filter(Resume.user_id == current_user.id).count()
    if user_resume_count >= 50:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resume storage limit of 50 resumes reached. Please delete an older resume before uploading a new one."
        )

    original_filename = file.filename or "resume.pdf"
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    chunks = []
    total_bytes = 0

    while True:
        chunk = await file.read(1024 * 64)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_MB}MB"
            )
        chunks.append(chunk)

    content = b"".join(chunks)

    mime_type = validate_file_content(content, original_filename)
    extracted_text = extract_resume_text(content, original_filename)
    stored_path, random_filename = storage_service.save_file(content, original_filename)

    resume = Resume(
        user_id=current_user.id,
        filename=original_filename,
        stored_path=stored_path,
        mime=mime_type,
        size=len(content),
        extracted_text=extracted_text
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return ResumeDetailResponse(
        id=resume.id,
        user_id=resume.user_id,
        filename=resume.filename,
        mime=resume.mime,
        size=resume.size,
        created_at=resume.created_at,
        latest_score=None,
        analyses_count=0,
        extracted_text=resume.extracted_text
    )


@router.get("", response_model=List[ResumeResponse])
def get_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(desc(Resume.created_at))
        .all()
    )

    results = []
    for r in resumes:
        analyses = (
            db.query(Analysis)
            .filter(Analysis.resume_id == r.id, Analysis.user_id == current_user.id)
            .order_by(desc(Analysis.created_at))
            .all()
        )
        latest_score = analyses[0].resume_score if analyses else None
        results.append(
            ResumeResponse(
                id=r.id,
                user_id=r.user_id,
                filename=r.filename,
                mime=r.mime,
                size=r.size,
                created_at=r.created_at,
                latest_score=latest_score,
                analyses_count=len(analyses)
            )
        )
    return results


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
def get_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    analyses = (
        db.query(Analysis)
        .filter(Analysis.resume_id == resume.id, Analysis.user_id == current_user.id)
        .order_by(desc(Analysis.created_at))
        .all()
    )
    latest_score = analyses[0].resume_score if analyses else None

    return ResumeDetailResponse(
        id=resume.id,
        user_id=resume.user_id,
        filename=resume.filename,
        mime=resume.mime,
        size=resume.size,
        created_at=resume.created_at,
        latest_score=latest_score,
        analyses_count=len(analyses),
        extracted_text=resume.extracted_text
    )


@router.get("/{resume_id}/file")
def get_resume_file(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    try:
        content = storage_service.get_file(resume.stored_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical resume file could not be found"
        )

    sanitized_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', resume.filename)

    headers = {
        "Content-Disposition": f'inline; filename="{sanitized_filename}"',
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "sandbox",
    }

    return Response(
        content=content,
        media_type=resume.mime,
        headers=headers
    )


@router.delete("/{resume_id}")
def delete_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    storage_service.delete_file(resume.stored_path)
    db.query(Analysis).filter(Analysis.resume_id == resume.id).delete()
    db.delete(resume)
    db.commit()

    return {"message": "Resume deleted successfully"}
