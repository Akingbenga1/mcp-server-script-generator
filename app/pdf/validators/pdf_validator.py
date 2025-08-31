"""
PDF File Validator
"""

import os
import magic
from typing import Tuple
from .base_validator import BaseFileValidator

class PDFValidator(BaseFileValidator):
    """PDF file validator"""
    
    async def validate(self, file_path: str) -> Tuple[bool, str]:
        """Validate PDF file"""
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Check file type
        is_valid_type, type_error = await self.validate_file_type(file_path)
        if not is_valid_type:
            return False, type_error
        
        # Check file size
        is_valid_size, size_error = await self.validate_file_size(file_path)
        if not is_valid_size:
            return False, size_error
        
        return True, "File is valid"
    
    async def validate_file_size(self, file_path: str, max_size_mb: int = 50) -> Tuple[bool, str]:
        """Validate file size"""
        try:
            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                return False, f"File size exceeds {max_size_mb}MB limit"
            
            return True, "File size is valid"
        except Exception as e:
            return False, f"Error checking file size: {str(e)}"
    
    async def validate_file_type(self, file_path: str) -> Tuple[bool, str]:
        """Validate file type"""
        try:
            # Check file extension
            if not file_path.lower().endswith('.pdf'):
                return False, "File is not a PDF"
            
            # Check MIME type
            mime_type = magic.from_file(file_path, mime=True)
            if mime_type != 'application/pdf':
                return False, "File is not a valid PDF"
            
            return True, "File type is valid"
        except Exception as e:
            return False, f"Error checking file type: {str(e)}"
