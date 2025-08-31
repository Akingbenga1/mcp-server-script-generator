"""
PDFPlumber-based PDF Text Extractor
"""

import pdfplumber
from typing import List, Dict, Any
from .base_extractor import BasePDFExtractor

class PDFPlumberExtractor(BasePDFExtractor):
    """PDFPlumber-based PDF text extractor"""
    
    async def extract_text(self, pdf_path: str) -> str:
        """Extract text content from PDF file using PDFPlumber"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"PDFPlumber extraction failed: {str(e)}")
    
    async def extract_pages(self, pdf_path: str) -> List[str]:
        """Extract text from individual pages using PDFPlumber"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    pages.append(page_text if page_text else "")
            return pages
        except Exception as e:
            raise Exception(f"PDFPlumber page extraction failed: {str(e)}")
    
    async def extract_metadata(self, pdf_path: str) -> dict:
        """Extract PDF metadata using PDFPlumber"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata = pdf.metadata
                return {
                    'title': metadata.get('Title', ''),
                    'author': metadata.get('Author', ''),
                    'subject': metadata.get('Subject', ''),
                    'creator': metadata.get('Creator', ''),
                    'producer': metadata.get('Producer', ''),
                    'pages': len(pdf.pages)
                }
        except Exception as e:
            raise Exception(f"PDFPlumber metadata extraction failed: {str(e)}")
