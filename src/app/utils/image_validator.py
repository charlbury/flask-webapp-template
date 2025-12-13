"""
Image validation and processing utilities.
"""

import os
import io
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage
from flask import current_app
from PIL import Image


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

