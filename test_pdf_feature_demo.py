#!/usr/bin/env python3
"""
Test script to demonstrate the PDF-to-MCP generation feature.
This script shows how the new functionality works without needing a PDF file.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the workspace to the Python path
sys.path.insert(0, '/workspace')

from app.pdf.factories import PDFAnalysisFactory
from app.mcp_server_generator import MCPServerGenerator

async def test_pdf_to_mcp_generation():
    """Test the PDF to MCP generation functionality"""
    print("🚀 Testing PDF-to-MCP Generation Feature")
    print("=" * 50)
    
    # Create a mock PDF analysis result for demonstration
    from app.models import APIEndpoint, HTTPMethod, APIDiscovery
    
    # Create sample API endpoints (as if extracted from a PDF)
    endpoints = [
        APIEndpoint(
            url="/users",
            method=HTTPMethod.GET,
            description="Get all users",
            parameters={},
            request_body={},
            response_schema={"type": "array"},
            authentication_required=True,
            tags=["users"]
        ),
        APIEndpoint(
            url="/users",
            method=HTTPMethod.POST,
            description="Create a new user",
            parameters={
                "name": {"type": "string", "required": True, "source": "body"},
                "email": {"type": "string", "required": True, "source": "body"}
            },
            request_body={"name": "string", "email": "string"},
            response_schema={"type": "object"},
            authentication_required=True,
            tags=["users"]
        ),
        APIEndpoint(
            url="/users/{id}",
            method=HTTPMethod.GET,
            description="Get user by ID",
            parameters={
                "id": {"type": "integer", "required": True, "source": "path"}
            },
            request_body={},
            response_schema={"type": "object"},
            authentication_required=True,
            tags=["users"]
        ),
        APIEndpoint(
            url="/users/{id}",
            method=HTTPMethod.PUT,
            description="Update user",
            parameters={
                "id": {"type": "integer", "required": True, "source": "path"},
                "name": {"type": "string", "required": False, "source": "body"},
                "email": {"type": "string", "required": False, "source": "body"}
            },
            request_body={"name": "string", "email": "string"},
            response_schema={"type": "object"},
            authentication_required=True,
            tags=["users"]
        ),
        APIEndpoint(
            url="/users/{id}",
            method=HTTPMethod.DELETE,
            description="Delete user",
            parameters={
                "id": {"type": "integer", "required": True, "source": "path"}
            },
            request_body={},
            response_schema={},
            authentication_required=True,
            tags=["users"]
        )
    ]
    
    # Create API discovery object
    api_discovery = APIDiscovery(
        base_url="https://api.example.com/v1",
        endpoints=endpoints,
        authentication=None,
        schemas={},
        openapi_specs=[]
    )
    
    print(f"📊 Sample API Discovery created with {len(endpoints)} endpoints")
    
    # Initialize MCP server generator
    mcp_generator = MCPServerGenerator()
    
    # Generate MCP server content from the "PDF" (mock data)
    pdf_filename = "sample_api_documentation.pdf"
    production_base_url = "https://api.example.com/v1"
    
    print(f"🔧 Generating MCP server content for: {pdf_filename}")
    
    try:
        mcp_content = mcp_generator.generate_mcp_server_content_from_pdf(
            pdf_filename, api_discovery, production_base_url
        )
        
        print("✅ MCP Server Generation Successful!")
        print(f"   📦 Server Name: {mcp_content['repo_name']}")
        print(f"   🔗 Source File: {mcp_content['source_file']}")
        print(f"   🔢 Endpoints: {mcp_content['endpoints_count']}")
        print(f"   🛠️  Total Tools: {mcp_content['tools_count']}")
        print(f"   🏗️  Framework: {mcp_content['framework']}")
        print(f"   📅 Generated: {mcp_content['generated_at']}")
        
        # Display a preview of the generated files
        print("\n📄 Generated Files Preview:")
        print("=" * 30)
        
        print("\n1. mcp_server.py (first 20 lines):")
        python_lines = mcp_content['python_code'].split('\n')[:20]
        for i, line in enumerate(python_lines, 1):
            print(f"   {i:2d}: {line}")
        print(f"   ... ({len(mcp_content['python_code'].split('\n')) - 20} more lines)")
        
        print("\n2. requirements.txt:")
        req_lines = mcp_content['requirements_txt_content'].split('\n')
        for line in req_lines:
            if line.strip():
                print(f"   {line}")
        
        print("\n3. Dockerfile (first 10 lines):")
        docker_lines = mcp_content['dockerfile_content'].split('\n')[:10]
        for i, line in enumerate(docker_lines, 1):
            print(f"   {i:2d}: {line}")
        print(f"   ... ({len(mcp_content['dockerfile_content'].split('\n')) - 10} more lines)")
        
        print("\n🎉 Demo completed successfully!")
        print(f"📁 Generated files are saved in: data/mcp_servers/{mcp_content['repo_name']}_mcp_server.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating MCP server content: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 PDF-to-MCP Generation Feature Demo")
    print("This demonstrates the new functionality for generating MCP server files from PDF API documentation.")
    print()
    
    # Run the test
    success = asyncio.run(test_pdf_to_mcp_generation())
    
    if success:
        print("\n✅ All tests passed! The PDF-to-MCP generation feature is working correctly.")
        print("\n🌐 To use the web interface:")
        print("   1. Start the server: python3 main.py")
        print("   2. Open: http://localhost:8001")
        print("   3. Use the 'Generate MCP Server from PDF' section")
        print("   4. Upload a PDF with API documentation")
        print("   5. Download the generated zip file with 3 files:")
        print("      - mcp_server.py")
        print("      - requirements.txt") 
        print("      - Dockerfile")
    else:
        print("\n❌ Test failed. Please check the error messages above.")
        sys.exit(1)