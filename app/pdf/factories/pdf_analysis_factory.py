"""
PDF Analysis Factory
Factory pattern for creating PDF analysis services
"""

from app.pdf.extractors import PyPDFExtractor, PDFPlumberExtractor
from app.pdf.parsers import OpenAPIParser, MarkdownAPIParser
from app.pdf.validators import PDFValidator
from app.pdf.services import PDFAnalysisService

class PDFAnalysisFactory:
    """Factory for creating PDF analysis services"""
    
    @staticmethod
    def create_analysis_service(
        extractor_type: str = "pypdf",
        parser_type: str = "openapi"
    ) -> PDFAnalysisService:
        """Factory method to create analysis service with specified components"""
        
        # Create extractor
        if extractor_type == "pypdf":
            extractor = PyPDFExtractor()
        elif extractor_type == "pdfplumber":
            extractor = PDFPlumberExtractor()
        else:
            raise ValueError(f"Unknown extractor type: {extractor_type}")
        
        # Create parser
        if parser_type == "openapi":
            parser = OpenAPIParser()
        elif parser_type == "markdown":
            parser = MarkdownAPIParser()
        else:
            raise ValueError(f"Unknown parser type: {parser_type}")
        
        # Create validator
        validator = PDFValidator()
        
        return PDFAnalysisService(extractor, parser, validator)
    
    @staticmethod
    def get_available_extractors() -> list:
        """Get list of available extractors"""
        return ["pypdf", "pdfplumber"]
    
    @staticmethod
    def get_available_parsers() -> list:
        """Get list of available parsers"""
        return ["openapi", "markdown"]
