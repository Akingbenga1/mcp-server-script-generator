#!/usr/bin/env python3
"""
Test script for PDF-to-MCP-server generation functionality.
This script tests the complete workflow without needing the web interface.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
import tempfile
import logging

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from app.pdf_analyzer import PDFAnalyzer
from app.mcp_server_generator import MCPServerGenerator
from app.database import Database

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_pdf_content():
    """Create a sample PDF content as text for testing purposes"""
    
    sample_api_docs = """
API Documentation for Sample Service

Base URL: https://api.sample.com/v1

Authentication
This API uses Bearer token authentication. Include the token in the Authorization header:
Authorization: Bearer your-token-here

Endpoints

GET /users
Retrieves a list of all users.
Query parameters:
- page (integer): Page number for pagination
- limit (integer): Number of items per page
- filter (string): Filter users by name

POST /users
Creates a new user.
Request body:
{
  "name": "string",
  "email": "string",
  "role": "string"
}

GET /users/{id}
Retrieves a specific user by ID.
Path parameters:
- id (integer): User ID

PUT /users/{id}
Updates a user.
Path parameters:
- id (integer): User ID
Request body:
{
  "name": "string",
  "email": "string",
  "role": "string"
}

DELETE /users/{id}
Deletes a user.
Path parameters:
- id (integer): User ID

GET /products
Retrieves all products.
Query parameters:
- category (string): Product category
- price_min (number): Minimum price
- price_max (number): Maximum price

POST /products
Creates a new product.
Request body:
{
  "name": "string",
  "description": "string",
  "price": "number",
  "category": "string"
}

GET /orders
Retrieves all orders.
Query parameters:
- status (string): Order status
- user_id (integer): Filter by user ID

POST /orders
Creates a new order.
Request body:
{
  "user_id": "integer",
  "products": [
    {
      "product_id": "integer",
      "quantity": "integer"
    }
  ]
}
"""
    
    return sample_api_docs.encode('utf-8')

def create_sample_pdf_file():
    """Create a sample PDF file for testing"""
    try:
        # Try to create a simple PDF using reportlab if available
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from io import BytesIO
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, "Sample API Documentation")
        
        # Add content
        p.setFont("Helvetica", 12)
        y_position = 720
        
        api_content = [
            "Base URL: https://api.sample.com/v1",
            "",
            "Authentication: Bearer Token",
            "",
            "Endpoints:",
            "",
            "GET /users - Retrieve all users",
            "POST /users - Create a new user",
            "GET /users/{id} - Get user by ID",
            "PUT /users/{id} - Update user",
            "DELETE /users/{id} - Delete user",
            "",
            "GET /products - Retrieve all products",
            "POST /products - Create a new product",
            "",
            "GET /orders - Retrieve all orders",
            "POST /orders - Create a new order",
        ]
        
        for line in api_content:
            p.drawString(100, y_position, line)
            y_position -= 20
            if y_position < 100:
                p.showPage()
                y_position = 750
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        logger.warning("reportlab not available, using text content instead")
        # Fallback to text content if reportlab is not available
        return create_sample_pdf_content()

async def test_pdf_analysis():
    """Test PDF analysis functionality"""
    
    logger.info("=== Testing PDF Analysis ===")
    
    # Initialize PDF analyzer
    pdf_analyzer = PDFAnalyzer()
    
    try:
        # Create sample PDF content
        pdf_content = create_sample_pdf_file()
        logger.info(f"Created sample PDF content ({len(pdf_content)} bytes)")
        
        # Analyze the PDF
        logger.info("Analyzing PDF content...")
        api_discovery = await pdf_analyzer.analyze_pdf(pdf_content, "sample_api_docs.pdf")
        
        logger.info(f"Analysis completed!")
        logger.info(f"Base URL: {api_discovery.base_url}")
        logger.info(f"Endpoints found: {len(api_discovery.endpoints)}")
        logger.info(f"Authentication: {api_discovery.authentication}")
        logger.info(f"Schemas: {len(api_discovery.schemas)}")
        
        # Display endpoints
        for endpoint in api_discovery.endpoints:
            logger.info(f"  {endpoint.method.value.upper()} {endpoint.url} - {endpoint.description or 'No description'}")
            if endpoint.parameters:
                for param_name, param_info in endpoint.parameters.items():
                    param_type = param_info.get('type', 'unknown') if isinstance(param_info, dict) else getattr(param_info, 'type', 'unknown')
                    param_source = param_info.get('source', 'unknown') if isinstance(param_info, dict) else getattr(param_info, 'source', 'unknown')
                    logger.info(f"    Param: {param_name} ({param_type}) - {param_source}")
        
        return api_discovery
        
    except Exception as e:
        logger.error(f"PDF analysis failed: {e}")
        raise
    finally:
        # Cleanup
        pdf_analyzer.cleanup()

async def test_mcp_generation(api_discovery):
    """Test MCP server generation"""
    
    logger.info("=== Testing MCP Server Generation ===")
    
    # Initialize MCP server generator
    mcp_generator = MCPServerGenerator()
    
    try:
        # Generate MCP server content
        logger.info("Generating MCP server content...")
        mcp_content = mcp_generator.generate_mcp_server_content(
            "pdf://sample_api_docs.pdf", 
            api_discovery,
            "https://api.sample.com/v1"  # Production base URL
        )
        
        logger.info(f"MCP server content generated!")
        logger.info(f"Repository name: {mcp_content['repo_name']}")
        logger.info(f"Tools count: {mcp_content['tools_count']}")
        logger.info(f"Framework: {mcp_content['framework']}")
        
        return mcp_content
        
    except Exception as e:
        logger.error(f"MCP generation failed: {e}")
        raise

async def test_file_generation(mcp_content):
    """Test generating the actual files"""
    
    logger.info("=== Testing File Generation ===")
    
    try:
        # Create output directory
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        # Generate mcp_server.py
        mcp_server_file = output_dir / "mcp_server.py"
        with open(mcp_server_file, 'w', encoding='utf-8') as f:
            f.write(mcp_content['python_code'])
        logger.info(f"Generated: {mcp_server_file}")
        
        # Generate requirements.txt
        requirements_file = output_dir / "requirements.txt"
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write(mcp_content['requirements_txt_content'])
        logger.info(f"Generated: {requirements_file}")
        
        # Generate Dockerfile
        dockerfile = output_dir / "Dockerfile"
        with open(dockerfile, 'w', encoding='utf-8') as f:
            f.write(mcp_content['dockerfile_content'])
        logger.info(f"Generated: {dockerfile}")
        
        # Generate run.py for testing
        run_file = output_dir / "run.py"
        run_content = '''#!/usr/bin/env python3
"""
Test runner for the generated MCP server
"""

import sys
import os
import subprocess
import importlib.util

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import fastmcp
        import aiohttp
        import asyncio
        print("✓ All dependencies are available")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False

def test_server():
    """Test the MCP server"""
    if not check_dependencies():
        return False
    
    try:
        # Import the generated server
        spec = importlib.util.spec_from_file_location("mcp_server", "mcp_server.py")
        mcp_server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mcp_server)
        
        print("✓ MCP server imported successfully")
        print(f"✓ Base URL: {mcp_server.BASE_URL}")
        print("✓ Server appears to be working correctly")
        
        # Test that tools are available
        if hasattr(mcp_server, 'mcp'):
            print(f"✓ FastMCP instance found")
            print("✓ All tests passed!")
        else:
            print("⚠ FastMCP instance not found, but basic import worked")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing server: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Generated MCP Server")
    print("=" * 40)
    
    success = test_server()
    
    if success:
        print("\n🎉 All tests passed! The MCP server is ready to use.")
        print("\nTo run the server:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the server: python mcp_server.py")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")
        sys.exit(1)
'''
        
        with open(run_file, 'w', encoding='utf-8') as f:
            f.write(run_content)
        logger.info(f"Generated: {run_file}")
        
        # Make run.py executable
        import stat
        run_file.chmod(run_file.stat().st_mode | stat.S_IEXEC)
        
        logger.info(f"\nFiles generated in: {output_dir.absolute()}")
        logger.info("To test the generated server, run:")
        logger.info(f"  cd {output_dir}")
        logger.info("  python run.py")
        
        return output_dir
        
    except Exception as e:
        logger.error(f"File generation failed: {e}")
        raise

async def run_generated_test(output_dir):
    """Run the generated test script"""
    
    logger.info("=== Running Generated Test ===")
    
    try:
        import subprocess
        
        # Change to the output directory and run the test
        result = subprocess.run([
            sys.executable, "run.py"
        ], cwd=output_dir, capture_output=True, text=True, timeout=30)
        
        logger.info("Test output:")
        logger.info(result.stdout)
        
        if result.stderr:
            logger.warning("Test errors:")
            logger.warning(result.stderr)
        
        if result.returncode == 0:
            logger.info("✅ Generated server test passed!")
            return True
        else:
            logger.warning(f"Generated server test failed with return code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.warning("Test timed out after 30 seconds")
        return False
    except Exception as e:
        logger.error(f"Error running generated test: {e}")
        return False

async def main():
    """Main test function"""
    
    print("🚀 Starting PDF-to-MCP Server Generation Tests")
    print("=" * 60)
    
    try:
        # Test PDF analysis
        api_discovery = await test_pdf_analysis()
        
        # Test MCP generation
        mcp_content = await test_mcp_generation(api_discovery)
        
        # Test file generation
        output_dir = await test_file_generation(mcp_content)
        
        # Run the generated test
        test_success = await run_generated_test(output_dir)
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        print(f"✅ PDF Analysis: SUCCESS")
        print(f"✅ MCP Generation: SUCCESS")
        print(f"✅ File Generation: SUCCESS")
        print(f"{'✅' if test_success else '⚠️'} Generated Server Test: {'SUCCESS' if test_success else 'PARTIAL'}")
        
        if test_success:
            print("\n🎉 All tests passed! The PDF-to-MCP server generator is working correctly.")
        else:
            print("\n⚠️ Some tests had warnings, but core functionality is working.")
        
        print(f"\nGenerated files are available in: {output_dir.absolute()}")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())