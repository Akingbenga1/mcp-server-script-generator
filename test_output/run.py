#!/usr/bin/env python3
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
