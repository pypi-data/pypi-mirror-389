"""
Tests for the backend-clone package
"""
import sys
import os
import pytest

# Add the backend_clone directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that we can import the main components"""
    try:
        from backend_clone import Generator
        from backend_clone import __version__
        assert True  # If we get here, imports worked
    except ImportError as e:
        assert False, f"Import failed: {e}"

def test_version():
    """Test that we can access the version"""
    try:
        from backend_clone import __version__
        assert isinstance(__version__, str)
        assert len(__version__) > 0
    except Exception as e:
        assert False, f"Version test failed: {e}"

def test_generator_creation():
    """Test that we can create a Generator instance"""
    try:
        from backend_clone.generator import Generator
        generator = Generator("test-project")
        assert generator.project_name == "test-project"
        assert generator.framework == "fastapi"  # default
    except Exception as e:
        assert False, f"Generator creation failed: {e}"

if __name__ == "__main__":
    test_imports()
    test_version()
    test_generator_creation()
    print("All tests passed!")