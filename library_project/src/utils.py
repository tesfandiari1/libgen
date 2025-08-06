"""Shared utilities for LibGen downloader."""

import re
import os
import unicodedata
from typing import Optional

# Fixed [CRITICAL-003]: Add proper filename sanitization
def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename to prevent security issues.
    
    Args:
        filename: The filename to sanitize
        max_length: Maximum length for the filename
        
    Returns:
        Sanitized filename safe for filesystem use
    """
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    
    # Remove any path separators and null bytes
    filename = filename.replace('/', '').replace('\\', '').replace('\0', '')
    
    # Remove/replace problematic characters
    filename = re.sub(r'[<>:"|?*]', '', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure not empty
    if not filename:
        filename = 'unnamed'
    
    # Handle extension separately to preserve it
    name_parts = filename.rsplit('.', 1)
    if len(name_parts) == 2:
        name, ext = name_parts
        # Truncate name if needed, preserving extension
        if len(filename) > max_length:
            max_name_length = max_length - len(ext) - 1
            if max_name_length > 0:
                filename = f"{name[:max_name_length]}.{ext}"
            else:
                filename = filename[:max_length]
    else:
        # No extension, just truncate
        if len(filename) > max_length:
            filename = filename[:max_length]
    
    return filename


def generate_safe_filename(title: str, author: str, extension: str) -> str:
    """Generate a safe filename from paper metadata.
    
    Args:
        title: Paper title
        author: Paper author(s)
        extension: File extension
        
    Returns:
        Safe filename for the paper
    """
    # Sanitize individual components
    safe_title = sanitize_filename(title, max_length=100)
    safe_author = sanitize_filename(author, max_length=50)
    
    # Remove extension from title if it accidentally got included
    if safe_title.endswith(f".{extension}"):
        safe_title = safe_title[:-len(extension)-1]
    
    # Combine and sanitize final filename
    filename = f"{safe_author} - {safe_title}.{extension}"
    return sanitize_filename(filename, max_length=255)