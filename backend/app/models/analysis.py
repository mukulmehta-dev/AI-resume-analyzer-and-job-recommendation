import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from backend.app.db.session import Base
from backend.app.models.user import GUID


class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    done = "done"
    failed = "failed"


JSONType = JSON().with_variant(JSONB, "postgresql")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(GUID(), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description = Column(Text, nullable=True)
    resume_score = Column(Integer, nullable=False, default=0)
    compatibility_score = Column(Integer, nullable=True)
    detected_skills = Column(JSONType, nullable=False, default=list)
    matching_skills = Column(JSONType, nullable=False, default=list)
    missing_skills = Column(JSONType, nullable=False, default=list)
    sections = Column(JSONType, nullable=False, default=dict)
    strengths = Column(JSONType, nullable=False, default=list)
    weaknesses = Column(JSONType, nullable=False, default=list)
    recommendations = Column(JSONType, nullable=False, default=list)
    summary_feedback = Column(Text, nullable=True)
    ai_unavailable = Column(Boolean, nullable=False, default=False)
    ai_model = Column(Text, nullable=True)
    job_tailored_tips = Column(JSONType, nullable=False, default=list)
    job_skills = Column(JSONType, nullable=False, default=list)
    ai_insights = Column(JSONType, nullable=True)
    status = Column(
        SAEnum(AnalysisStatus, name="analysis_status", native_enum=False),
        default=AnalysisStatus.pending,
        nullable=False,
    )
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", backref="analyses")
    resume = relationship("Resume", backref="analyses")
