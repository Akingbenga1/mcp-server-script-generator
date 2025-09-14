import json
import os
import logging
import re
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from .models import APIDiscovery, MCPTool

logger = logging.getLogger(__name__)

class MCPServerGenerator:
    """Generate FastMCP-style MCP server Python code and Dockerfile for GitHub repositories"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.mcp_servers_dir = self.data_dir / "mcp_servers"
        self.mcp_servers_dir.mkdir(exist_ok=True)
        logger.info(f"MCP Servers directory: {self.mcp_servers_dir}")
    
    def generate_mcp_server_content(self, github_url: str, api_discovery: APIDiscovery, production_base_url: str = None) -> Dict[str, Any]:
        """Generate MCP server Python code and Dockerfile content in FastMCP style"""
        try:
            # Extract repository name from GitHub URL
            repo_name = self._extract_repo_name(github_url)
            
            # Generate Python code in FastMCP style
            python_code = self._generate_fastmcp_python_code(repo_name, api_discovery, production_base_url)
            
            # Generate Dockerfile
            dockerfile_content = self._generate_dockerfile(repo_name)
            
            # Generate requirements.txt for FastMCP
            requirements_txt_content = self._generate_fastmcp_requirements()
            
            # Create content dictionary
            mcp_content = {
                "repo_name": repo_name,
                "github_url": github_url,
                "python_code": python_code,
                "dockerfile_content": dockerfile_content,
                "requirements_txt_content": requirements_txt_content,
                "generated_at": datetime.now().isoformat(),
                "endpoints_count": len(api_discovery.endpoints),
                "tools_count": len(api_discovery.endpoints) + 4,  # +4 for generic HTTP methods
                "production_base_url": production_base_url,
                "framework": "FastMCP"
            }
            
            # Save to file
            self._save_mcp_content(repo_name, mcp_content)
            
            logger.info(f"Generated FastMCP server with {mcp_content['tools_count']} tools")
            return mcp_content
            
        except Exception as e:
            logger.error(f"Error generating MCP server content: {e}")
            raise e
    
    def _extract_repo_name(self, github_url: str) -> str:
        """Extract repository name from GitHub URL"""
        try:
            if github_url.endswith('.git'):
                github_url = github_url[:-4]
            
            parts = github_url.rstrip('/').split('/')
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1]
                return f"{owner}_{repo}"
            else:
                return "unknown_repo"
        except Exception as e:
            logger.error(f"Error extracting repo name from {github_url}: {e}")
            return "unknown_repo"
    
    def _generate_fastmcp_python_code(self, repo_name: str, api_discovery: APIDiscovery, production_base_url: str = None) -> str:
        """Generate Python code for MCP server in FastMCP style"""
        logger.info(f"Generating FastMCP-style code for {repo_name} with {len(api_discovery.endpoints)} endpoints")
        
        # Generate server description
        server_description = self._generate_server_description(repo_name, api_discovery, production_base_url)
        
        # Generate endpoint-specific tools
        endpoint_tools = []
        for endpoint in api_discovery.endpoints:
            tool_code = self._generate_fastmcp_tool(endpoint, production_base_url)
            endpoint_tools.append(tool_code)
        
        # Generate tool summary for main section
        tool_summary = self._generate_tool_summary(api_discovery.endpoints)
        
        # Use the production base URL or fallback to API discovery base URL
        base_url = production_base_url if production_base_url else (api_discovery.base_url or 'https://api.example.com')
        
        python_code = f'''#!/usr/bin/env python3
"""
{server_description}
"""

from fastmcp import FastMCP
import aiohttp
import asyncio
import json
from typing import Dict, List, Optional, Any

# Initialize the MCP server with FastMCP framework
mcp = FastMCP(name="{repo_name.replace('_', ' ').title()} MCP Server")

# Base URL for the API
BASE_URL = "{base_url}"

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
                    return {{
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }}
            elif method.upper() == "POST":
                async with session.post(url, json=data, headers=headers) as response:
                    return {{
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }}
            elif method.upper() == "PUT":
                async with session.put(url, json=data, headers=headers) as response:
                    return {{
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }}
            elif method.upper() == "DELETE":
                async with session.delete(url, headers=headers) as response:
                    return {{
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }}
            else:
                return {{
                    "status_code": 405,
                    "data": f"Unsupported method: {{method}}",
                    "success": False
                }}
        except Exception as e:
            return {{
                "status_code": 500,
                "data": f"Request failed: {{str(e)}}",
                "success": False,
                "error": str(e)
            }}

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
        headers: Optional headers for the request (e.g., {{"Authorization": "Bearer token"}})
        
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
        headers: Optional headers for the request (e.g., {{"Authorization": "Bearer token"}})
        
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
        headers: Optional headers for the request (e.g., {{"Authorization": "Bearer token"}})
        
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
        headers: Optional headers for the request (e.g., {{"Authorization": "Bearer token"}})
        
    Returns:
        Response data including status_code, data, and success flag
    """
    return asyncio.run(make_request("DELETE", url, None, headers))

# Endpoint-specific tools generated from API analysis
# Total endpoint-specific tools: {len(api_discovery.endpoints)}
{"\n".join(endpoint_tools) if endpoint_tools else "# No endpoint-specific tools generated"}

if __name__ == "__main__":
    print(f"""
{'='*60}
{repo_name.replace('_', ' ').title()} MCP Server
Using FastMCP Framework Style
{'='*60}

Base URL: {{BASE_URL}}
Available Tools ({len(api_discovery.endpoints) + 4} total):
- Generic HTTP Methods (4): post_request, get_request, put_request, delete_request
- Endpoint-specific Tools ({len(api_discovery.endpoints)}):
{tool_summary}

All endpoint-specific tools are automatically generated with:
- Type-safe parameters based on API analysis
- Proper parameter source detection (path, query, header, body)
- Comprehensive error handling and response processing

Starting server with HTTP transport...
{'='*60}
""")
    
    # Run the server with HTTP transport
    mcp.run(transport="http", port=8000, host="0.0.0.0")'''

        logger.info(f"Generated FastMCP server code with {len(api_discovery.endpoints)} endpoints")
        return python_code

    
    def _generate_server_description(self, repo_name: str, api_discovery: APIDiscovery, production_base_url: str = None) -> str:
        """Generate comprehensive server description"""
        base_url = production_base_url or api_discovery.base_url or "API"
        return f"""MCP Server for {repo_name.replace('_', ' ').title()}
Generated automatically from GitHub repository analysis using enhanced parameter extraction.

This server provides Model Context Protocol (MCP) tools for interacting with the {repo_name} API.
Each endpoint has been analyzed to extract proper parameter types, sources, and validation rules.

FEATURES:
- Automatic parameter detection (path, query, header, cookie, form, body)
- Type-safe parameter handling with validation
- Comprehensive error handling and response processing
- FastMCP framework for optimal performance
- Production-ready with configurable base URL

BASE URL: {base_url}
ENDPOINTS: {len(api_discovery.endpoints)} API endpoints analyzed
TOOLS: {len(api_discovery.endpoints) + 4} total tools available

USAGE:
Each endpoint is available as both a specific tool (with parameter validation) and via generic HTTP methods.
Use specific tools for type safety, or generic methods for flexibility.

AUTHENTICATION:
Include authentication headers in the 'headers' parameter of any tool call.
Example: {{"Authorization": "Bearer your-token-here"}}

Generated with enhanced parameter extraction technology."""

    def _generate_tool_summary(self, endpoints) -> str:
        """Generate tool summary for the main section"""
        if not endpoints:
            return "    - No specific endpoints found"
        
        # Categorize endpoints by their first path segment
        categories = {}
        for endpoint in endpoints:
            path_parts = endpoint.url.strip('/').split('/')
            category = path_parts[0] if path_parts and path_parts[0] else 'general'
            category = category.replace('{', '').replace('}', '')
            if not category or category.startswith('api'):
                category = path_parts[1] if len(path_parts) > 1 else 'general'
            
            if category not in categories:
                categories[category] = []
            categories[category].append(endpoint)
        
        summary_lines = []
        for category, cat_endpoints in categories.items():
            category_name = category.replace('_', ' ').title()
            endpoint_methods = [ep.method.value for ep in cat_endpoints]
            method_counts = {}
            for method in endpoint_methods:
                method_counts[method] = method_counts.get(method, 0) + 1
            method_summary = ", ".join([f"{method}({count})" for method, count in method_counts.items()])
            summary_lines.append(f"    - {category_name}: {method_summary}")
        
        # Add some sample tool names
        sample_tools = []
        for endpoint in endpoints[:5]:  # Show first 5 as examples
            # Clean tool name - remove ALL invalid characters for Python function names
            tool_name = f"{endpoint.method.value.lower()}_{endpoint.url.replace('/', '_').replace('{', '').replace('}', '').replace('-', '_').replace(':', '_').replace('.', '_').replace('?', '_').replace('&', '_').replace('=', '_').replace('+', '_').replace('@', '_').replace('#', '_').replace('$', '_').replace('%', '_').replace('^', '_').replace('*', '_').replace('(', '_').replace(')', '_').replace('[', '_').replace(']', '_').replace('{', '_').replace('}', '_').replace('|', '_').replace('\\', '_').replace(';', '_').replace('"', '_').replace("'", '_').replace('<', '_').replace('>', '_').replace(',', '_').replace('!', '_').replace('~', '_').replace('`', '_')}"
            
            # Ensure the function name starts with a letter or underscore
            if tool_name and tool_name[0].isdigit():
                tool_name = f"endpoint_{tool_name}"
            
            # Remove any consecutive underscores and ensure no trailing underscore
            tool_name = re.sub(r'_+', '_', tool_name).rstrip('_')
            
            sample_tools.append(f"      • {tool_name}")
        
        if len(endpoints) > 5:
            sample_tools.append(f"      • ... and {len(endpoints) - 5} more endpoint-specific tools")
        
        summary_lines.append("    - Sample endpoint tools:")
        summary_lines.extend(sample_tools)
        
        return "\n".join(summary_lines)

    def _generate_fastmcp_tool(self, endpoint, production_base_url: str = None) -> str:
        """Generate FastMCP-style tool for an endpoint"""
        # Clean tool name - remove ALL invalid characters for Python function names
        # Python function names can only contain: letters, digits, underscores
        # Must start with a letter or underscore
        tool_name = f"{endpoint.method.value.lower()}_{endpoint.url.replace('/', '_').replace('{', '').replace('}', '').replace('-', '_').replace(':', '_').replace('.', '_').replace('?', '_').replace('&', '_').replace('=', '_').replace('+', '_').replace('@', '_').replace('#', '_').replace('$', '_').replace('%', '_').replace('^', '_').replace('*', '_').replace('(', '_').replace(')', '_').replace('[', '_').replace(']', '_').replace('{', '_').replace('}', '_').replace('|', '_').replace('\\', '_').replace(';', '_').replace('"', '_').replace("'", '_').replace('<', '_').replace('>', '_').replace(',', '_').replace('!', '_').replace('~', '_').replace('`', '_')}"
        
        # Ensure the function name starts with a letter or underscore
        if tool_name and tool_name[0].isdigit():
            tool_name = f"endpoint_{tool_name}"
        
        # Remove any consecutive underscores and ensure no trailing underscore
        tool_name = re.sub(r'_+', '_', tool_name).rstrip('_')
        
        # Generate comprehensive description
        description_lines = [
            f"{endpoint.method.value} request to {endpoint.url}",
            "",
            endpoint.description or f"Execute {endpoint.method.value} operation on {endpoint.url}",
            "",
            "Args:"
        ]
        
        # Add parameter documentation
        required_params = []
        optional_params = []
        
        if hasattr(endpoint, 'parameters') and endpoint.parameters:
            for param_name, param_info in endpoint.parameters.items():
                # Handle both dict and object parameter structures
                if isinstance(param_info, dict):
                    param_type = param_info.get('type', 'str')
                    param_source = param_info.get('source', 'unknown')
                    param_desc = param_info.get('description', f'{param_name} parameter')
                    required = param_info.get('required', True)
                else:
                    # Handle object-style parameters (ParameterInfo objects)
                    param_type = getattr(param_info, 'type', 'str')
                    param_source = getattr(param_info, 'source', 'unknown')
                    param_desc = getattr(param_info, 'description', f'{param_name} parameter')
                    required = getattr(param_info, 'required', True)
                
                # Convert enum values to strings if needed
                if hasattr(param_type, 'value'):
                    param_type = param_type.value
                if hasattr(param_source, 'value'):
                    param_source = param_source.value
                
                # Map parameter types
                python_type = {
                    'string': 'str', 'integer': 'int', 'boolean': 'bool',
                    'array': 'List[str]', 'object': 'Dict[str, Any]', 'float': 'float',
                    'unknown': 'str'  # Handle unknown types
                }.get(param_type, 'str')
                
                description_lines.append(f"        {param_name}: {python_type} - {param_desc} ({param_source} parameter)")
                
                # Separate required and optional parameters
                if required:
                    required_params.append(f"{param_name}: {python_type}")
                else:
                    optional_params.append(f"{param_name}: Optional[{python_type}] = None")
        
        # Combine parameters in correct order: required first, then optional
        func_params = required_params + optional_params
        
        description_lines.extend([
            "        headers: Optional headers for the request (e.g., {\"Authorization\": \"Bearer token\"})",
            "",
            "Returns:",
            "        Response data including status_code, data, success flag, and headers"
        ])
        
        func_params.append("headers: Dict[str, str] = None")
        func_signature = ", ".join(func_params)
        description = "\n    ".join(description_lines)
        
        # Generate URL construction
        if production_base_url:
            url_base = f'"{production_base_url.rstrip("/")}"'
        else:
            url_base = 'BASE_URL'
            
        # Build URL with path parameters
        url_template = endpoint.url
        if hasattr(endpoint, 'parameters') and endpoint.parameters:
            for param_name, param_info in endpoint.parameters.items():
                if param_info.get('source') == 'path':
                    url_template = url_template.replace(f'{{{param_name}}}', f'{{{param_name}}}')
        
        url_construction = f'url = f"{url_base}{url_template}"'
        
        # Generate data preparation for body parameters
        data_prep_lines = []
        if hasattr(endpoint, 'parameters') and endpoint.parameters:
            body_params = [name for name, info in endpoint.parameters.items() if info.get('source') == 'body']
            if body_params and endpoint.method.value in ['POST', 'PUT', 'PATCH']:
                body_dict = '{' + ', '.join([f'"{p}": {p}' for p in body_params]) + '}'
                data_prep_lines.extend([
                    f"data = {body_dict}",
                    "data = {k: v for k, v in data.items() if v is not None}"
                ])
        
        # Generate method call
        if data_prep_lines:
            method_call = f'return asyncio.run(make_request("{endpoint.method.value}", url, data, headers))'
        else:
            method_call = f'return asyncio.run(make_request("{endpoint.method.value}", url, None, headers))'
        
        # Combine everything with proper formatting
        tool_code_lines = [
            "",  # Empty line before each tool for readability
            "@mcp.tool",
            f"def {tool_name}({func_signature}) -> Dict[str, Any]:",
            '    """',
            f'    {description}',
            '    """',
            f'    {url_construction}'
        ]
        
        if data_prep_lines:
            for line in data_prep_lines:
                tool_code_lines.append(f'    {line}')
        
        tool_code_lines.append(f'    {method_call}')
        
        return "\n".join(tool_code_lines)

    
    def _generate_dockerfile(self, repo_name: str) -> str:
        """Generate Dockerfile content for FastMCP server"""
        return f'''# Dockerfile for FastMCP Server - {repo_name}
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the MCP server code
COPY . .

# Expose the port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV MCP_SERVER_PORT=8000

# Run the MCP server
CMD ["python", "-m", "mcp_server"]
'''

    def _generate_fastmcp_requirements(self) -> str:
        """Generate requirements.txt content for FastMCP server"""
        return '''# Requirements for FastMCP Server
# FastMCP framework (replaces standard MCP packages)
fastmcp>=0.9.0

# HTTP client for API calls
aiohttp>=3.8.0

# Async support
asyncio

# JSON handling
json5>=0.9.0

# Type checking
typing-extensions>=4.0.0

# Environment variables
python-dotenv>=1.0.0

# Data validation
pydantic>=2.0.0
'''

    def _save_mcp_content(self, repo_name: str, mcp_content: Dict[str, Any]):
        """Save MCP content to JSON file"""
        try:
            file_path = self.mcp_servers_dir / f"{repo_name}_mcp_server.json"
            
            # Save the complete content (but exclude the large code strings from JSON for size)
            json_content = {
                "repo_name": mcp_content["repo_name"],
                "github_url": mcp_content["github_url"],
                "generated_at": mcp_content["generated_at"],
                "endpoints_count": mcp_content["endpoints_count"],
                "tools_count": mcp_content["tools_count"],
                "production_base_url": mcp_content.get("production_base_url"),
                "framework": mcp_content.get("framework", "FastMCP")
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=2)
                
            logger.info(f"Saved FastMCP server content to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving MCP content: {e}")
    
    def get_mcp_content(self, repo_name: str) -> Dict[str, Any]:
        """Retrieve previously saved MCP content for a repository"""
        try:
            file_path = self.mcp_servers_dir / f"{repo_name}_mcp_server.json"
            
            if not file_path.exists():
                logger.info(f"No saved MCP content found for {repo_name}")
                return None
            
            # Load the saved metadata
            with open(file_path, 'r', encoding='utf-8') as f:
                saved_metadata = json.load(f)
            
            logger.info(f"Found saved MCP metadata for {repo_name}")
            
            # Return a basic structure that indicates content exists but needs regeneration
            # The main.py will detect this and call generate_mcp_server_content
            return {
                "repo_name": saved_metadata.get("repo_name", repo_name),
                "github_url": saved_metadata.get("github_url", ""),
                "generated_at": saved_metadata.get("generated_at", ""),
                "endpoints_count": saved_metadata.get("endpoints_count", 0),
                "tools_count": saved_metadata.get("tools_count", 0),
                "production_base_url": saved_metadata.get("production_base_url"),
                "framework": saved_metadata.get("framework", "FastMCP"),
                # Indicate that full content needs regeneration
                "needs_regeneration": True
            }
            
        except Exception as e:
            logger.error(f"Error retrieving MCP content for {repo_name}: {e}")
            return None
    
    def generate_mcp_server_content_from_pdf(self, pdf_filename: str, api_discovery: APIDiscovery, production_base_url: str = None) -> Dict[str, Any]:
        """Generate MCP server Python code and Dockerfile content from PDF API documentation"""
        try:
            # Extract a clean name from the PDF filename for the server
            pdf_name = Path(pdf_filename).stem
            # Clean the name to make it suitable for Python/server naming
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', pdf_name).lower()
            server_name = f"pdf_{clean_name}"
            
            # Generate Python code in FastMCP style
            python_code = self._generate_fastmcp_python_code_for_pdf(server_name, pdf_filename, api_discovery, production_base_url)
            
            # Generate Dockerfile
            dockerfile_content = self._generate_dockerfile_for_pdf(server_name)
            
            # Generate requirements.txt for FastMCP
            requirements_txt_content = self._generate_fastmcp_requirements()
            
            # Create content dictionary
            mcp_content = {
                "repo_name": server_name,
                "source_file": pdf_filename,
                "python_code": python_code,
                "dockerfile_content": dockerfile_content,
                "requirements_txt_content": requirements_txt_content,
                "generated_at": datetime.now().isoformat(),
                "endpoints_count": len(api_discovery.endpoints),
                "tools_count": len(api_discovery.endpoints) + 4,  # +4 for generic HTTP methods
                "production_base_url": production_base_url,
                "framework": "FastMCP",
                "source_type": "PDF"
            }
            
            # Save to file
            self._save_mcp_content(server_name, mcp_content)
            
            logger.info(f"Generated FastMCP server from PDF with {mcp_content['tools_count']} tools")
            return mcp_content
            
        except Exception as e:
            logger.error(f"Error generating MCP server content from PDF: {e}")
            raise e

    def _generate_fastmcp_python_code_for_pdf(self, server_name: str, pdf_filename: str, api_discovery: APIDiscovery, production_base_url: str = None) -> str:
        """Generate Python code for MCP server from PDF in FastMCP style"""
        logger.info(f"Generating FastMCP-style code for PDF {pdf_filename} with {len(api_discovery.endpoints)} endpoints")
        
        # Generate server description
        server_description = self._generate_server_description_for_pdf(server_name, pdf_filename, api_discovery, production_base_url)
        
        # Generate endpoint-specific tools
        endpoint_tools = []
        for endpoint in api_discovery.endpoints:
            tool_code = self._generate_fastmcp_tool(endpoint, production_base_url)
            endpoint_tools.append(tool_code)
        
        # Generate tool summary for main section
        tool_summary = self._generate_tool_summary(api_discovery.endpoints)
        
        # Use the production base URL or fallback to API discovery base URL
        base_url = production_base_url if production_base_url else (api_discovery.base_url or 'https://api.example.com')
        if base_url.startswith('pdf://'):
            base_url = 'https://api.example.com'  # Replace PDF URL with placeholder
        
        python_code = f'''#!/usr/bin/env python3
"""
{server_description}
"""

from fastmcp import FastMCP
import aiohttp
import asyncio
import json
from typing import Dict, List, Optional, Any

# Initialize the MCP server with FastMCP framework
mcp = FastMCP(name="{server_name.replace('_', ' ').title()} MCP Server")

# Base URL for the API
BASE_URL = "{base_url}"

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
                    return {{
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }}
            elif method.upper() == "POST":
                async with session.post(url, json=data, headers=headers) as response:
                    return {{
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }}
            elif method.upper() == "PUT":
                async with session.put(url, json=data, headers=headers) as response:
                    return {{
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }}
            elif method.upper() == "DELETE":
                async with session.delete(url, headers=headers) as response:
                    return {{
                        "status_code": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text(),
                        "success": 200 <= response.status < 300,
                        "headers": dict(response.headers)
                    }}
            else:
                return {{
                    "status_code": 405,
                    "data": f"Unsupported method: {{method}}",
                    "success": False
                }}
        except Exception as e:
            return {{
                "status_code": 500,
                "data": f"Request failed: {{str(e)}}",
                "success": False,
                "error": str(e)
            }}

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
        headers: Optional headers for the request (e.g., {{"Authorization": "Bearer token"}})
        
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
        headers: Optional headers for the request (e.g., {{"Authorization": "Bearer token"}})
        
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
        headers: Optional headers for the request (e.g., {{"Authorization": "Bearer token"}})
        
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
        headers: Optional headers for the request (e.g., {{"Authorization": "Bearer token"}})
        
    Returns:
        Response data including status_code, data, and success flag
    """
    return asyncio.run(make_request("DELETE", url, None, headers))

# Endpoint-specific tools generated from PDF API documentation
# Total endpoint-specific tools: {len(api_discovery.endpoints)}
{"\n".join(endpoint_tools) if endpoint_tools else "# No endpoint-specific tools generated"}

if __name__ == "__main__":
    print(f"""
{'='*60}
{server_name.replace('_', ' ').title()} MCP Server
Generated from PDF API Documentation: {pdf_filename}
Using FastMCP Framework Style
{'='*60}

Base URL: {{BASE_URL}}
Available Tools ({len(api_discovery.endpoints) + 4} total):
- Generic HTTP Methods (4): post_request, get_request, put_request, delete_request
- Endpoint-specific Tools ({len(api_discovery.endpoints)}):
{tool_summary}

All endpoint-specific tools are automatically generated with:
- Type-safe parameters based on PDF API documentation analysis
- Proper parameter source detection (path, query, header, body)
- Comprehensive error handling and response processing

Starting server with HTTP transport...
{'='*60}
""")
    
    # Run the server with HTTP transport
    mcp.run(transport="http", port=8000, host="0.0.0.0")'''

        logger.info(f"Generated FastMCP server code from PDF with {len(api_discovery.endpoints)} endpoints")
        return python_code

    def _generate_server_description_for_pdf(self, server_name: str, pdf_filename: str, api_discovery: APIDiscovery, production_base_url: str = None) -> str:
        """Generate comprehensive server description for PDF-generated server"""
        base_url = production_base_url or "API"
        if base_url.startswith('pdf://'):
            base_url = "API"
        
        return f"""MCP Server for {server_name.replace('_', ' ').title()}
Generated automatically from PDF API documentation: {pdf_filename}
Using enhanced parameter extraction from PDF content.

This server provides Model Context Protocol (MCP) tools for interacting with the API documented in the PDF.
Each endpoint has been analyzed and extracted from the PDF to create proper parameter types, sources, and validation rules.

FEATURES:
- Automatic parameter detection from PDF documentation (path, query, header, cookie, form, body)
- Type-safe parameter handling with validation
- Comprehensive error handling and response processing
- FastMCP framework for optimal performance
- Production-ready with configurable base URL

SOURCE: {pdf_filename}
BASE URL: {base_url}
ENDPOINTS: {len(api_discovery.endpoints)} API endpoints extracted from PDF
TOOLS: {len(api_discovery.endpoints) + 4} total tools available

USAGE:
Each endpoint is available as both a specific tool (with parameter validation) and via generic HTTP methods.
Use specific tools for type safety, or generic methods for flexibility.

AUTHENTICATION:
Include authentication headers in the 'headers' parameter of any tool call.
Example: {{"Authorization": "Bearer your-token-here"}}

Generated with enhanced PDF API documentation extraction technology."""

    def _generate_dockerfile_for_pdf(self, server_name: str) -> str:
        """Generate Dockerfile content for PDF-generated FastMCP server"""
        return f'''# Dockerfile for FastMCP Server - {server_name} (Generated from PDF)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the MCP server code
COPY . .

# Expose the port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV MCP_SERVER_PORT=8000

# Run the MCP server
CMD ["python", "-m", "mcp_server"]
'''

    def list_mcp_servers(self) -> List[Dict[str, Any]]:
        """List all available MCP servers"""
        try:
            servers = []
            
            # Scan the MCP servers directory for saved content
            for file_path in self.mcp_servers_dir.glob("*_mcp_server.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        server_info = json.load(f)
                    servers.append(server_info)
                except Exception as e:
                    logger.error(f"Error reading MCP server file {file_path}: {e}")
                    continue
            
            logger.info(f"Found {len(servers)} MCP servers")
            return servers
            
        except Exception as e:
            logger.error(f"Error listing MCP servers: {e}")
            return []
