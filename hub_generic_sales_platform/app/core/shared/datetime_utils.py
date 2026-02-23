"""
Utility functions cho datetime và timezone-aware
Hỗ trợ cả UTC và UTC+7 (Asia/Ho_Chi_Minh)
"""
from datetime import datetime, timezone, timedelta


def utc_now() -> datetime:
    """
    Lấy local datetime hiện tại với timezone UTC+7 (Asia/Ho_Chi_Minh)
    
    DEPRECATED: Use local_now() instead for UTC+7 timezone
    
    Returns:
        datetime object với UTC+7 timezone
        
    Example:
        >>> now = utc_now()
        >>> now.tzinfo.utcoffset(now).total_seconds() / 3600
        7.0
    """
    # Trả về local time UTC+7 thay vì UTC
    return local_now()


def to_utc(dt: datetime) -> datetime:
    """
    Convert datetime sang UTC timezone-aware
    
    Nếu datetime đã có timezone, convert sang UTC
    Nếu datetime là naive (không có timezone), giả định là UTC
    
    Args:
        dt: datetime object (có thể là naive hoặc timezone-aware)
        
    Returns:
        datetime object với UTC timezone
    """
    if dt.tzinfo is None:
        # Nếu là naive datetime, giả định là UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Nếu đã có timezone, convert sang UTC
        return dt.astimezone(timezone.utc)


def local_now() -> datetime:
    """
    Lấy local datetime hiện tại với timezone UTC+7 (Asia/Ho_Chi_Minh)
    
    Returns:
        datetime object với UTC+7 timezone
        
    Example:
        >>> now = local_now()
        >>> now.tzinfo.utcoffset(now).total_seconds() / 3600
        7.0
    """
    # UTC+7 timezone
    utc_plus_7 = timezone(timedelta(hours=7))
    return datetime.now(utc_plus_7)
