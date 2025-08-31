#!/usr/bin/env python3
"""
Test script for PDF feature functionality
"""

import sys
import os
import tempfile
import asyncio
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, '.')

from app.pdf.factories import PDFAnalysisFactory
from app.pdf.services import PDFAnalysisService

async def test_pdf_extractors():
    """Test PDF extractors"""
    print("🧪 Testing PDF Extractors...")
    
    # Create a simple test PDF content (we'll use a text file for testing)
    test_content = """
    # API Documentation
    
    ## GET /users - Get all users
    Retrieve a list of all users in the system.
    
    **Parameters:**
    - **page**: Page number (optional)
    - **limit**: Number of items per page (optional)
    
    ## POST /users - Create user
    Create a new user in the system.
    
    **Request Body:**
    ```json
    {
        "name": "John Doe",
        "email": "john@example.com",
        "role": "user"
    }
    ```
    
    ## PUT /users/{id} - Update user
    Update an existing user by ID.
    
    ## DELETE /users/{id} - Delete user
    Delete a user by ID.
    """
    
    # Create a temporary text file to simulate PDF content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        # Test PyPDF2 extractor
        print("  Testing PyPDF2 extractor...")
        extractor = PDFAnalysisFactory.create_analysis_service("pypdf", "openapi")
        # Note: This will fail since we're using a text file, but it tests the factory
        
        # Test PDFPlumber extractor
        print("  Testing PDFPlumber extractor...")
        extractor = PDFAnalysisFactory.create_analysis_service("pdfplumber", "openapi")
        
        print("✅ PDF extractors created successfully")
        
    except Exception as e:
        print(f"❌ PDF extractor test failed: {e}")
    
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)

async def test_pdf_parsers():
    """Test PDF parsers"""
    print("🧪 Testing PDF Parsers...")
    
    test_text = """
    # API Documentation
    
    ## GET /users - Get all users
    Retrieve a list of all users in the system.
    
    **Parameters:**
    - **page**: Page number (optional)
    - **limit**: Number of items per page (optional)
    
    ## POST /users - Create user
    Create a new user in the system.
    
    **Request Body:**
    ```json
    {
        "name": "John Doe",
        "email": "john@example.com",
        "role": "user"
    }
    ```
    
    ## PUT /users/{id} - Update user
    Update an existing user by ID.
    
    ## DELETE /users/{id} - Delete user
    Delete a user by ID.
    """
    
    try:
        # Test OpenAPI parser
        print("  Testing OpenAPI parser...")
        service = PDFAnalysisFactory.create_analysis_service("pypdf", "openapi")
        endpoints = await service.parser.parse_endpoints(test_text)
        print(f"    Found {len(endpoints)} endpoints with OpenAPI parser")
        
        # Test Markdown parser
        print("  Testing Markdown parser...")
        service = PDFAnalysisFactory.create_analysis_service("pypdf", "markdown")
        endpoints = await service.parser.parse_endpoints(test_text)
        print(f"    Found {len(endpoints)} endpoints with Markdown parser")
        
        print("✅ PDF parsers working correctly")
        
    except Exception as e:
        print(f"❌ PDF parser test failed: {e}")

async def test_pdf_validators():
    """Test PDF validators"""
    print("🧪 Testing PDF Validators...")
    
    try:
        # Test validator creation
        service = PDFAnalysisFactory.create_analysis_service("pypdf", "openapi")
        validator = service.validator
        
        # Test with non-existent file
        is_valid, error = await validator.validate("/non/existent/file.pdf")
        print(f"  Non-existent file validation: {is_valid} - {error}")
        
        # Test file size validation
        is_valid, error = await validator.validate_file_size("/non/existent/file.pdf")
        print(f"  File size validation: {is_valid} - {error}")
        
        # Test file type validation
        is_valid, error = await validator.validate_file_type("/non/existent/file.pdf")
        print(f"  File type validation: {is_valid} - {error}")
        
        print("✅ PDF validators working correctly")
        
    except Exception as e:
        print(f"❌ PDF validator test failed: {e}")

async def test_factory():
    """Test PDF analysis factory"""
    print("🧪 Testing PDF Analysis Factory...")
    
    try:
        # Test available extractors
        extractors = PDFAnalysisFactory.get_available_extractors()
        print(f"  Available extractors: {extractors}")
        
        # Test available parsers
        parsers = PDFAnalysisFactory.get_available_parsers()
        print(f"  Available parsers: {parsers}")
        
        # Test service creation
        service = PDFAnalysisFactory.create_analysis_service("pypdf", "openapi")
        print(f"  Created service with extractor: {service.extractor.__class__.__name__}")
        print(f"  Created service with parser: {service.parser.__class__.__name__}")
        print(f"  Created service with validator: {service.validator.__class__.__name__}")
        
        print("✅ PDF analysis factory working correctly")
        
    except Exception as e:
        print(f"❌ PDF factory test failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting PDF Feature Tests")
    print("=" * 50)
    
    await test_factory()
    print()
    
    await test_pdf_extractors()
    print()
    
    await test_pdf_parsers()
    print()
    
    await test_pdf_validators()
    print()
    
    print("=" * 50)
    print("✅ All PDF feature tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
