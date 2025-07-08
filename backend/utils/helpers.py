"""
Helper utilities for the 3D Quotes application.
"""
import hashlib
import re
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def generate_order_id() -> str:
    """
    Generate a unique order ID.
    
    Returns:
        str: Unique order ID
    """
    return str(uuid.uuid4())


def generate_quote_id() -> str:
    """
    Generate a unique quote ID.
    
    Returns:
        str: Unique quote ID
    """
    return str(uuid.uuid4())


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    
    Args:
        length: Token length
        
    Returns:
        str: Secure token
    """
    return secrets.token_urlsafe(length)


def hash_string(text: str, salt: Optional[str] = None) -> str:
    """
    Hash a string with optional salt.
    
    Args:
        text: Text to hash
        salt: Optional salt
        
    Returns:
        str: Hashed string
    """
    if salt:
        text = f"{text}{salt}"

    return hashlib.sha256(text.encode()).hexdigest()


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format currency amount.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        str: Formatted currency string
    """
    if currency.upper() == "USD":
        return f"${amount:.2f}"
    else:
        return f"{amount:.2f} {currency.upper()}"


def calculate_expiry_date(hours: int = 24) -> datetime:
    """
    Calculate expiry date from now.
    
    Args:
        hours: Hours from now
        
    Returns:
        datetime: Expiry date
    """
    return datetime.utcnow() + timedelta(hours=hours)


def is_expired(expiry_date: datetime) -> bool:
    """
    Check if a date has expired.
    
    Args:
        expiry_date: Date to check
        
    Returns:
        bool: True if expired
    """
    return datetime.utcnow() > expiry_date


def clean_filename(filename: str) -> str:
    """
    Clean filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Cleaned filename
    """
    # Remove invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Limit length
    if len(cleaned) > 255:
        name, ext = cleaned.rsplit('.', 1) if '.' in cleaned else (cleaned, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        cleaned = name[:max_name_length] + ('.' + ext if ext else '')

    return cleaned


def parse_file_size(size_str: str) -> int:
    """
    Parse file size string to bytes.
    
    Args:
        size_str: Size string like "10MB", "5GB", etc.
        
    Returns:
        int: Size in bytes
    """
    size_str = size_str.upper().strip()

    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Human-readable size
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        dict: Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def calculate_percentage(part: float, whole: float) -> float:
    """
    Calculate percentage.
    
    Args:
        part: Part value
        whole: Whole value
        
    Returns:
        float: Percentage
    """
    if whole == 0:
        return 0.0

    return (part / whole) * 100


def round_to_nearest(value: float, nearest: float = 0.01) -> float:
    """
    Round value to nearest increment.
    
    Args:
        value: Value to round
        nearest: Nearest increment
        
    Returns:
        float: Rounded value
    """
    return round(value / nearest) * nearest


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: Filename
        
    Returns:
        str: File extension (including dot)
    """
    return filename.split('.')[-1] if '.' in filename else ''


def batch_process(items: List[Any], batch_size: int = 10) -> List[List[Any]]:
    """
    Split items into batches.
    
    Args:
        items: Items to batch
        batch_size: Size of each batch
        
    Returns:
        List[List[Any]]: Batched items
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def retry_on_failure(max_attempts: int = 3, delay_seconds: float = 1.0):
    """
    Decorator for retrying function calls on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay_seconds: Delay between attempts
        
    Returns:
        Decorator function
    """
    def decorator(func):
        import asyncio
        import functools

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay_seconds)
                    else:
                        raise last_exception

            raise last_exception

        return wrapper
    return decorator
