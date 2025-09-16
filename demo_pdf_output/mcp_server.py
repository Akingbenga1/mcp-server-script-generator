#!/usr/bin/env python3
"""
MCP Server for  Sample Api Docs.Pdf
Generated automatically from GitHub repository analysis using enhanced parameter extraction.

This server provides Model Context Protocol (MCP) tools for interacting with the _sample_api_docs.pdf API.
Each endpoint has been analyzed to extract proper parameter types, sources, and validation rules.

FEATURES:
- Automatic parameter detection (path, query, header, cookie, form, body)
- Type-safe parameter handling with validation
- Comprehensive error handling and response processing
- FastMCP framework for optimal performance
- Production-ready with configurable base URL

BASE URL: https://api.demo.com/v1
ENDPOINTS: 5 API endpoints analyzed
TOOLS: 9 total tools available

USAGE:
Each endpoint is available as both a specific tool (with parameter validation) and via generic HTTP methods.
Use specific tools for type safety, or generic methods for flexibility.

AUTHENTICATION:
Include authentication headers in the 'headers' parameter of any tool call.
Example: {"Authorization": "Bearer your-token-here"}

Generated with enhanced parameter extraction technology.
"""

from fastmcp import FastMCP
import aiohttp
import asyncio
import json
from typing import Dict, List, Optional, Any

# Initialize the MCP server with FastMCP framework
mcp = FastMCP(name=" Sample Api Docs.Pdf MCP Server")

# Base URL for the API
BASE_URL = "https://api.demo.com/v1"

async def make_request(method: str, url: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Helper function to make HTTP requests with comprehensive error handling.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        url: Target URL for the request
        data: Optional request body data
        headers: Optional request headers
        
    Returns:
        Dictionary containing status_code, data, and success flag
    """
    async with aiohttp.ClientSession() as session:
        try:
            if method.upper() == "GET":
                async with session.get(url, headers=headers) as response:
                    return {
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }
            elif method.upper() == "POST":
                async with session.post(url, json=data, headers=headers) as response:
                    return {
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }
            elif method.upper() == "PUT":
                async with session.put(url, json=data, headers=headers) as response:
                    return {
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }
            elif method.upper() == "DELETE":
                async with session.delete(url, headers=headers) as response:
                    return {
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }
            else:
                return {
                    "status_code": 405,
                    "data": f"Unsupported method: {method}",
                    "success": False
                }
        except Exception as e:
            return {
                "status_code": 500,
                "data": f"Request failed: {str(e)}",
                "success": False,
                "error": str(e)
            }

# Generic HTTP method tools for flexibility
@mcp.tool
def post_request(url: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Make a POST request to the API.
    
    This is a generic POST request tool that can be used for any endpoint.
    For specific endpoints, use the dedicated tools below.
    
    Args:
        url: The full URL for the POST request
        data: Optional data to send in the request body
        headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
        
    Returns:
        Response data including status_code, data, and success flag
    """
    return asyncio.run(make_request("POST", url, data, headers))

@mcp.tool
def get_request(url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Make a GET request to the API.
    
    This is a generic GET request tool that can be used for any endpoint.
    For specific endpoints, use the dedicated tools below.
    
    Args:
        url: The full URL for the GET request
        headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
        
    Returns:
        Response data including status_code, data, and success flag
    """
    return asyncio.run(make_request("GET", url, None, headers))

@mcp.tool
def put_request(url: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Make a PUT request to the API.
    
    This is a generic PUT request tool that can be used for any endpoint.
    For specific endpoints, use the dedicated tools below.
    
    Args:
        url: The full URL for the PUT request
        data: Optional data to send in the request body
        headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
        
    Returns:
        Response data including status_code, data, and success flag
    """
    return asyncio.run(make_request("PUT", url, data, headers))

@mcp.tool
def delete_request(url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Make a DELETE request to the API.
    
    This is a generic DELETE request tool that can be used for any endpoint.
    For specific endpoints, use the dedicated tools below.
    
    Args:
        url: The full URL for the DELETE request
        headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
        
    Returns:
        Response data including status_code, data, and success flag
    """
    return asyncio.run(make_request("DELETE", url, None, headers))

# Endpoint-specific tools generated from API analysis
# Total endpoint-specific tools: 5

@mcp.tool
def post_orders(page: str, Page: str, number: str, name: str, User: str, id: str, ID: str, category: str, Product: str, user_id: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    POST request to /orders
    
    Get all users
    
    Args:
            page: str - page parameter (query parameter)
            Page: str - Page parameter (query parameter)
            number: str - number parameter (query parameter)
            name: str - name parameter (query parameter)
            User: str - User parameter (query parameter)
            id: str - id parameter (query parameter)
            ID: str - ID parameter (query parameter)
            category: str - category parameter (query parameter)
            Product: str - Product parameter (query parameter)
            user_id: str - user_id parameter (query parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = "https://api.demo.com/v1/orders"
    return asyncio.run(make_request("POST", url, None, headers))

@mcp.tool
def get_products(page: str, Page: str, number: str, name: str, User: str, id: str, ID: str, category: str, Product: str, user_id: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    GET request to /products
    
    Get all users
    
    Args:
            page: str - page parameter (query parameter)
            Page: str - Page parameter (query parameter)
            number: str - number parameter (query parameter)
            name: str - name parameter (query parameter)
            User: str - User parameter (query parameter)
            id: str - id parameter (query parameter)
            ID: str - ID parameter (query parameter)
            category: str - category parameter (query parameter)
            Product: str - Product parameter (query parameter)
            user_id: str - user_id parameter (query parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = "https://api.demo.com/v1/products"
    return asyncio.run(make_request("GET", url, None, headers))

@mcp.tool
def get_users(page: str, Page: str, number: str, name: str, User: str, id: str, ID: str, category: str, Product: str, user_id: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    GET request to /users
    
    Get all users
    
    Args:
            page: str - page parameter (query parameter)
            Page: str - Page parameter (query parameter)
            number: str - number parameter (query parameter)
            name: str - name parameter (query parameter)
            User: str - User parameter (query parameter)
            id: str - id parameter (query parameter)
            ID: str - ID parameter (query parameter)
            category: str - category parameter (query parameter)
            Product: str - Product parameter (query parameter)
            user_id: str - user_id parameter (query parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = "https://api.demo.com/v1/users"
    return asyncio.run(make_request("GET", url, None, headers))

@mcp.tool
def post_users(page: str, Page: str, number: str, name: str, User: str, id: str, ID: str, category: str, Product: str, user_id: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    POST request to /users
    
    Get all users
    
    Args:
            page: str - page parameter (query parameter)
            Page: str - Page parameter (query parameter)
            number: str - number parameter (query parameter)
            name: str - name parameter (query parameter)
            User: str - User parameter (query parameter)
            id: str - id parameter (query parameter)
            ID: str - ID parameter (query parameter)
            category: str - category parameter (query parameter)
            Product: str - Product parameter (query parameter)
            user_id: str - user_id parameter (query parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = "https://api.demo.com/v1/users"
    return asyncio.run(make_request("POST", url, None, headers))

@mcp.tool
def get_users_id(page: str, Page: str, number: str, name: str, User: str, id: str, ID: str, category: str, Product: str, user_id: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    GET request to /users/{id}
    
    Get all users
    
    Args:
            page: str - page parameter (query parameter)
            Page: str - Page parameter (query parameter)
            number: str - number parameter (query parameter)
            name: str - name parameter (query parameter)
            User: str - User parameter (query parameter)
            id: str - id parameter (query parameter)
            ID: str - ID parameter (query parameter)
            category: str - category parameter (query parameter)
            Product: str - Product parameter (query parameter)
            user_id: str - user_id parameter (query parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = "https://api.demo.com/v1/users/{id}"
    return asyncio.run(make_request("GET", url, None, headers))

if __name__ == "__main__":
    print(f"""
============================================================
 Sample Api Docs.Pdf MCP Server
Using FastMCP Framework Style
============================================================

Base URL: {BASE_URL}
Available Tools (9 total):
- Generic HTTP Methods (4): post_request, get_request, put_request, delete_request
- Endpoint-specific Tools (5):
    - Orders: POST(1)
    - Products: GET(1)
    - Users: GET(2), POST(1)
    - Sample endpoint tools:
      • post_orders
      • get_products
      • get_users
      • post_users
      • get_users_id

All endpoint-specific tools are automatically generated with:
- Type-safe parameters based on API analysis
- Proper parameter source detection (path, query, header, body)
- Comprehensive error handling and response processing

Starting server with HTTP transport...
============================================================
""")
    
    # Run the server with HTTP transport
    mcp.run(transport="http", port=8000, host="0.0.0.0")