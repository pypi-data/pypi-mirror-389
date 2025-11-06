"""
Image processor for WebClone Backend
"""
from PIL import Image
from typing import Tuple, Optional
from pathlib import Path

class ImageProcessor:
    """Image processing system"""
    
    def resize_image(
        self,
        image_path: str,
        size: Tuple[int, int],
        output_path: Optional[str] = None
    ) -> str:
        """Resize an image"""
        img = Image.open(image_path)
        img = img.resize(size)
        
        if not output_path:
            output_path = str(Path(image_path).with_suffix('.resized.jpg'))
        
        img.save(output_path)
        return output_path
    
    def crop_image(
        self,
        image_path: str,
        box: Tuple[int, int, int, int],
        output_path: Optional[str] = None
    ) -> str:
        """Crop an image"""
        img = Image.open(image_path)
        img = img.crop(box)
        
        if not output_path:
            output_path = str(Path(image_path).with_suffix('.cropped.jpg'))
        
        img.save(output_path)
        return output_path
    
    def create_thumbnail(
        self,
        image_path: str,
        size: Tuple[int, int] = (128, 128)
    ) -> str:
        """Create a thumbnail"""
        img = Image.open(image_path)
        img.thumbnail(size)
        
        output_path = str(Path(image_path).with_suffix('.thumb.jpg'))
        img.save(output_path)
        return output_path