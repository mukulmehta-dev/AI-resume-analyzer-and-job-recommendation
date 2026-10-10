import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.user import User, UserRole
from backend.app.models.resume import Resume
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.schemas.user import (
    UserResponse,
    UserAdminUpdateRequest,
    AdminStatsResponse,
    AdminDayCount,
    AdminFailedAnalysisItem,
    AdminUsersResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to access this resource.",
        )
    return current_user


@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    admin_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    users_count = db.query(User).count()
    resumes_count = db.query(Resume).count()
    analyses_count = db.query(Analysis).count()
    failed_analyses_count = (
        db.query(Analysis).filter(Analysis.status == AnalysisStatus.failed).count()
    )

    now = datetime.now(timezone.utc)
    today = now.date()
    analyses_per_day = []

    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        start_dt = datetime(
            target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=timezone.utc
        )
        end_dt = start_dt + timedelta(days=1)
        cnt = (
            db.query(Analysis)
            .filter(Analysis.created_at >= start_dt, Analysis.created_at < end_dt)
            .count()
        )
        analyses_per_day.append(
            AdminDayCount(date=target_date.strftime("%Y-%m-%d"), count=cnt)
        )

    failed_records = (
        db.query(Analysis)
        .filter(Analysis.status == AnalysisStatus.failed)
        .order_by(Analysis.created_at.desc())
        .limit(10)
        .all()
    )

    recent_failures = [
        AdminFailedAnalysisItem(
            id=f.id,
            resume_id=f.resume_id,
            resume_filename=f.resume.filename if f.resume else None,
            error=f.error,
            created_at=f.created_at,
        )
        for f in failed_records
    ]

    return AdminStatsResponse(
        users=users_count,
        resumes=resumes_count,
        analyses=analyses_count,
        failed_analyses=failed_analyses_count,
        analyses_last_7_days=analyses_per_day,
        recent_failures=recent_failures,
    )


@router.get("/users", response_model=AdminUsersResponse)
def list_admin_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    admin_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query = query.filter(User.email.ilike(term))

    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AdminUsersResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user_admin(
    user_id: uuid.UUID,
    data: UserAdminUpdateRequest,
    admin_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    demoting_or_deactivating = (data.is_active is False) or (
        data.role is not None and data.role != UserRole.admin
    )

    if target.id == admin_user.id and demoting_or_deactivating:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate or demote their own account.",
        )

    if target.role == UserRole.admin and target.is_active and demoting_or_deactivating:
        active_admins = (
            db.query(User)
            .filter(User.role == UserRole.admin, User.is_active == True)
            .count()
        )
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate or demote the last active administrator.",
            )

    if data.is_active is not None:
        target.is_active = data.is_active
    if data.role is not None:
        target.role = data.role

    db.commit()
    db.refresh(target)
    return UserResponse.model_validate(target)
