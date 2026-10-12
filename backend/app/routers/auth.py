from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole
from backend.app.schemas.user import UserRegisterRequest, UserLoginRequest, UserResponse
from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.core.deps import get_current_user
from backend.app.core.ratelimit import check_rate_limit, get_client_ip, record_and_check_limit
from backend.app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_rate_limit("auth_register", max_requests=30, window_seconds=60))]
)
def register(
    data: UserRegisterRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    user = User(
        name=data.name.strip(),
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        role=UserRole.user,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=86400,
        path="/"
    )
    return user


@router.post(
    "/login",
    response_model=UserResponse
)
def login(
    request: Request,
    data: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    client_ip = get_client_ip(request)
    record_and_check_limit(f"auth_login_ip:{client_ip}", max_requests=100, window_seconds=60)
    record_and_check_limit(f"auth_login_ip_email:{client_ip}:{data.email.lower().strip()}", max_requests=10, window_seconds=60)

    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    token = create_access_token(user.id)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=86400,
        path="/"
    )
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE
    )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
