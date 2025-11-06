"""
Authentication module for WebClone Backend
"""
from .jwt_handler import Auth, require_login, require_role

__all__ = ['Auth', 'require_login', 'require_role']