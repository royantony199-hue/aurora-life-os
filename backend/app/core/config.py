from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ValidationInfo
from typing import Optional, List
import os
import secrets
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="Aurora Life OS", env="APP_NAME")
    version: str = Field(default="1.0.0", env="VERSION")
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Security
    secret_key: str = Field(env="SECRET_KEY")
    refresh_secret_key: str = Field(env="REFRESH_SECRET_KEY")
    encryption_key: str = Field(env="ENCRYPTION_KEY")
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # JWT Configuration
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # API Security
    api_rate_limit_per_minute: int = Field(default=100, env="API_RATE_LIMIT_PER_MINUTE")
    max_login_attempts: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    lockout_duration_minutes: int = Field(default=15, env="LOCKOUT_DURATION_MINUTES")
    
    # CORS
    allowed_origins: str = Field(default="http://localhost:5173,http://localhost:3000", env="ALLOWED_ORIGINS")
    allowed_hosts: str = Field(default="localhost,127.0.0.1", env="ALLOWED_HOSTS")
    
    # External APIs
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Google Services
    google_client_id: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: Optional[str] = Field(default=None, env="GOOGLE_REDIRECT_URI")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Monitoring & Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # Email
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    from_email: str = Field(default="noreply@auroralifeos.com", env="FROM_EMAIL")
    
    # File Storage
    upload_dir: str = Field(default="/app/uploads", env="UPLOAD_DIR")
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    
    # SSL/HTTPS
    ssl_keyfile: Optional[str] = Field(default=None, env="SSL_KEYFILE")
    ssl_certfile: Optional[str] = Field(default=None, env="SSL_CERTFILE")
    force_https: bool = Field(default=False, env="FORCE_HTTPS")
    
    # Security Settings
    trusted_proxy_ips: str = Field(default="", env="TRUSTED_PROXY_IPS")
    session_timeout_minutes: int = Field(default=480, env="SESSION_TIMEOUT_MINUTES")  # 8 hours
    max_request_size_mb: int = Field(default=10, env="MAX_REQUEST_SIZE_MB")
    allowed_file_extensions: str = Field(default="jpg,jpeg,png,gif,pdf,txt,doc,docx", env="ALLOWED_FILE_EXTENSIONS")
    
    # Rate Limiting
    api_rate_limit_burst: int = Field(default=200, env="API_RATE_LIMIT_BURST")
    login_rate_limit_per_hour: int = Field(default=10, env="LOGIN_RATE_LIMIT_PER_HOUR")
    
    # Content Security
    enable_csrf_protection: bool = Field(default=True, env="ENABLE_CSRF_PROTECTION")
    content_security_policy: str = Field(
        default="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'",
        env="CONTENT_SECURITY_POLICY"
    )

    @field_validator('secret_key', 'refresh_secret_key', 'encryption_key')
    @classmethod
    def validate_secrets(cls, v: str, info: ValidationInfo) -> str:
        field_name = info.field_name
        if not v:
            raise ValueError(f'{field_name} must be set')
        if field_name in ['secret_key', 'refresh_secret_key'] and len(v) < 32:
            raise ValueError(f'{field_name} must be at least 32 characters long')
        if field_name == 'encryption_key':
            # Encryption key should be a base64 encoded Fernet key (44 characters)
            if len(v) < 32:
                raise ValueError('encryption_key must be at least 32 characters long')
            # Could be either a raw key or base64 encoded key
        return v

    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str, info: ValidationInfo) -> str:
        # Allow SQLite for development
        data = info.data if hasattr(info, 'data') else {}
        environment = data.get('environment', Environment.DEVELOPMENT)
        
        if environment == Environment.DEVELOPMENT and v.startswith('sqlite:'):
            return v
        elif v.startswith(('postgresql://', 'postgres://')):
            return v
        else:
            raise ValueError('database_url must be a PostgreSQL URL (or SQLite for development)')
        return v

    @field_validator('allowed_origins')
    @classmethod
    def validate_cors_origins(cls, v: str, info: ValidationInfo) -> str:
        # Get environment from context if available
        data = info.data if hasattr(info, 'data') else {}
        if data.get('environment') == Environment.PRODUCTION and '*' in v:
            raise ValueError('Wildcard CORS origins not allowed in production')
        return v

    @property
    def cors_origins(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.allowed_origins.split(',')]

    @property
    def cors_hosts(self) -> List[str]:
        """Convert comma-separated hosts to list"""
        return [host.strip() for host in self.allowed_hosts.split(',')]

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    def generate_secure_key(self) -> str:
        """Generate a secure random key"""
        return secrets.token_urlsafe(32)

    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    print("📋 Please check your .env file and ensure all required variables are set.")
    print("📄 Copy .env.example to .env and update the values.")
    raise