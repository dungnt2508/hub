"""
Unicode Normalizer - Xử lý chuẩn hóa Unicode cho tiếng Việt

Vấn đề: Khi người dùng nhập từ bàn phím hoặc copy từ nơi khác, ký tự tiếng Việt
có thể ở dạng chuẩn hóa khác nhau (NFC vs NFD), dẫn đến không tìm thấy kết quả.

Giải pháp: Normalize tất cả text thành NFC (Composed form) để đảm bảo consistency
"""
import unicodedata
from typing import Optional


def normalize_unicode(text: Optional[str], form: str = 'NFC') -> Optional[str]:
    """
    Chuẩn hóa Unicode text thành form được chỉ định
    
    Args:
        text: Text cần normalize
        form: Dạng chuẩn hóa - 'NFC' (composed, mặc định), 'NFD' (decomposed), etc.
        
    Returns:
        Text đã normalize, hoặc None nếu input là None
    """
    if text is None:
        return None
    
    if not isinstance(text, str):
        return text
    
    try:
        # Normalize text thành NFC (Composed form - ký tự duy nhất)
        return unicodedata.normalize(form, text)
    except Exception:
        # Nếu có lỗi, trả về text gốc
        return text


def normalize_query(query: Optional[str]) -> Optional[str]:
    """
    Normalize query string thành NFC form
    Đây là hàm shorthand cho normalize_unicode(text, 'NFC')
    
    Args:
        query: Query string
        
    Returns:
        Query đã normalize
    """
    return normalize_unicode(query, form='NFC')


def compare_normalized(text1: Optional[str], text2: Optional[str]) -> bool:
    """
    So sánh hai text sau khi normalize
    
    Args:
        text1: Text thứ nhất
        text2: Text thứ hai
        
    Returns:
        True nếu hai text giống nhau sau normalize, False nếu khác
    """
    norm1 = normalize_unicode(text1)
    norm2 = normalize_unicode(text2)
    return norm1 == norm2


def normalize_filter_value(value: Optional[str]) -> Optional[str]:
    """
    Normalize filter value cho database query
    
    Args:
        value: Filter value (có thể None)
        
    Returns:
        Normalized value hoặc None
    """
    if value is None:
        return None
    
    if not isinstance(value, str):
        return str(value)
    
    # Normalize Unicode + strip whitespace
    normalized = normalize_unicode(value.strip())
    return normalized


def normalize_and_escape_sql(value: str, null_if_empty: bool = False) -> str:
    """
    Normalize Unicode và escape cho SQL query
    
    Args:
        value: Value cần normalize và escape
        null_if_empty: Trả về "NULL" nếu empty string
        
    Returns:
        Normalized + escaped value, hoặc "NULL" nếu null_if_empty=True và value empty
    """
    if value is None or (null_if_empty and not value.strip()):
        return "NULL"
    
    if not isinstance(value, str):
        value = str(value)
    
    # Normalize Unicode
    normalized = normalize_unicode(value)
    if normalized is None:
        return "NULL" if null_if_empty else "''"
    
    # Escape single quotes cho SQL
    escaped = normalized.replace("'", "''")
    return escaped
