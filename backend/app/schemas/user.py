import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from backend.app.models.user import UserRole


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        b = v.encode("utf-8")
        if len(b) < 8 or len(b) > 72:
            raise ValueError("Password must be between 8 and 72 bytes")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserAdminUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class AdminDayCount(BaseModel):
    date: str
    count: int


class AdminFailedAnalysisItem(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    resume_filename: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime


class AdminStatsResponse(BaseModel):
    users: int
    resumes: int
    analyses: int
    failed_analyses: int
    analyses_last_7_days: list[AdminDayCount]
    recent_failures: list[AdminFailedAnalysisItem]


class AdminUsersResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
