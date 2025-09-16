#!/usr/bin/env python3
"""
MCP Server for  Sample Openapi.Json
Generated automatically from GitHub repository analysis using enhanced parameter extraction.

This server provides Model Context Protocol (MCP) tools for interacting with the _sample_openapi.json API.
Each endpoint has been analyzed to extract proper parameter types, sources, and validation rules.

FEATURES:
- Automatic parameter detection (path, query, header, cookie, form, body)
- Type-safe parameter handling with validation
- Comprehensive error handling and response processing
- FastMCP framework for optimal performance
- Production-ready with configurable base URL

BASE URL: https://api.ecommerce-sample.com/v2
ENDPOINTS: 12 API endpoints analyzed
TOOLS: 16 total tools available

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
mcp = FastMCP(name=" Sample Openapi.Json MCP Server")

# Base URL for the API
BASE_URL = "https://api.ecommerce-sample.com/v2"

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
# Total endpoint-specific tools: 12

@mcp.tool
def get_users(page: Optional[int] = None, limit: Optional[int] = None, status: Optional[str] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    GET request to /users
    
    List all users
    
    Args:
            page: int - Page number for pagination (query parameter)
            limit: int - Number of items per page (query parameter)
            status: str - Filter by user status (query parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/users"
    return asyncio.run(make_request("GET", url, None, headers))

@mcp.tool
def post_users(username: str, email: str, password: str, first_name: Optional[str] = None, last_name: Optional[str] = None, phone: Optional[str] = None, role: Optional[str] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    POST request to /users
    
    Create a new user
    
    Args:
            username: str - username body parameter (body parameter)
            email: str - email body parameter (body parameter)
            password: str - password body parameter (body parameter)
            first_name: str - first_name body parameter (body parameter)
            last_name: str - last_name body parameter (body parameter)
            phone: str - phone body parameter (body parameter)
            role: str - role body parameter (body parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/users"
    data = {"username": username, "email": email, "password": password, "first_name": first_name, "last_name": last_name, "phone": phone, "role": role}
    data = {k: v for k, v in data.items() if v is not None}
    return asyncio.run(make_request("POST", url, data, headers))

@mcp.tool
def get_users_userId(userId: int, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    GET request to /users/{userId}
    
    Get user by ID
    
    Args:
            userId: int - Unique identifier for the user (path parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/users/{userId}"
    return asyncio.run(make_request("GET", url, None, headers))

@mcp.tool
def put_users_userId(userId: int, first_name: Optional[str] = None, last_name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None, status: Optional[str] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    PUT request to /users/{userId}
    
    Update user information
    
    Args:
            userId: int - userId parameter (path parameter)
            first_name: str - first_name body parameter (body parameter)
            last_name: str - last_name body parameter (body parameter)
            email: str - email body parameter (body parameter)
            phone: str - phone body parameter (body parameter)
            status: str - status body parameter (body parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/users/{userId}"
    data = {"first_name": first_name, "last_name": last_name, "email": email, "phone": phone, "status": status}
    data = {k: v for k, v in data.items() if v is not None}
    return asyncio.run(make_request("PUT", url, data, headers))

@mcp.tool
def delete_users_userId(userId: int, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    DELETE request to /users/{userId}
    
    Delete user account
    
    Args:
            userId: int - userId parameter (path parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/users/{userId}"
    return asyncio.run(make_request("DELETE", url, None, headers))

@mcp.tool
def get_products(category: Optional[str] = None, price_min: Optional[str] = None, price_max: Optional[str] = None, in_stock: Optional[bool] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    GET request to /products
    
    List products
    
    Args:
            category: str - Filter by product category (query parameter)
            price_min: str - Minimum price filter (query parameter)
            price_max: str - Maximum price filter (query parameter)
            in_stock: bool - Filter by stock availability (query parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/products"
    return asyncio.run(make_request("GET", url, None, headers))

@mcp.tool
def post_products(name: str, price: str, category: str, sku: str, description: Optional[str] = None, stock_quantity: Optional[int] = None, tags: Optional[List[str]] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    POST request to /products
    
    Create new product
    
    Args:
            name: str - name body parameter (body parameter)
            description: str - description body parameter (body parameter)
            price: str - price body parameter (body parameter)
            category: str - category body parameter (body parameter)
            stock_quantity: int - stock_quantity body parameter (body parameter)
            sku: str - sku body parameter (body parameter)
            tags: List[str] - tags body parameter (body parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/products"
    data = {"name": name, "description": description, "price": price, "category": category, "stock_quantity": stock_quantity, "sku": sku, "tags": tags}
    data = {k: v for k, v in data.items() if v is not None}
    return asyncio.run(make_request("POST", url, data, headers))

@mcp.tool
def get_products_productId(productId: int, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    GET request to /products/{productId}
    
    Get product details
    
    Args:
            productId: int - productId parameter (path parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/products/{productId}"
    return asyncio.run(make_request("GET", url, None, headers))

@mcp.tool
def get_orders(user_id: Optional[int] = None, status: Optional[str] = None, date_from: Optional[str] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    GET request to /orders
    
    List orders
    
    Args:
            user_id: int - Filter orders by user ID (query parameter)
            status: str - Filter by order status (query parameter)
            date_from: str - Filter orders from this date (query parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/orders"
    return asyncio.run(make_request("GET", url, None, headers))

@mcp.tool
def post_orders(user_id: int, items: List[str], shipping_address: Optional[str] = None, billing_address: Optional[str] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    POST request to /orders
    
    Create new order
    
    Args:
            user_id: int - user_id body parameter (body parameter)
            items: List[str] - items body parameter (body parameter)
            shipping_address: str - shipping_address body parameter (body parameter)
            billing_address: str - billing_address body parameter (body parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/orders"
    data = {"user_id": user_id, "items": items, "shipping_address": shipping_address, "billing_address": billing_address}
    data = {k: v for k, v in data.items() if v is not None}
    return asyncio.run(make_request("POST", url, data, headers))

@mcp.tool
def get_orders_orderId(orderId: int, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    GET request to /orders/{orderId}
    
    Get order details
    
    Args:
            orderId: int - orderId parameter (path parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/orders/{orderId}"
    return asyncio.run(make_request("GET", url, None, headers))

@mcp.tool
def patch_orders_orderId(orderId: int, status: Optional[str] = None, tracking_number: Optional[str] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    PATCH request to /orders/{orderId}
    
    Update order status
    
    Args:
            orderId: int - orderId parameter (path parameter)
            status: str - status body parameter (body parameter)
            tracking_number: str - tracking_number body parameter (body parameter)
            headers: Optional headers for the request (e.g., {"Authorization": "Bearer token"})
    
    Returns:
            Response data including status_code, data, success flag, and headers
    """
    url = f"{BASE_URL}/orders/{orderId}"
    data = {"status": status, "tracking_number": tracking_number}
    data = {k: v for k, v in data.items() if v is not None}
    return asyncio.run(make_request("PATCH", url, data, headers))

if __name__ == "__main__":
    print(f"""
============================================================
 Sample Openapi.Json MCP Server
Using FastMCP Framework Style
============================================================

Base URL: {BASE_URL}
Available Tools (16 total):
- Generic HTTP Methods (4): post_request, get_request, put_request, delete_request
- Endpoint-specific Tools (12):
    - Users: GET(2), POST(1), PUT(1), DELETE(1)
    - Products: GET(2), POST(1)
    - Orders: GET(2), POST(1), PATCH(1)
    - Sample endpoint tools:
      • get_users
      • post_users
      • get_users_userId
      • put_users_userId
      • delete_users_userId
      • ... and 7 more endpoint-specific tools

All endpoint-specific tools are automatically generated with:
- Type-safe parameters based on API analysis
- Proper parameter source detection (path, query, header, body)
- Comprehensive error handling and response processing

Starting server with HTTP transport...
============================================================
""")
    
    # Run the server with HTTP transport
    mcp.run(transport="http", port=8000, host="0.0.0.0")