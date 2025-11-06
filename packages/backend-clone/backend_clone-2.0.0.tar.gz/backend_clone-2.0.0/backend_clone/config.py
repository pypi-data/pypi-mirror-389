"""
Configuration module for backend-clone v2.0.0 Revolutionary
"""
import os
from typing import Any, Dict
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application settings"""
    # General settings
    debug: bool = field(default_factory=lambda: os.getenv('DEBUG', 'False').lower() == 'true')
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    
    # AI settings
    openai_api_key: str = field(default_factory=lambda: os.getenv('OPENAI_API_KEY', ''))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv('ANTHROPIC_API_KEY', ''))
    google_api_key: str = field(default_factory=lambda: os.getenv('GOOGLE_API_KEY', ''))
    cohere_api_key: str = field(default_factory=lambda: os.getenv('COHERE_API_KEY', ''))
    
    # Cloud settings
    aws_access_key_id: str = field(default_factory=lambda: os.getenv('AWS_ACCESS_KEY_ID', ''))
    aws_secret_access_key: str = field(default_factory=lambda: os.getenv('AWS_SECRET_ACCESS_KEY', ''))
    gcp_credentials: str = field(default_factory=lambda: os.getenv('GCP_CREDENTIALS', ''))
    azure_subscription_id: str = field(default_factory=lambda: os.getenv('AZURE_SUBSCRIPTION_ID', ''))
    
    # Database settings
    postgres_url: str = field(default_factory=lambda: os.getenv('POSTGRES_URL', ''))
    mongo_url: str = field(default_factory=lambda: os.getenv('MONGO_URL', ''))
    redis_url: str = field(default_factory=lambda: os.getenv('REDIS_URL', ''))
    
    # Security settings
    secret_key: str = field(default_factory=lambda: os.getenv('SECRET_KEY', ''))
    jwt_secret: str = field(default_factory=lambda: os.getenv('JWT_SECRET', ''))


# Global settings instance
settings = Settings()