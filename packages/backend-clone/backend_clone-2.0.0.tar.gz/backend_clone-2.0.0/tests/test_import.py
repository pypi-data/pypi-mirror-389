"""
Basic import tests for WebClone Backend
"""
import sys
import os

# Add the webclone_backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that we can import the main components"""
    try:
        from webclone_backend import WebCloneBackend, Database, BaseModel
        from webclone_backend.auth import Auth
        from webclone_backend.storage import FileManager, ImageProcessor
        assert True  # If we get here, imports worked
    except ImportError as e:
        assert False, f"Import failed: {e}"

def test_version():
    """Test that we can access the version"""
    try:
        from webclone_backend import __version__
        assert isinstance(__version__, str)
        assert len(__version__) > 0
    except Exception as e:
        assert False, f"Version test failed: {e}"

if __name__ == "__main__":
    test_imports()
    test_version()
    print("All tests passed!")