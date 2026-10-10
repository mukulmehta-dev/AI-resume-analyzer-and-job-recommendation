import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AnalysisCreateRequest(BaseModel):
    resume_id: uuid.UUID
    job_description: Optional[str] = Field(default=None, max_length=20000)


class RecommendationItem(BaseModel):
    title: str
    detail: str
    priority: str


class SkillWithCategory(BaseModel):
    name: str
    category: str


class AnalysisResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    resume_filename: Optional[str] = None
    user_id: uuid.UUID
    job_description: Optional[str]
    resume_score: int
    compatibility_score: Optional[int]
    detected_skills: List[str]
    detected_skills_with_category: Optional[List[SkillWithCategory]] = None
    matching_skills: List[str]
    missing_skills: List[str]
    sections: Dict[str, Any]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[Any]
    summary_feedback: Optional[str]
    ai_unavailable: bool
    status: str
    error: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisAcceptedResponse(BaseModel):
    id: uuid.UUID
    status: str


class AnalysisListResponse(BaseModel):
    items: List[AnalysisResponse]
    total: int
    page: int
    page_size: int
