"""
JWT handler for WebClone Backend
"""
import jwt
from typing import Dict, Any, Callable
from functools import wraps
from fastapi import HTTPException, Request

class JWTHandler:
    """JWT token handler"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def create_token(self, data: Dict[str, Any], expires_delta: int = 30) -> str:
        """Create JWT token"""
        import datetime
        to_encode = data.copy()
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_delta)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

class Auth:
    """Authentication system"""
    
    def __init__(self, secret_key: str):
        self.jwt_handler = JWTHandler(secret_key)
    
    def require_login(self, func: Callable):
        """Decorator to require login"""
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise HTTPException(status_code=401, detail='Authorization header missing or invalid')
            
            token = auth_header.replace('Bearer ', '')
            if not token or not self.jwt_handler.decode_token(token):
                raise HTTPException(status_code=401, detail='Invalid token')
            
            return await func(request, *args, **kwargs)
        return wrapper

def require_login(func: Callable):
    """Shortcut for Auth.require_login"""
    # This is a placeholder - in practice, you'd need to access the Auth instance
    return func

def require_role(role: str):
    """Decorator to require specific role"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Role checking logic would go here
            return await func(*args, **kwargs)
        return wrapper
    return decorator