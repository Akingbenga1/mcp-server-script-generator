"""
OpenAPI/Swagger API Parser
"""

import re
import json
from typing import List, Dict, Any
from .base_parser import BaseAPIParser
from app.models import APIEndpoint, HTTPMethod

class OpenAPIParser(BaseAPIParser):
    """OpenAPI/Swagger API documentation parser"""
    
    async def parse_endpoints(self, text: str) -> List[APIEndpoint]:
        """Parse OpenAPI/Swagger endpoints from text content"""
        endpoints = []
        
        # Look for OpenAPI/Swagger patterns in text
        patterns = [
            r'(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)\s*[-–—]\s*([^\n]+)',
            r'(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)\s*:\s*([^\n]+)',
            r'([^\s]+)\s+(GET|POST|PUT|DELETE|PATCH)\s*[-–—]\s*([^\n]+)',
            r'##\s*(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)\s*[-–—]\s*([^\n]+)',
            r'###\s*(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)\s*[-–—]\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2).strip()
                description = match.group(3).strip()
                
                # Clean up path
                if not path.startswith('/'):
                    path = '/' + path
                
                # Create endpoint
                endpoint = APIEndpoint(
                    url=path,
                    method=HTTPMethod(method),
                    description=description,
                    parameters={},
                    request_body={},
                    response_schema={},
                    authentication_required=False,
                    tags=[]
                )
                endpoints.append(endpoint)
        
        # Look for JSON/YAML OpenAPI specs
        json_patterns = [
            r'```(?:json|yaml)\s*\n(.*?)\n```',
            r'\{.*?"openapi".*?\}',
            r'swagger:\s*["\']?[\d.]+["\']?'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    spec = json.loads(match)
                    if 'paths' in spec:
                        for path, methods in spec['paths'].items():
                            for method, details in methods.items():
                                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                                    endpoint = APIEndpoint(
                                        url=path,
                                        method=HTTPMethod(method.upper()),
                                        description=details.get('summary', ''),
                                        parameters=details.get('parameters', {}),
                                        request_body=details.get('requestBody', {}),
                                        response_schema=details.get('responses', {}),
                                        authentication_required=details.get('security', False),
                                        tags=details.get('tags', [])
                                    )
                                    endpoints.append(endpoint)
                except json.JSONDecodeError:
                    continue
        
        return endpoints
    
    async def parse_schema(self, text: str) -> Dict[str, Any]:
        """Parse OpenAPI schema from text content"""
        # Extract JSON/YAML schema definitions
        schema_patterns = [
            r'```(?:json|yaml)\s*\n(.*?)\n```',
            r'\{.*?"openapi".*?\}',
            r'swagger:\s*["\']?[\d.]+["\']?'
        ]
        
        for pattern in schema_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        return {}
    
    async def parse_authentication(self, text: str) -> Dict[str, Any]:
        """Parse authentication information from text content"""
        auth_info = {}
        
        # Look for authentication patterns
        auth_patterns = [
            r'Authorization:\s*(Bearer|Basic|API-Key)\s+([^\s]+)',
            r'X-API-Key:\s*([^\s]+)',
            r'Authentication:\s*(Bearer|Basic|API-Key)',
            r'API Key:\s*([^\s]+)'
        ]
        
        for pattern in auth_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    auth_info['type'] = match[0].lower()
                    auth_info['key'] = match[1]
                else:
                    auth_info['type'] = match[0].lower()
        
        return auth_info
