"""
Cache system for WebClone Backend
"""
from typing import Any, Optional
from datetime import datetime, timedelta
import json

class Cache:
    """Simple in-memory cache system"""
    
    def __init__(self):
        """Initialize cache"""
        self._cache = {}
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set a value in cache with TTL (time to live) in seconds"""
        expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        if key not in self._cache:
            return None
        
        item = self._cache[key]
        
        if item['expires_at'] and datetime.now() > item['expires_at']:
            del self._cache[key]
            return None
        
        return item['value']
    
    def delete(self, key: str):
        """Delete a value from cache"""
        self._cache.pop(key, None)
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()