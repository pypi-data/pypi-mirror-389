"""
Password management for WebClone Backend
"""
import bcrypt
from typing import Union

class PasswordManager:
    """Password manager"""
    
    @staticmethod
    def hash_password(password: Union[str, bytes]) -> str:
        """Hash a password"""
        if isinstance(password, str):
            password = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: Union[str, bytes], hashed: Union[str, bytes]) -> bool:
        """Verify a password against its hash"""
        if isinstance(password, str):
            password = password.encode('utf-8')
        if isinstance(hashed, str):
            hashed = hashed.encode('utf-8')
        return bcrypt.checkpw(password, hashed)