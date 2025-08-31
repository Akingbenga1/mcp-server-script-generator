"""
PyPDF2-based PDF Text Extractor
"""

import PyPDF2
from typing import List, Dict, Any
from .base_extractor import BasePDFExtractor

class PyPDFExtractor(BasePDFExtractor):
    """PyPDF2-based PDF text extractor"""
    
    async def extract_text(self, pdf_path: str) -> str:
        """Extract text content from PDF file using PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"PyPDF2 extraction failed: {str(e)}")
    
    async def extract_pages(self, pdf_path: str) -> List[str]:
        """Extract text from individual pages using PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                pages = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    pages.append(page_text if page_text else "")
            return pages
        except Exception as e:
            raise Exception(f"PyPDF2 page extraction failed: {str(e)}")
    
    async def extract_metadata(self, pdf_path: str) -> dict:
        """Extract PDF metadata using PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata = reader.metadata
                return {
                    'title': metadata.get('/Title', ''),
                    'author': metadata.get('/Author', ''),
                    'subject': metadata.get('/Subject', ''),
                    'creator': metadata.get('/Creator', ''),
                    'producer': metadata.get('/Producer', ''),
                    'pages': len(reader.pages)
                }
        except Exception as e:
            raise Exception(f"PyPDF2 metadata extraction failed: {str(e)}")
