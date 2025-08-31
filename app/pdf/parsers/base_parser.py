"""
Base API Parser Interface
Following Single Responsibility Principle (SRP)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models import APIEndpoint

class BaseAPIParser(ABC):
    """Abstract base class for API endpoint parsing"""
    
    @abstractmethod
    async def parse_endpoints(self, text: str) -> List[APIEndpoint]:
        """Parse API endpoints from text content"""
        pass
    
    @abstractmethod
    async def parse_schema(self, text: str) -> Dict[str, Any]:
        """Parse API schema from text content"""
        pass
    
    @abstractmethod
    async def parse_authentication(self, text: str) -> Dict[str, Any]:
        """Parse authentication information from text content"""
        pass
