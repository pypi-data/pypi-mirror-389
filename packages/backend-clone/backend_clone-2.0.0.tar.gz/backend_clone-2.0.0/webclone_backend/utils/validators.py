"""
Validators for WebClone Backend
"""
import re
from typing import Union

class Validators:
    """Data validators"""
    
    @staticmethod
    def is_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_phone(phone: str) -> bool:
        """Validate phone number format"""
        pattern = r'^\+?1?\d{9,15}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def is_url(url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://[^\s]+$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def min_length(value: Union[str, list], length: int) -> bool:
        """Check minimum length"""
        return len(value) >= length
    
    @staticmethod
    def max_length(value: Union[str, list], length: int) -> bool:
        """Check maximum length"""
        return len(value) <= length