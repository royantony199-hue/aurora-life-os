"""
Input validation and sanitization utilities
"""
import re
import html
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, validator
import bleach


class ValidationError(Exception):
    """Custom validation error"""
    pass


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input to prevent XSS and other attacks"""
    if not isinstance(value, str):
        raise ValidationError("Value must be a string")
    
    # Remove HTML tags and escape special characters
    sanitized = bleach.clean(value, tags=[], strip=True)
    sanitized = html.escape(sanitized)
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> bool:
    """Validate username format"""
    # Only alphanumeric characters, underscores, and hyphens
    # 3-50 characters long
    pattern = r'^[a-zA-Z0-9_-]{3,50}$'
    return bool(re.match(pattern, username))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"


def validate_date_string(date_str: str) -> bool:
    """Validate date string format (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_datetime_string(datetime_str: str) -> bool:
    """Validate datetime string format (ISO 8601)"""
    try:
        datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def validate_positive_integer(value: Any) -> bool:
    """Validate that value is a positive integer"""
    try:
        int_val = int(value)
        return int_val > 0
    except (ValueError, TypeError):
        return False


def validate_file_upload(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file upload"""
    if not filename:
        return False
    
    # Check file extension
    extension = filename.lower().split('.')[-1]
    return extension in allowed_extensions


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove directory traversal attempts
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    
    # Keep only alphanumeric, dots, hyphens, and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:250] + ('.' + ext if ext else '')
    
    return sanitized


class BaseValidator(BaseModel):
    """Base validator with common validation methods"""
    
    @validator('*', pre=True)
    def sanitize_strings(cls, v):
        """Sanitize all string inputs"""
        if isinstance(v, str):
            return sanitize_string(v)
        return v


def validate_json_size(data: Dict[str, Any], max_size_mb: int = 10) -> bool:
    """Validate JSON payload size"""
    import json
    import sys
    
    try:
        json_str = json.dumps(data)
        size_mb = sys.getsizeof(json_str) / (1024 * 1024)
        return size_mb <= max_size_mb
    except Exception:
        return False


def validate_ip_address(ip: str) -> bool:
    """Validate IP address format"""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


# SQL Injection prevention patterns
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
    r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
    r"(-{2}|/\*|\*/)",
    r"(\bxp_cmdshell\b)",
    r"(\bsp_executesql\b)",
]


def check_sql_injection(value: str) -> bool:
    """Check for potential SQL injection patterns"""
    if not isinstance(value, str):
        return False
    
    value_upper = value.upper()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value_upper, re.IGNORECASE):
            return True
    return False


# XSS prevention patterns
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"vbscript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>.*?</iframe>",
    r"<object[^>]*>.*?</object>",
    r"<embed[^>]*>.*?</embed>",
]


def check_xss_patterns(value: str) -> bool:
    """Check for potential XSS patterns"""
    if not isinstance(value, str):
        return False
    
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
            return True
    return False