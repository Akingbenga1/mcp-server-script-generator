"""
Base File Validator Interface
Following Single Responsibility Principle (SRP)
"""

from abc import ABC, abstractmethod
from typing import Tuple

class BaseFileValidator(ABC):
    """Abstract base class for file validation"""
    
    @abstractmethod
    async def validate(self, file_path: str) -> Tuple[bool, str]:
        """Validate file and return (is_valid, error_message)"""
        pass
    
    @abstractmethod
    async def validate_file_size(self, file_path: str, max_size_mb: int = 50) -> Tuple[bool, str]:
        """Validate file size"""
        pass
    
    @abstractmethod
    async def validate_file_type(self, file_path: str) -> Tuple[bool, str]:
        """Validate file type"""
        pass
