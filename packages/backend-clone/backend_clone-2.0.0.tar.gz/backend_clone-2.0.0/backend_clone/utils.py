"""
Utilities for backend-clone v2.0.0 Revolutionary
"""
import re
import logging
from typing import Dict, Any
from dataclasses import dataclass

# Set up logger
logger = logging.getLogger("backend-clone")
logger.setLevel(logging.INFO)

# Create console handler
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@dataclass
class DependencyCheckResult:
    """Result of dependency check"""
    success: bool
    error: str = ""


def validate_project_name(name: str) -> bool:
    """
    Validate project name
    
    Args:
        name: Project name to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Check if name is not empty
    if not name:
        return False
    
    # Check if name contains only valid characters
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False
    
    # Check length
    if len(name) > 50:
        return False
    
    return True


def check_dependencies() -> DependencyCheckResult:
    """
    Check if all required dependencies are installed
    
    Returns:
        Dependency check result
    """
    # In a real implementation, this would check actual dependencies
    return DependencyCheckResult(success=True)


def estimate_cost(config: Dict[str, Any]) -> float:
    """
    Estimate project cost based on configuration
    
    Args:
        config: Project configuration
        
    Returns:
        Estimated monthly cost in USD
    """
    # Simple cost estimation logic
    base_cost = 50.0  # Base cost
    
    # Scale factor
    scale_costs = {
        'small': 1.0,
        'medium': 2.0,
        'large': 5.0,
        'xlarge': 10.0,
        'massive': 20.0
    }
    
    scale_factor = scale_costs.get(config.get('scale', 'small'), 1.0)
    
    # Feature factors
    feature_cost = 0.0
    if config.get('ai_features'):
        feature_cost += 100.0
    if config.get('cloud_features'):
        feature_cost += 50.0
    if config.get('security_level') == 'maximum':
        feature_cost += 75.0
    
    return base_cost * scale_factor + feature_cost


def analyze_requirements(project_type: str, scale: str) -> str:
    """
    Analyze requirements and recommend framework
    
    Args:
        project_type: Type of project
        scale: Expected scale
        
    Returns:
        Recommended framework
    """
    # Simple recommendation logic
    recommendations = {
        ('startup', 'small'): 'fastapi',
        ('startup', 'medium'): 'fastapi',
        ('enterprise', 'large'): 'django',
        ('enterprise', 'xlarge'): 'microservices',
        ('mobile', 'small'): 'flask',
        ('ecommerce', 'medium'): 'django',
        ('realtime', 'large'): 'tornado',
        ('ai_service', 'medium'): 'fastapi',
    }
    
    key = (project_type, scale)
    return recommendations.get(key, 'fastapi')