"""
Database module for WebClone Backend
"""
from .connection import Database
from .models import BaseModel

__all__ = ['Database', 'BaseModel']