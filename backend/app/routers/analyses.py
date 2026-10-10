import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from backend.app.db.session import get_db, SessionLocal
from backend.app.core.deps import get_current_user
from backend.app.core.ratelimit import check_rate_limit
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.resume import Resume
from backend.app.schemas.analysis import (
    AnalysisCreateRequest,
    AnalysisResponse,
    AnalysisAcceptedResponse,
    AnalysisListResponse,
    SkillWithCategory,
)
from backend.app.models.user import User
from backend.app.services.pipeline import run_rule_based
from backend.app.services.gemini import enhance_analysis, GeminiUnavailable
from backend.app.services.skills import get_all_skills

router = APIRouter(prefix="/analyses", tags=["analyses"])

_SKILL_CATEGORY_MAP = {s["canonical"]: s["category"] for s in get_all_skills()}


def _enrich_response(analysis: Analysis) -> AnalysisResponse:
    detected = analysis.detected_skills or []
    with_cat = [
        SkillWithCategory(name=s, category=_SKILL_CATEGORY_MAP.get(s, "other"))
        for s in detected
    ]
    data = AnalysisResponse.model_validate(analysis)
    data.detected_skills_with_category = with_cat
    if analysis.resume:
        data.resume_filename = analysis.resume.filename
    return data


def _run_pipeline(
    analysis_id: uuid.UUID,
    resume_text: str,
    jd_text: Optional[str],
    session_factory=None,
) -> None:
    factory = session_factory or SessionLocal
    db: Session = factory()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return

        result = run_rule_based(resume_text, jd_text)

        analysis.resume_score = result.resume_score
        analysis.compatibility_score = result.compatibility_score
        analysis.detected_skills = result.detected_skills
        analysis.matching_skills = result.matching_skills
        analysis.missing_skills = result.missing_skills
        analysis.sections = result.sections
        analysis.strengths = result.strengths
        analysis.weaknesses = result.weaknesses
        analysis.recommendations = [r.model_dump() for r in result.recommendations]
        analysis.summary_feedback = result.summary_feedback
        analysis.ai_unavailable = False
        db.commit()

        try:
            resume_facts = {
                "word_count": result.word_count,
                "estimated_years_of_experience": result.estimated_years_of_experience,
                "action_verb_count": result.action_verb_count,
                "quantified_achievement_count": result.quantified_achievement_count,
                "degree_mentions": result.degree_mentions,
            }
            ai_result = enhance_analysis(
                resume_facts=resume_facts,
                jd_text=jd_text,
                detected_skills=result.detected_skills,
                matching_skills=result.matching_skills,
                missing_skills=result.missing_skills,
                resume_score=result.resume_score,
                sections=result.sections,
            )
            analysis.strengths = ai_result.get("strengths", analysis.strengths)
            analysis.weaknesses = ai_result.get("weaknesses", analysis.weaknesses)
            analysis.recommendations = ai_result.get("recommendations", analysis.recommendations)
            analysis.summary_feedback = ai_result.get("summary_feedback", "")
            analysis.ai_unavailable = False
        except GeminiUnavailable:
            analysis.ai_unavailable = True
        except Exception:
            analysis.ai_unavailable = True

        analysis.status = AnalysisStatus.done
        db.commit()

    except Exception:
        db.rollback()
        try:
            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if analysis:
                analysis.status = AnalysisStatus.failed
                analysis.error = "Analysis pipeline failed. Please try again."
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()



@router.post(
    "",
    response_model=AnalysisAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(check_rate_limit("analyses_create", max_requests=10, window_seconds=3600))],
)
def create_analysis(
    data: AnalysisCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(
        Resume.id == data.resume_id,
        Resume.user_id == current_user.id,
    ).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    jd_text = data.job_description.strip() if data.job_description else None
    jd_normalized = (jd_text or "")[:200]

    in_flight = db.query(Analysis).filter(
        Analysis.user_id == current_user.id,
        Analysis.resume_id == data.resume_id,
        Analysis.status == AnalysisStatus.pending,
    ).first()
    if in_flight:
        if jd_normalized == ((in_flight.job_description or "")[:200]):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An identical analysis is already in progress for this resume.",
            )

    analysis = Analysis(
        user_id=current_user.id,
        resume_id=data.resume_id,
        job_description=jd_text,
        resume_score=0,
        detected_skills=[],
        matching_skills=[],
        missing_skills=[],
        sections={},
        strengths=[],
        weaknesses=[],
        recommendations=[],
        status=AnalysisStatus.pending,
        ai_unavailable=False,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    background_tasks.add_task(
        _run_pipeline,
        analysis.id,
        resume.extracted_text,
        jd_text,
    )

    return AnalysisAcceptedResponse(id=analysis.id, status=analysis.status)


@router.get("", response_model=AnalysisListResponse)
def list_analyses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None, description="Filter by resume filename"),
    has_job_description: Optional[bool] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Analysis).options(joinedload(Analysis.resume)).filter(Analysis.user_id == current_user.id)

    if search:
        query = query.join(Resume).filter(
            Resume.filename.ilike(f"%{search}%")
        )
    if has_job_description is True:
        query = query.filter(Analysis.job_description.isnot(None))
    elif has_job_description is False:
        query = query.filter(Analysis.job_description.is_(None))

    total = query.count()
    items = (
        query.order_by(Analysis.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return AnalysisListResponse(
        items=[_enrich_response(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = db.query(Analysis).options(joinedload(Analysis.resume)).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id,
    ).first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return _enrich_response(analysis)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.user_id == current_user.id,
    ).first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    db.delete(analysis)
    db.commit()
