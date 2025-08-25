from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr, field_validator, ValidationInfo
from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, decode_access_token, 
    validate_password, create_token_pair, decode_refresh_token
)
from app.core.validation import (
    sanitize_string, validate_email, validate_username, 
    validate_password_strength, check_sql_injection, check_xss_patterns
)
from app.core.error_handlers import ValidationAPIError, AuthenticationError, ConflictError
from app.models import User
from app.core.config import settings
from app.middleware.rate_limit import rate_limiter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator('username')
    @classmethod
    def validate_username_field(cls, v: str) -> str:
        # Sanitize input
        v = sanitize_string(v, max_length=50)
        
        # Check for injection attempts
        if check_sql_injection(v) or check_xss_patterns(v):
            raise ValueError('Invalid characters in username')
        
        # Validate format
        if not validate_username(v):
            raise ValueError('Username must be 3-50 characters and contain only letters, numbers, underscores, and hyphens')
        
        return v.lower()

    @field_validator('email')
    @classmethod
    def validate_email_field(cls, v: str) -> str:
        # Sanitize input
        v = sanitize_string(v, max_length=254)
        
        # Check for injection attempts
        if check_sql_injection(v) or check_xss_patterns(v):
            raise ValueError('Invalid characters in email')
        
        # Validate email format
        if not validate_email(v):
            raise ValueError('Invalid email format')
        
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password_field(cls, v: str) -> str:
        # Check for injection attempts (passwords can have special chars but not SQL/XSS)
        if check_sql_injection(v):
            raise ValueError('Invalid characters in password')
        
        # Validate password strength
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Remove demo token vulnerability - only accept valid JWTs
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user


def _get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting (IP + User-Agent hash)"""
    client_ip = getattr(request.client, "host", "unknown")
    user_agent = request.headers.get("user-agent", "")
    return f"{client_ip}:{hash(user_agent)}"


@router.post("/token", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """Authenticate user and return access/refresh tokens"""
    client_id = _get_client_identifier(request)
    
    # Check for account lockout
    allowed, remaining = rate_limiter.check_login_attempts(client_id)
    if not allowed:
        lockout_time = rate_limiter.get_lockout_time(client_id)
        lockout_minutes = lockout_time // 60 if lockout_time else 15
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked due to too many failed attempts. Try again in {lockout_minutes} minutes.",
            headers={"Retry-After": str(lockout_time or 900)}
        )
    
    # Try to find user by username or email (case-insensitive)
    identifier = form_data.username.lower().strip()
    user = db.query(User).filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()
    
    # Verify credentials
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Record failed attempt
        rate_limiter.record_failed_login(client_id)
        logger.warning(f"Failed login attempt for identifier: {identifier} from {client_id}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )
    
    # Create token pair
    tokens = create_token_pair({"sub": user.username, "user_id": user.id})
    
    logger.info(f"Successful login for user: {user.username}")
    
    return TokenResponse(**tokens)


@router.post("/register", response_model=UserResponse)
async def register(
    request: Request,
    user_data: RegisterRequest, 
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    client_id = _get_client_identifier(request)
    
    # Rate limit registration attempts
    allowed, remaining, _ = rate_limiter.check_rate_limit(request, limit=5, endpoint="register")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later.",
        )
    
    # Check if user already exists (case-insensitive)
    existing_user = db.query(User).filter(
        (User.username == user_data.username.lower()) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create new user
    try:
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username.lower(),
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"New user registered: {db_user.username}")
        
        return UserResponse(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            is_active=db_user.is_active
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode refresh token
    payload = decode_refresh_token(token_data.refresh_token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    # Verify user still exists and is active
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception
    
    # Create new token pair
    tokens = create_token_pair({"sub": user.username, "user_id": user.id})
    
    logger.info(f"Token refreshed for user: {user.username}")
    
    return TokenResponse(**tokens)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard tokens)"""
    # In a production system, you might want to blacklist the tokens
    # For now, we rely on the client to discard the tokens
    logger.info(f"User logged out: {current_user.username}")
    return {"detail": "Successfully logged out"}