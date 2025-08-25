"""
Centralized error handling for the application
"""
import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.core.config import settings

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error class"""
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(APIError):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_ERROR",
            details=details
        )


class AuthorizationError(APIError):
    """Authorization related errors"""
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHZ_ERROR",
            details=details
        )


class ValidationAPIError(APIError):
    """Validation related errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details
        )


class NotFoundError(APIError):
    """Resource not found errors"""
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details
        )


class ConflictError(APIError):
    """Conflict errors (e.g., duplicate resources)"""
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT_ERROR",
            details=details
        )


class RateLimitError(APIError):
    """Rate limiting errors"""
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_ERROR",
            details=details
        )


def create_error_response(
    error: APIError,
    request: Optional[Request] = None,
    include_details: bool = None
) -> JSONResponse:
    """Create standardized error response"""
    
    if include_details is None:
        include_details = not settings.is_production
    
    response_data = {
        "error": True,
        "message": error.message,
        "error_code": error.error_code,
        "status_code": error.status_code
    }
    
    if include_details and error.details:
        response_data["details"] = error.details
    
    if include_details and request:
        response_data["path"] = str(request.url.path)
        response_data["method"] = request.method
    
    # Add correlation ID for tracking
    if request and hasattr(request.state, 'correlation_id'):
        response_data["correlation_id"] = request.state.correlation_id
    
    return JSONResponse(
        status_code=error.status_code,
        content=response_data
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors"""
    logger.warning(f"API Error: {exc.message} - {exc.error_code}", extra={
        "error_code": exc.error_code,
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method
    })
    
    return create_error_response(exc, request)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    api_error = APIError(
        message=exc.detail,
        status_code=exc.status_code,
        error_code="HTTP_ERROR"
    )
    
    return create_error_response(api_error, request)


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error['loc'])
        errors.append({
            "field": field,
            "message": error['msg'],
            "type": error['type']
        })
    
    api_error = ValidationAPIError(
        message="Validation failed",
        details={"validation_errors": errors}
    )
    
    logger.warning(f"Validation Error: {api_error.message}", extra={
        "validation_errors": errors,
        "path": request.url.path,
        "method": request.method
    })
    
    return create_error_response(api_error, request)


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors"""
    error_message = "Database error occurred"
    error_code = "DATABASE_ERROR"
    
    if isinstance(exc, IntegrityError):
        error_message = "Data integrity constraint violation"
        error_code = "INTEGRITY_ERROR"
        
        # Handle common integrity errors
        if "UNIQUE constraint failed" in str(exc):
            error_message = "Duplicate entry - resource already exists"
        elif "FOREIGN KEY constraint failed" in str(exc):
            error_message = "Referenced resource does not exist"
    
    api_error = APIError(
        message=error_message,
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code=error_code
    )
    
    logger.error(f"Database Error: {str(exc)}", extra={
        "error_type": type(exc).__name__,
        "path": request.url.path,
        "method": request.method
    })
    
    return create_error_response(api_error, request)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.error(f"Unhandled Exception: {str(exc)}", extra={
        "correlation_id": correlation_id,
        "path": request.url.path,
        "method": request.method,
        "exception_type": type(exc).__name__,
        "traceback": traceback.format_exc()
    })
    
    api_error = APIError(
        message="An unexpected error occurred" if settings.is_production else str(exc),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_ERROR",
        details={"correlation_id": correlation_id} if not settings.is_production else None
    )
    
    return create_error_response(api_error, request)


def log_error(
    error: Exception,
    context: Dict[str, Any] = None,
    level: str = "error"
) -> None:
    """Log error with context"""
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc()
    }
    
    if context:
        log_data.update(context)
    
    getattr(logger, level)(f"Error occurred: {str(error)}", extra=log_data)