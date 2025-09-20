"""
Authentication API endpoints for Ultimate Fantasy Platform
Provides REST API for user registration, login, password reset, and account management
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr, validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ...infrastructure.database.session_factory import get_db_session
from ...domains.users.services.user_service import UserService
from ...domains.shared.exceptions import (
    UserNotFoundError, AuthenticationError, EmailAlreadyExistsError,
    UsernameAlreadyExistsError, InvalidTokenError, TokenExpiredError,
    WeakPasswordError, AccountDisabledError, TooManyAttemptsError
)
from ..middleware.auth import get_current_user, get_optional_current_user
from ..models.response import APIResponse, ErrorResponse
from ...models.user import User


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)

user_service = UserService()


# Pydantic Models for Request/Response
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    timezone: str = Field(default="UTC", description="User timezone")

    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v.lower()

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Password")
    remember_me: bool = Field(default=False, description="Remember login")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    timezone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    timezone: str
    preferences: Dict[str, Any]

    class Config:
        from_attributes = True


class LoginActivityResponse(BaseModel):
    session_id: str
    ip_address: str
    user_agent: str
    login_time: datetime
    last_activity: datetime
    is_current: bool
    location: Optional[str]

    class Config:
        from_attributes = True


# Authentication Endpoints
@router.post("/register", response_model=APIResponse[TokenResponse])
async def register(
    request: RegisterRequest,
    client_request: Request,
    db: Session = Depends(get_db_session)
):
    """Register a new user account"""
    try:
        user = user_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            date_of_birth=request.date_of_birth,
            timezone=request.timezone,
            db=db
        )

        # Generate tokens
        access_token = user_service.create_access_token(user.user_id)
        refresh_token = user_service.create_refresh_token(user.user_id)

        # Log the registration
        user_service.log_user_activity(
            user_id=str(user.user_id),
            activity_type="registration",
            ip_address=client_request.client.host,
            user_agent=client_request.headers.get("user-agent"),
            db=db
        )

        token_data = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,  # 1 hour
            user_id=str(user.user_id)
        )

        return APIResponse(
            success=True,
            data=token_data,
            message="Account created successfully"
        )

    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered"
        )
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(
    request: LoginRequest,
    client_request: Request,
    db: Session = Depends(get_db_session)
):
    """Login with username/email and password"""
    try:
        user = user_service.authenticate_user(
            username_or_email=request.username_or_email,
            password=request.password,
            db=db
        )

        # Generate tokens
        expires_in = 7 * 24 * 3600 if request.remember_me else 3600  # 7 days or 1 hour
        access_token = user_service.create_access_token(str(user.user_id), expires_in=expires_in)
        refresh_token = user_service.create_refresh_token(str(user.user_id))

        # Log the login
        user_service.log_user_activity(
            user_id=str(user.user_id),
            activity_type="login",
            ip_address=client_request.client.host,
            user_agent=client_request.headers.get("user-agent"),
            db=db
        )

        token_data = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user_id=str(user.user_id)
        )

        return APIResponse(
            success=True,
            data=token_data,
            message="Login successful"
        )

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    except AccountDisabledError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    except TooManyAttemptsError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db_session)
):
    """Refresh access token using refresh token"""
    try:
        token_data = user_service.refresh_access_token(request.refresh_token, db)

        return APIResponse(
            success=True,
            data=token_data,
            message="Token refreshed successfully"
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
):
    """Logout and invalidate current session"""
    try:
        if credentials:
            user_service.invalidate_token(credentials.credentials, db)

        user_service.log_user_activity(
            user_id=current_user["user_id"],
            activity_type="logout",
            db=db
        )

        return APIResponse(
            success=True,
            data=None,
            message="Logout successful"
        )

    except InvalidTokenError:
        # Token already invalid, still return success
        pass

    return APIResponse(
        success=True,
        data=None,
        message="Logout successful"
    )


# Password Management
@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db_session)
):
    """Request password reset email"""
    try:
        user_service.initiate_password_reset(request.email, db)

        # Always return success to avoid email enumeration
        return APIResponse(
            success=True,
            data=None,
            message="If an account exists with this email, a reset link has been sent"
        )

    except UserNotFoundError:
        # Don't reveal that user doesn't exist
        return APIResponse(
            success=True,
            data=None,
            message="If an account exists with this email, a reset link has been sent"
        )


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db_session)
):
    """Reset password using token from email"""
    try:
        user_service.reset_password(
            token=request.token,
            new_password=request.new_password,
            db=db
        )

        return APIResponse(
            success=True,
            data=None,
            message="Password reset successfully"
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Change password for authenticated user"""
    try:
        user_service.change_password(
            user_id=current_user["user_id"],
            current_password=request.current_password,
            new_password=request.new_password,
            db=db
        )

        return APIResponse(
            success=True,
            data=None,
            message="Password changed successfully"
        )

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Profile Management
@router.get("/profile", response_model=APIResponse[UserResponse])
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get current user profile"""
    try:
        user = user_service.get_user(current_user["user_id"], db)

        return APIResponse(
            success=True,
            data=UserResponse.from_orm(user),
            message="Profile retrieved successfully"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.put("/profile", response_model=APIResponse[UserResponse])
async def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update user profile"""
    try:
        update_data = request.dict(exclude_unset=True)
        user = user_service.update_user_profile(
            user_id=current_user["user_id"],
            update_data=update_data,
            db=db
        )

        return APIResponse(
            success=True,
            data=UserResponse.from_orm(user),
            message="Profile updated successfully"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already in use"
        )


@router.delete("/profile")
async def delete_account(
    password: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Delete user account (requires password confirmation)"""
    try:
        user_service.delete_user_account(
            user_id=current_user["user_id"],
            password=password,
            db=db
        )

        return APIResponse(
            success=True,
            data=None,
            message="Account deleted successfully"
        )

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


# Email Verification
@router.post("/resend-verification")
async def resend_verification_email(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Resend email verification"""
    try:
        user_service.resend_verification_email(current_user["user_id"], db)

        return APIResponse(
            success=True,
            data=None,
            message="Verification email sent"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db_session)
):
    """Verify email address using token"""
    try:
        user_service.verify_email(token, db)

        return APIResponse(
            success=True,
            data=None,
            message="Email verified successfully"
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )


# Session Management
@router.get("/sessions", response_model=APIResponse[List[LoginActivityResponse]])
async def get_active_sessions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get all active sessions for the user"""
    try:
        sessions = user_service.get_user_sessions(current_user["user_id"], db)

        return APIResponse(
            success=True,
            data=[LoginActivityResponse.from_orm(session) for session in sessions],
            message="Active sessions retrieved successfully"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Revoke a specific session"""
    try:
        user_service.revoke_session(
            user_id=current_user["user_id"],
            session_id=session_id,
            db=db
        )

        return APIResponse(
            success=True,
            data=None,
            message="Session revoked successfully"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )


@router.delete("/sessions")
async def revoke_all_sessions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Revoke all sessions except current"""
    try:
        revoked_count = user_service.revoke_all_sessions(current_user["user_id"], db)

        return APIResponse(
            success=True,
            data={"revoked_sessions": revoked_count},
            message="All other sessions revoked successfully"
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


# Token Validation
@router.get("/validate")
async def validate_token(
    current_user: dict = Depends(get_current_user)
):
    """Validate current token and return user info"""
    return APIResponse(
        success=True,
        data={
            "user_id": current_user["user_id"],
            "username": current_user["username"],
            "is_valid": True
        },
        message="Token is valid"
    )