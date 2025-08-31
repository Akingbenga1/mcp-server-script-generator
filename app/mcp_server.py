import json
import logging
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

from .models import APIDiscovery, MCPTool, HTTPMethod

logger = logging.getLogger(__name__)

class MCPServer:
    def __init__(self):
        pass
    
    async def generate_tools(self, api_discovery: APIDiscovery, production_base_url: str = None) -> List[MCPTool]:
        """Generate MCP tools from discovered API endpoints"""
        logger.info(f"Generating MCP tools for {len(api_discovery.endpoints)} endpoints")
        if production_base_url:
            logger.info(f"Using production base URL: {production_base_url}")
        
        tools = []
        
        # Generate tools directly from discovered endpoints
        endpoint_tools = await self._generate_endpoint_tools(api_discovery)
        tools.extend(endpoint_tools)
        
        logger.info(f"Generated {len(tools)} MCP tools from discovered endpoints")
        return tools
    
    async def _generate_endpoint_tools(self, api_discovery: APIDiscovery) -> List[MCPTool]:
        """Generate MCP tools directly from discovered API endpoints"""
        tools = []
        
        for endpoint in api_discovery.endpoints:
            # Generate a unique tool name based on the endpoint
            tool_name = self._generate_tool_name(endpoint)
            tool_description = self._generate_tool_description(endpoint)
            tool_category = self._determine_tool_category(endpoint)
            
            # Generate parameters based on the endpoint
            parameters = self._generate_tool_parameters(endpoint)
            
            tool = MCPTool(
                name=tool_name,
                description=tool_description,
                parameters=parameters,
                endpoint_url=endpoint.url,
                method=endpoint.method,
                authentication_required=endpoint.authentication_required,
                category=tool_category
            )
            tools.append(tool)
            
            logger.info(f"Generated tool: {tool_name} - {tool_description} - {endpoint.method.value} {endpoint.url}")
        
        return tools
    

    

    

    

    
    def _determine_tool_category(self, endpoint) -> str:
        """Determine the category of a tool based on endpoint URL and method"""
        url_lower = endpoint.url.lower()
        method = endpoint.method
        
        # Authentication category
        if any(keyword in url_lower for keyword in ['login', 'signin', 'auth', 'register', 'signup', 'logout', 'password']):
            return 'authentication'
        
        # Appointment category
        if any(keyword in url_lower for keyword in ['appointment', 'booking', 'schedule']):
            return 'appointments'
        
        # Profile category
        if any(keyword in url_lower for keyword in ['profile', 'user', 'account']):
            return 'profile'
        
        # Search category
        if any(keyword in url_lower for keyword in ['search', 'find', 'query']):
            return 'search'
        
        # Data management category
        if any(keyword in url_lower for keyword in ['create', 'update', 'delete', 'list', 'get']):
            return 'data_management'
        
        # Default category
        return 'general'
    
    def _generate_tool_name(self, endpoint) -> str:
        """Generate a tool name from endpoint URL"""
        url_parts = [part for part in endpoint.url.split('/') if part]  # Remove empty parts
        
        # Get the last meaningful part
        if not url_parts:
            last_part = 'api'
        elif len(url_parts) == 1:
            last_part = url_parts[0]
        else:
            # Use last part if it's not empty, otherwise use second to last
            last_part = url_parts[-1] if url_parts[-1] else url_parts[-2] if len(url_parts) >= 2 else url_parts[0]
        
        # Convert to snake_case
        name = re.sub(r'[^a-zA-Z0-9]', '_', last_part.lower())
        name = re.sub(r'_+', '_', name).strip('_')
        
        # Add method prefix
        method_prefix = endpoint.method.lower()
        return f"{method_prefix}_{name}"
    
    def _generate_tool_description(self, endpoint) -> str:
        """Generate a tool description from endpoint"""
        if endpoint.description:
            return endpoint.description
        
        url_parts = [part for part in endpoint.url.split('/') if part]  # Remove empty parts
        
        # Get the last meaningful part safely
        if not url_parts:
            last_part = 'api'
        elif len(url_parts) == 1:
            last_part = url_parts[0]
        else:
            # Use last part if it's not empty, otherwise use second to last
            last_part = url_parts[-1] if url_parts[-1] else url_parts[-2] if len(url_parts) >= 2 else url_parts[0]
        
        method = endpoint.method.lower()
        return f"{method.title()} operation for {last_part.replace('_', ' ')}"
    
    def _generate_tool_parameters(self, endpoint) -> Dict[str, Any]:
        """Generate tool parameters from endpoint"""
        if endpoint.parameters:
            return {
                'type': 'object',
                'properties': endpoint.parameters,
                'required': [name for name, param in endpoint.parameters.items() if param.get('required', False)]
            }
        
        if endpoint.request_body:
            return {
                'type': 'object',
                'properties': endpoint.request_body.get('properties', {}),
                'required': endpoint.request_body.get('required', [])
            }
        
        # Default empty parameters
        return {
            'type': 'object',
            'properties': {},
            'required': []
        }
    
    def get_tool_schema(self, tools: List[MCPTool]) -> Dict[str, Any]:
        """Generate MCP tool schema for the server"""
        tool_schemas = {}
        
        for tool in tools:
            tool_schemas[tool.name] = {
                'description': tool.description,
                'inputSchema': tool.parameters,
                'category': tool.category
            }
        
        return {
            'tools': tool_schemas,
            'version': '1.0.0',
            'generated_at': datetime.now().isoformat()
        }
