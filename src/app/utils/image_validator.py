"""
Image validation and processing utilities.
"""

import os
import io
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage
from flask import current_app
from PIL import Image, ImageDraw, ImageFont


ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/webp'
}


def validate_image_file(file: FileStorage, max_size: int = 2097152) -> Tuple[bool, Optional[str]]:
    """
    Validate image file.

    Args:
        file: FileStorage object from Flask request
        max_size: Maximum file size in bytes (default: 2MB)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file provided"

    # Check file extension
    filename = file.filename.lower()
    extension = filename.rsplit('.', 1)[-1] if '.' in filename else None

    if not extension or extension not in ALLOWED_EXTENSIONS:
        allowed = ', '.join(ALLOWED_EXTENSIONS)
        return False, f"Invalid file type. Allowed types: {allowed}"

    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        return False, f"Invalid MIME type: {file.content_type}"

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer

    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        return False, f"File size exceeds maximum of {max_size_mb}MB"

    if file_size == 0:
        return False, "File is empty"

    return True, None


def get_file_extension(filename: str) -> Optional[str]:
    """
    Get file extension from filename.

    Args:
        filename: Name of the file

    Returns:
        Extension without dot, or None
    """
    if '.' not in filename:
        return None
    return filename.rsplit('.', 1)[-1].lower()


def crop_to_square(image_data: bytes, content_type: str) -> Tuple[bytes, str]:
    """
    Crop image to largest possible square (center crop).

    Args:
        image_data: Binary image data
        content_type: MIME type of the image

    Returns:
        Tuple of (cropped_image_data, content_type)
    """
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_data))

        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        width, height = image.size

        # If already square, return as-is
        if width == height:
            output = io.BytesIO()
            # Determine format from content type
            format_map = {
                'image/jpeg': 'JPEG',
                'image/jpg': 'JPEG',
                'image/png': 'PNG',
                'image/gif': 'GIF',
                'image/webp': 'WEBP'
            }
            save_format = format_map.get(content_type, 'JPEG')
            image.save(output, format=save_format, quality=95)
            return output.getvalue(), content_type

        # Calculate square crop (center crop)
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size

        # Crop to square
        cropped_image = image.crop((left, top, right, bottom))

        # Save to bytes
        output = io.BytesIO()
        # Determine format from content type
        format_map = {
            'image/jpeg': 'JPEG',
            'image/jpg': 'JPEG',
            'image/png': 'PNG',
            'image/gif': 'GIF',
            'image/webp': 'WEBP'
        }
        save_format = format_map.get(content_type, 'JPEG')

        # For JPEG, use quality setting; for others, use default
        if save_format == 'JPEG':
            cropped_image.save(output, format=save_format, quality=95)
        else:
            cropped_image.save(output, format=save_format)

        return output.getvalue(), content_type

    except Exception as e:
        current_app.logger.error(f"Error cropping image to square: {e}")
        # If cropping fails, return original image
        return image_data, content_type


def generate_initial_avatar(username: Optional[str] = None, first_name: Optional[str] = None, last_name: Optional[str] = None, size: int = 400) -> Tuple[bytes, str]:
    """
    Generate a grey avatar image with the first letter of username, first_name, or last_name.
    
    Priority: username > first_name > last_name
    
    Args:
        username: User's username (optional)
        first_name: User's first name (optional)
        last_name: User's last name (optional)
        size: Size of the square avatar in pixels (default: 400)
    
    Returns:
        Tuple of (image_data_bytes, content_type)
    """
    # Determine which letter to use (priority: username > first_name > last_name)
    letter = None
    if username and username.strip():
        letter = username.strip()[0].upper()
    elif first_name and first_name.strip():
        letter = first_name.strip()[0].upper()
    elif last_name and last_name.strip():
        letter = last_name.strip()[0].upper()
    else:
        # Fallback to '?' if no name available
        letter = '?'
    
    # Create a grey square image
    # Using a medium grey color (RGB: 128, 128, 128)
    grey_color = (128, 128, 128)
    image = Image.new('RGB', (size, size), grey_color)
    
    # Create drawing context
    draw = ImageDraw.Draw(image)
    
    # Try to use a nice font, fallback to default if not available
    font_size = int(size * 0.5)  # Font size is 50% of image size
    font = None
    
    # Try to load system fonts in order of preference
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "/System/Library/Fonts/Arial.ttf",  # macOS alternative
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Linux alternative
        "C:/Windows/Fonts/arial.ttf",  # Windows
    ]
    
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except (OSError, IOError):
            continue
    
    # Fallback to default font if no system font found
    if font is None:
        try:
            font = ImageFont.load_default()
        except Exception:
            # Last resort: create a basic font
            font = None
    
    # Calculate text position (centered)
    # Get text bounding box to center it properly
    white_color = (255, 255, 255)
    
    if font:
        try:
            # Try new PIL API (Pillow 8.0+)
            bbox = draw.textbbox((0, 0), letter, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except (AttributeError, TypeError):
            # Older PIL versions use textsize instead of textbbox
            try:
                text_width, text_height = draw.textsize(letter, font=font)
            except Exception:
                # Fallback: estimate size
                text_width = size * 0.3
                text_height = size * 0.5
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        # Draw white letter on grey background
        draw.text((x, y), letter, fill=white_color, font=font)
    else:
        # No font available, use simple centered text
        # Estimate position for default rendering
        x = size // 2 - size // 10
        y = size // 2 - size // 10
        draw.text((x, y), letter, fill=white_color)
    
    # Convert to bytes
    output = io.BytesIO()
    image.save(output, format='PNG', quality=95)
    image_data = output.getvalue()
    
    return image_data, 'image/png'

