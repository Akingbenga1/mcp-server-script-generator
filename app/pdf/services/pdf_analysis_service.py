"""
PDF Analysis Service
Orchestrates the PDF analysis workflow following SOLID principles
"""

from typing import List, Dict, Any, Optional
from app.pdf.extractors.base_extractor import BasePDFExtractor
from app.pdf.parsers.base_parser import BaseAPIParser
from app.pdf.validators.base_validator import BaseFileValidator
from app.models import APIEndpoint, APIDiscovery, WebsiteAnalysis
from datetime import datetime

class PDFAnalysisResult:
    """Result of PDF analysis"""
    def __init__(self, endpoints: List[APIEndpoint], schema: Dict[str, Any], metadata: Dict[str, Any]):
        self.endpoints = endpoints
        self.schema = schema
        self.metadata = metadata

class PDFAnalysisService:
    """Service for analyzing PDF files and extracting API endpoints"""
    
    def __init__(
        self,
        extractor: BasePDFExtractor,
        parser: BaseAPIParser,
        validator: BaseFileValidator
    ):
        self.extractor = extractor
        self.parser = parser
        self.validator = validator
    
    async def analyze_pdf(self, pdf_path: str) -> PDFAnalysisResult:
        """Main analysis workflow"""
        # Validate file
        is_valid, error_message = await self.validator.validate(pdf_path)
        if not is_valid:
            raise ValueError(error_message)
        
        # Extract text
        text_content = await self.extractor.extract_text(pdf_path)
        pages = await self.extractor.extract_pages(pdf_path)
        metadata = await self.extractor.extract_metadata(pdf_path)
        
        # Parse endpoints
        endpoints = await self.parser.parse_endpoints(text_content)
        schema = await self.parser.parse_schema(text_content)
        auth_info = await self.parser.parse_authentication(text_content)
        
        # Create analysis result
        result = PDFAnalysisResult(
            endpoints=endpoints,
            schema=schema,
            metadata={
                'file_path': pdf_path,
                'page_count': len(pages),
                'text_length': len(text_content),
                'extraction_method': self.extractor.__class__.__name__,
                'parser_method': self.parser.__class__.__name__,
                'pdf_metadata': metadata,
                'authentication_info': auth_info,
                'analysis_timestamp': datetime.now().isoformat()
            }
        )
        
        return result
    
    async def convert_to_website_analysis(self, pdf_path: str, result: PDFAnalysisResult) -> WebsiteAnalysis:
        """Convert PDF analysis result to WebsiteAnalysis format"""
        return WebsiteAnalysis(
            url=f"pdf://{pdf_path}",
            title=f"PDF Analysis: {pdf_path.split('/')[-1]}",
            description=f"API endpoints extracted from PDF document",
            pages=[],  # PDFs don't have traditional web pages
            forms=[],  # PDFs don't have forms
            api_endpoints=[endpoint.url for endpoint in result.endpoints],
            javascript_files=[],
            css_files=[],
            external_apis=[],
            analysis_timestamp=datetime.now()
        )
    
    async def convert_to_api_discovery(self, pdf_path: str, result: PDFAnalysisResult) -> APIDiscovery:
        """Convert PDF analysis result to APIDiscovery format"""
        return APIDiscovery(
            base_url=f"pdf://{pdf_path}",
            endpoints=result.endpoints,
            authentication=None,  # Will be populated from auth_info if needed
            schemas=result.schema,
            openapi_specs=[],
            openapi_spec=result.schema if result.schema else None
        )
