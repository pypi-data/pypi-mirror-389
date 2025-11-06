"""
File manager for WebClone Backend
"""
import shutil
import uuid
from typing import Optional, BinaryIO
from pathlib import Path

class FileManager:
    """File management system"""
    
    def __init__(self, upload_dir: str = "uploads"):
        """Initialize file manager"""
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    def save_file(
        self,
        file: BinaryIO,
        filename: Optional[str] = None
    ) -> str:
        """Save a file"""
        if not filename:
            filename = f"{uuid.uuid4()}{Path(file.name).suffix}"
        
        filepath = self.upload_dir / filename
        
        # Reset file pointer to beginning
        file.seek(0)
        
        with open(filepath, 'wb') as f:
            shutil.copyfileobj(file, f)
        
        return str(filepath)
    
    def delete_file(self, filepath: str) -> bool:
        """Delete a file"""
        try:
            Path(filepath).unlink()
            return True
        except FileNotFoundError:
            return False
    
    def get_file_url(self, filepath: str) -> str:
        """Get file URL"""
        return f"/files/{Path(filepath).name}"