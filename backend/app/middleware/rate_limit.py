from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
import time
import redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Connected to Redis for rate limiting")
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting, using in-memory: {e}")
            self.use_redis = False
            self.memory_store: Dict[str, Dict[str, int]] = {}

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request with security validation"""
        # Get direct client IP first
        direct_ip = getattr(request.client, "host", "unknown")
        
        # Only trust proxy headers if we're behind a known proxy
        # In production, configure TRUSTED_PROXY_IPS environment variable
        trusted_proxies = settings.__dict__.get('trusted_proxy_ips', []).split(',') if hasattr(settings, 'trusted_proxy_ips') else []
        
        if direct_ip in trusted_proxies:
            # Check for forwarded headers only from trusted proxies
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                # Validate IP format to prevent header injection
                ip = forwarded_for.split(",")[0].strip()
                if self._is_valid_ip(ip):
                    return ip
            
            real_ip = request.headers.get("X-Real-IP")
            if real_ip and self._is_valid_ip(real_ip):
                return real_ip
        
        # Always return direct IP if proxy headers aren't trusted
        return direct_ip
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def _get_key(self, identifier: str, endpoint: str = "general") -> str:
        """Generate Redis key for rate limiting"""
        return f"rate_limit:{endpoint}:{identifier}"

    def _check_rate_limit_redis(self, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        """Check rate limit using Redis"""
        try:
            pipe = self.redis_client.pipeline()
            now = int(time.time())
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, now - window)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Count requests in window
            pipe.zcard(key)
            # Set expiry
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_requests = results[2]
            
            remaining = max(0, limit - current_requests)
            reset_time = now + window
            
            return current_requests <= limit, remaining, reset_time
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fallback to allowing request if Redis fails
            return True, limit, int(time.time() + window)

    def _check_rate_limit_memory(self, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        """Check rate limit using in-memory store"""
        now = int(time.time())
        
        if key not in self.memory_store:
            self.memory_store[key] = {"requests": [], "reset_time": now + window}
        
        bucket = self.memory_store[key]
        
        # Remove old requests
        bucket["requests"] = [req_time for req_time in bucket["requests"] if req_time > now - window]
        
        # Add current request
        bucket["requests"].append(now)
        
        current_requests = len(bucket["requests"])
        remaining = max(0, limit - current_requests)
        reset_time = now + window
        
        return current_requests <= limit, remaining, reset_time

    def check_rate_limit(
        self, 
        request: Request, 
        limit: Optional[int] = None, 
        window: int = 60,
        endpoint: str = "general"
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit
        Returns (allowed, remaining, reset_time)
        """
        if limit is None:
            limit = settings.api_rate_limit_per_minute
        
        client_ip = self._get_client_ip(request)
        key = self._get_key(client_ip, endpoint)
        
        if self.use_redis:
            return self._check_rate_limit_redis(key, limit, window)
        else:
            return self._check_rate_limit_memory(key, limit, window)

    def check_login_attempts(self, identifier: str) -> tuple[bool, int]:
        """
        Check if login attempts are within limit
        Returns (allowed, remaining_attempts)
        """
        key = self._get_key(identifier, "login_attempts")
        window = settings.lockout_duration_minutes * 60
        
        allowed, remaining, _ = self._check_rate_limit_redis(key, settings.max_login_attempts, window) if self.use_redis else self._check_rate_limit_memory(key, settings.max_login_attempts, window)
        
        return allowed, remaining

    def record_failed_login(self, identifier: str):
        """Record a failed login attempt"""
        key = self._get_key(identifier, "failed_login")
        
        if self.use_redis:
            try:
                now = int(time.time())
                window = settings.lockout_duration_minutes * 60
                
                pipe = self.redis_client.pipeline()
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, window)
                pipe.execute()
                
            except Exception as e:
                logger.error(f"Failed to record login attempt in Redis: {e}")
        else:
            # For memory store, this is handled in check_rate_limit_memory
            pass

    def get_lockout_time(self, identifier: str) -> Optional[int]:
        """Get remaining lockout time in seconds"""
        key = self._get_key(identifier, "failed_login")
        
        if self.use_redis:
            try:
                ttl = self.redis_client.ttl(key)
                return ttl if ttl > 0 else None
            except Exception as e:
                logger.error(f"Failed to get lockout time from Redis: {e}")
                return None
        else:
            # For memory store, calculate based on stored data
            now = int(time.time())
            if key in self.memory_store:
                reset_time = self.memory_store[key].get("reset_time", now)
                remaining = reset_time - now
                return remaining if remaining > 0 else None
            return None


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware class"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Check general API rate limit
        allowed, remaining, reset_time = rate_limiter.check_rate_limit(request)
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Too many requests. Limit: {settings.api_rate_limit_per_minute} per minute",
                    "remaining": remaining,
                    "reset_time": reset_time
                },
                headers={
                    "X-RateLimit-Limit": str(settings.api_rate_limit_per_minute),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(60)  # Retry after 60 seconds
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(settings.api_rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response