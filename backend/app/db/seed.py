from sqlalchemy.orm import Session
from backend.app.models.user import User, UserRole
from backend.app.core.config import settings
from backend.app.core.security import hash_password


def seed_admin(db: Session) -> None:
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        return

    admin_exists = db.query(User).filter(User.role == UserRole.admin).first()
    if admin_exists:
        return

    user_by_email = db.query(User).filter(User.email == settings.ADMIN_EMAIL.lower().strip()).first()
    if user_by_email:
        user_by_email.role = UserRole.admin
        db.commit()
        return

    admin_user = User(
        name="System Administrator",
        email=settings.ADMIN_EMAIL.lower().strip(),
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        role=UserRole.admin,
        is_active=True
    )
    db.add(admin_user)
    db.commit()
