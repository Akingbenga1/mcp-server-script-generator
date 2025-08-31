"""
Base PDF Extractor Interface
Following Single Responsibility Principle (SRP)
"""

from abc import ABC, abstractmethod
from typing import List, Optional

class BasePDFExtractor(ABC):
    """Abstract base class for PDF text extraction"""
    
    @abstractmethod
    async def extract_text(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        pass
    
    @abstractmethod
    async def extract_pages(self, pdf_path: str) -> List[str]:
        """Extract text from individual pages"""
        pass
    
    @abstractmethod
    async def extract_metadata(self, pdf_path: str) -> dict:
        """Extract PDF metadata (title, author, etc.)"""
        pass
