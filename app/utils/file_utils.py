"""
File validation and utility functions.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple
from app.core.config import settings
import logging

# Try to import magic, but provide fallback if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logging.warning("python-magic not available, using extension-based file type detection")

logger = logging.getLogger(__name__)


class FileValidationResult:
    """Result of file validation."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []


class FileValidator:
    """Handles file validation for document uploads."""
    
    def __init__(self):
        self.max_file_size = settings.max_file_size
        self.supported_mime_types = settings.supported_mime_types_list
    
    def validate_file(self, filename: str, content: bytes) -> FileValidationResult:
        """
        Comprehensive file validation.
        
        Args:
            filename: Original filename
            content: File content as bytes
            
        Returns:
            FileValidationResult with validation status and errors
        """
        errors = []
        
        # Check file size
        if len(content) > self.max_file_size:
            size_mb = len(content) / (1024 * 1024)
            max_mb = self.max_file_size / (1024 * 1024)
            errors.append(f"File too large: {size_mb:.1f}MB (max: {max_mb}MB)")
        
        # Check MIME type using python-magic for accuracy (if available)
        if MAGIC_AVAILABLE:
            try:
                detected_mime = magic.from_buffer(content, mime=True)
                if detected_mime not in self.supported_mime_types:
                    errors.append(f"Unsupported file type: {detected_mime}")
            except Exception as e:
                logger.warning(f"MIME type detection failed: {e}")
                # Fallback to file extension checking
                if not self._validate_file_extension(filename):
                    errors.append(f"Unsupported file extension")
        else:
            # Use extension-based validation when magic is not available
            if not self._validate_file_extension(filename):
                errors.append(f"Unsupported file extension")
        
        # Check for empty files
        if len(content) == 0:
            errors.append("File is empty")
        
        # Check filename
        if not self._validate_filename(filename):
            errors.append("Invalid filename")
        
        return FileValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    def _validate_file_extension(self, filename: str) -> bool:
        """Validate file extension as fallback."""
        valid_extensions = {'.pdf', '.txt', '.md', '.docx'}
        extension = Path(filename).suffix.lower()
        return extension in valid_extensions
    
    def _validate_filename(self, filename: str) -> bool:
        """Validate filename for security."""
        if not filename or len(filename) > 255:
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        return not any(char in filename for char in dangerous_chars)


def calculate_content_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content for deduplication."""
    return hashlib.sha256(content).hexdigest()


def generate_safe_filename(original_filename: str, document_id: str) -> str:
    """Generate a safe filename for storage."""
    # Get file extension
    extension = Path(original_filename).suffix
    
    # Create safe filename with document ID
    safe_name = f"doc_{document_id}{extension}"
    
    return safe_name


def estimate_page_count(text: str) -> int:
    """Estimate page count based on text length."""
    # Rough estimate: 500 words per page
    words = len(text.split())
    return max(1, words // 500)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_mime_type_from_extension(filename: str) -> str:
    """Get expected MIME type from file extension."""
    extension_map = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    extension = Path(filename).suffix.lower()
    return extension_map.get(extension, 'application/octet-stream')