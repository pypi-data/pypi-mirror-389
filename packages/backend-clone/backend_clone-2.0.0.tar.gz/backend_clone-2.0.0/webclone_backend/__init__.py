"""
WebClone Backend - Professional Python Backend Framework
Version: 1.20.00
Author: [Your Name]
"""

from .core.app import WebCloneBackend
from .database import Database, BaseModel
from .auth import Auth, require_login, require_role
from .storage import FileManager, ImageProcessor
from .api import route, middleware

__version__ = '1.20.00'
__all__ = [
    'WebCloneBackend',
    'Database',
    'BaseModel',
    'Auth',
    'require_login',
    'require_role',
    'FileManager',
    'ImageProcessor',
    'route',
    'middleware'
]