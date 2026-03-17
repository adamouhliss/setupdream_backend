import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import aiofiles
import io

from ..core.config import settings


class ImageService:
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    MAX_IMAGE_SIZE = (1200, 1200)  # Max width, height
    THUMBNAIL_SIZE = (300, 300)

    @classmethod
    async def save_product_image(cls, file: UploadFile) -> str:
        """Save uploaded product image and return the URL"""
        
        # Validate file
        cls._validate_image_file(file)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, "products", unique_filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save and process image
        await cls._save_and_process_image(file, file_path)
        
        # Return URL path
        return f"/uploads/products/{unique_filename}"

    @classmethod
    async def save_store_logo(cls, file: UploadFile) -> str:
        """Save uploaded store logo and return the URL"""
        
        # Validate file
        cls._validate_image_file(file)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"logo_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, "logos", unique_filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save and process logo with specific sizing
        await cls._save_and_process_logo(file, file_path)
        
        # Return URL path
        return f"/uploads/logos/{unique_filename}"

    @classmethod
    async def _save_and_process_logo(cls, file: UploadFile, file_path: str) -> None:
        """Save and process the uploaded logo with logo-specific settings"""
        
        # Read file content
        content = await file.read()
        
        # Validate file size after reading
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        try:
            # Open and process image with Pillow
            image = Image.open(io.BytesIO(content))
            
            # For logos, preserve transparency if it exists (PNG)
            if image.mode == 'RGBA':
                # Keep RGBA for PNG logos with transparency
                pass
            elif image.mode in ('LA', 'P'):
                image = image.convert('RGBA')
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Logo-specific sizing - max 400x200 for headers
            LOGO_MAX_SIZE = (400, 200)
            if image.size[0] > LOGO_MAX_SIZE[0] or image.size[1] > LOGO_MAX_SIZE[1]:
                image.thumbnail(LOGO_MAX_SIZE, Image.Resampling.LANCZOS)
            
            # Save with appropriate format
            if image.mode == 'RGBA' and file_path.lower().endswith('.png'):
                # Save as PNG to preserve transparency
                image.save(file_path, 'PNG', optimize=True)
            else:
                # Convert to RGB and save as JPEG
                if image.mode == 'RGBA':
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                image.save(file_path, 'JPEG', quality=90, optimize=True)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

    @classmethod
    def delete_logo(cls, logo_url: str) -> bool:
        """Delete a logo file"""
        try:
            # Extract filename from URL
            if logo_url.startswith('/uploads/logos/'):
                file_path = os.path.join(settings.UPLOAD_DIR, "logos", logo_url[15:])  # Remove '/uploads/logos/'
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
            return False
        except Exception:
            return False

    @classmethod
    async def generate_favicon_from_logo(cls, logo_path: str) -> str:
        """Generate a favicon-optimized version of the logo"""
        try:
            # Open the original logo
            full_path = os.path.join(settings.UPLOAD_DIR, logo_path.lstrip('/uploads/'))
            if not os.path.exists(full_path):
                return logo_path  # Return original if file doesn't exist
            
            image = Image.open(full_path)
            
            # Create favicon sizes (32x32 is standard favicon size)
            favicon_size = (32, 32)
            
            # Create a square canvas with transparent background
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Calculate dimensions to maintain aspect ratio
            img_width, img_height = image.size
            if img_width != img_height:
                # Make it square by centering on transparent background
                max_dim = max(img_width, img_height)
                square_img = Image.new('RGBA', (max_dim, max_dim), (0, 0, 0, 0))
                
                # Center the image
                x = (max_dim - img_width) // 2
                y = (max_dim - img_height) // 2
                square_img.paste(image, (x, y), image if image.mode == 'RGBA' else None)
                image = square_img
            
            # Resize to favicon size with high quality
            image = image.resize(favicon_size, Image.Resampling.LANCZOS)
            
            # Generate favicon filename
            base_name = os.path.splitext(os.path.basename(full_path))[0]
            favicon_filename = f"{base_name}_favicon.png"
            favicon_path = os.path.join(settings.UPLOAD_DIR, "logos", favicon_filename)
            
            # Save as PNG with transparency support
            image.save(favicon_path, 'PNG', optimize=True)
            
            return f"/uploads/logos/{favicon_filename}"
            
        except Exception as e:
            print(f"Favicon generation error: {e}")
            return logo_path  # Return original logo path if favicon generation fails

    @classmethod
    def _validate_image_file(cls, file: UploadFile) -> None:
        """Validate uploaded image file"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(cls.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size (file.size might not be available in all cases)
        if hasattr(file, 'size') and file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )

    @classmethod
    async def _save_and_process_image(cls, file: UploadFile, file_path: str) -> None:
        """Save and process the uploaded image"""
        
        # Read file content
        content = await file.read()
        
        # Validate file size after reading
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        try:
            # Open and process image with Pillow
            image = Image.open(io.BytesIO(content))
            
            # Convert to RGB if necessary (for PNG with transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            if image.size[0] > cls.MAX_IMAGE_SIZE[0] or image.size[1] > cls.MAX_IMAGE_SIZE[1]:
                image.thumbnail(cls.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Save optimized image
            image.save(file_path, 'JPEG', quality=85, optimize=True)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

    @classmethod
    def delete_image(cls, image_url: str) -> bool:
        """Delete an image file"""
        try:
            # Extract filename from URL
            if image_url.startswith('/uploads/'):
                file_path = os.path.join(settings.UPLOAD_DIR, image_url[9:])  # Remove '/uploads/'
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
            return False
        except Exception:
            return False

image_service = ImageService() 