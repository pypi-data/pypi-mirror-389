"""
Main Application class for WebClone Backend
"""
from typing import Any, Dict, List, Callable
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

class WebCloneBackend:
    """Main application class"""
    
    def __init__(self, **kwargs):
        """Initialize the WebClone backend application"""
        self.app = FastAPI(**kwargs)
        self._components: Dict[str, Any] = {}
        
        # Default CORS configuration
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
    
    def register_component(self, name: str, component: Any):
        """Register a component with the application"""
        self._components[name] = component
    
    def get_component(self, name: str) -> Any:
        """Get a registered component by name"""
        return self._components.get(name)
    
    def run(
        self,
        host: str = '0.0.0.0',
        port: int = 8000,
        **kwargs
    ):
        """Run the application server"""
        import uvicorn
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            **kwargs
        )