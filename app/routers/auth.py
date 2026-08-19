"""
Authentication endpoints – JWT based.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, AccountStatus, AuditLog
from app.schemas import (
    LoginRequest, TokenResponse, ChangePasswordRequest, MessageResponse, UserOut
)
from app.security import (
    verify_password, hash_password, create_access_token,
    get_current_user
)
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES as TOKEN_EXPIRE

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    response: Response = None,
):
    """
    Login with username + password.
    Returns JWT access token.
    Also sets an httpOnly cookie for browser convenience.
    """
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="الحساب غير نشط. يرجى التواصل مع الإدارة.",
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Audit
    log = AuditLog(
        user_id=user.id,
        action="LOGIN",
        details=f"Successful login for {user.username}",
    )
    db.add(log)
    db.commit()

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value, "uid": user.id},
        expires_delta=timedelta(minutes=TOKEN_EXPIRE),
    )

    # Set cookie for browser sessions (optional convenience)
    if response is not None:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=TOKEN_EXPIRE * 60,
            samesite="lax",
            path="/",
        )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value,
        full_name=user.full_name,
        must_change_password=user.must_change_password,
        user_id=user.id,
    )


@router.post("/login-json", response_model=TokenResponse)
async def login_json(
    body: LoginRequest,
    db: Session = Depends(get_db),
    response: Response = None,
):
    """JSON body alternative to form login (useful for SPA / mobile)."""
    user = db.query(User).filter(User.username == body.username).first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
        )

    if user.status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="الحساب غير نشط. يرجى التواصل مع الإدارة.",
        )

    user.last_login = datetime.utcnow()
    db.commit()

    log = AuditLog(user_id=user.id, action="LOGIN", details=f"JSON login {user.username}")
    db.add(log)
    db.commit()

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value, "uid": user.id},
        expires_delta=timedelta(minutes=TOKEN_EXPIRE),
    )

    if response is not None:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=TOKEN_EXPIRE * 60,
            samesite="lax",
            path="/",
        )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role.value,
        full_name=user.full_name,
        must_change_password=user.must_change_password,
        user_id=user.id,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user profile."""
    return current_user


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Allow authenticated user to change their own password."""
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور الحالية غير صحيحة",
        )

    if len(body.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل",
        )

    current_user.password_hash = hash_password(body.new_password)
    current_user.must_change_password = False
    current_user.updated_at = datetime.utcnow()
    db.commit()

    log = AuditLog(
        user_id=current_user.id,
        action="PASSWORD_CHANGED",
        details="User changed own password",
    )
    db.add(log)
    db.commit()

    return MessageResponse(message="تم تغيير كلمة المرور بنجاح")


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    """Clear the auth cookie."""
    response.delete_cookie("access_token", path="/")
    return MessageResponse(message="تم تسجيل الخروج بنجاح")
