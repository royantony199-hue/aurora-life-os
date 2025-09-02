from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import time
import uuid
from app.core.config import settings
from app.core.database import engine, Base
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.error_handlers import (
    APIError, api_error_handler, http_exception_handler,
    validation_error_handler, sqlalchemy_error_handler, general_exception_handler
)
# from app.core.celery_app import celery_app
from app.routers import auth, users, goals, calendar, config, notifications, proactive, tasks, voice_commands, coaching, analytics, autonomous, ai_calendar
from app.routers import chat as chat_router
from app.routers import mood as mood_router
# Import all models to register them with SQLAlchemy
from app.models import user, chat, goal, mood, calendar as calendar_models, task

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database migrations are handled by Alembic
# Run: alembic upgrade head
# To create/update tables, use Alembic migrations instead of create_all()
# Base.metadata.create_all(bind=engine)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to requests for tracking"""
    async def dispatch(self, request: Request, call_next):
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HTTPS enforcement in production
        if settings.is_production or settings.force_https:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = settings.content_security_policy
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate request size and content"""
    async def dispatch(self, request: Request, call_next):
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length:
            content_length_mb = int(content_length) / (1024 * 1024)
            if content_length_mb > settings.max_request_size_mb:
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large", "max_size_mb": settings.max_request_size_mb}
                )
        
        response = await call_next(request)
        return response


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI Companion App for personal growth and productivity",
    debug=settings.debug and settings.is_development,
)

# Security middleware (order matters)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CorrelationIDMiddleware)

# Register error handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Trusted host middleware for production
if settings.is_production:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.cors_hosts)

# Configure CORS with proper security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Mx-ReqToken",
        "Keep-Alive",
        "X-Requested-With",
    ],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
app.include_router(goals.router, prefix="/api/goals", tags=["goals"])
app.include_router(mood_router.router, prefix="/api/mood", tags=["mood"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(config.router, prefix="/api/config", tags=["configuration"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(proactive.router, prefix="/api/proactive", tags=["proactive-messaging"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(voice_commands.router, prefix="/api/voice", tags=["voice-commands"])
app.include_router(coaching.router, prefix="/api/coaching", tags=["goal-coaching"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(autonomous.router, prefix="/api/autonomous", tags=["autonomous-scheduling"])
app.include_router(ai_calendar.router, prefix="/api/ai-calendar", tags=["ai-calendar"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Aurora Life OS is running!", "status": "ok", "version": settings.version}

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok"}


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependency status"""
    from app.core.database import get_db
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.version,
        "environment": settings.environment,
        "checks": {}
    }
    
    # Database check
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "healthy", "response_time_ms": 0}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    finally:
        if 'db' in locals():
            db.close()
    
    # Redis check (if enabled)
    if hasattr(settings, 'redis_url'):
        try:
            from app.middleware.rate_limit import rate_limiter
            if rate_limiter.use_redis:
                rate_limiter.redis_client.ping()
                health_status["checks"]["redis"] = {"status": "healthy"}
            else:
                health_status["checks"]["redis"] = {"status": "disabled"}
        except Exception as e:
            health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
    
    return health_status


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🌅 Aurora Life OS - AI Personal Assistant")
    logger.info("=" * 50)
    logger.info(f"🔍 Environment: {settings.environment}")
    logger.info(f"🔐 Debug mode: {settings.debug}")
    logger.info(f"📊 Metrics enabled: {settings.enable_metrics}")
    logger.info(f"🌐 CORS origins: {len(settings.cors_origins)} configured")
    
    # Security warnings
    if settings.is_development:
        logger.warning("⚠️  Running in DEVELOPMENT mode - not for production use!")
        if "*" in settings.allowed_origins:
            logger.warning("⚠️  CORS allows all origins - security risk!")
    
    if settings.is_production:
        logger.info("🔒 Production mode - security enhanced")
        if not settings.force_https:
            logger.warning("⚠️  HTTPS not enforced in production!")
    
    # Check critical dependencies
    try:
        from app.middleware.rate_limit import rate_limiter
        logger.info("✅ Rate limiting initialized")
    except Exception as e:
        logger.error(f"❌ Rate limiting failed: {e}")
    
    logger.info("✅ Aurora Life OS backend services initialized")
    logger.info(f"🚀 Server starting on environment: {settings.environment}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Aurora Life OS shutting down...")
    logger.info("✅ Cleanup completed")


@app.get("/api/scheduler/status")
async def scheduler_status():
    """Get scheduler status"""
    return {
        "status": "available",
        "message": "Scheduler available but not running"
    }


@app.post("/api/scheduler/trigger-daily-optimization")
async def trigger_daily_optimization():
    """Manually trigger daily calendar optimization"""
    return {
        "message": "Daily calendar optimization would be triggered (scheduler disabled)",
        "status": "simulated"
    }