"""
Markdown API Documentation Parser
"""

import re
import json
from typing import List, Dict, Any
from .base_parser import BaseAPIParser
from app.models import APIEndpoint, HTTPMethod

class MarkdownAPIParser(BaseAPIParser):
    """Markdown API documentation parser"""
    
    async def parse_endpoints(self, text: str) -> List[APIEndpoint]:
        """Parse markdown API documentation"""
        endpoints = []
        
        # Parse markdown API documentation
        lines = text.split('\n')
        current_endpoint = None
        current_parameters = []
        
        for i, line in enumerate(lines):
            # Look for endpoint headers
            if line.startswith('## ') and any(method in line.upper() for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']):
                if current_endpoint:
                    # Add parameters to previous endpoint
                    if current_parameters:
                        current_endpoint.parameters = current_parameters
                    endpoints.append(current_endpoint)
                
                # Extract method and path
                method_match = re.search(r'(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)', line, re.IGNORECASE)
                if method_match:
                    method = method_match.group(1).upper()
                    path = method_match.group(2)
                    description = line.replace(f'## {method} {path}', '').strip()
                    
                    # Clean up path
                    if not path.startswith('/'):
                        path = '/' + path
                    
                    current_endpoint = APIEndpoint(
                        url=path,
                        method=HTTPMethod(method),
                        description=description,
                        parameters={},
                        request_body={},
                        response_schema={},
                        authentication_required=False,
                        tags=[]
                    )
                    current_parameters = []
            
            # Parse parameters
            elif current_endpoint and line.strip().startswith('- **'):
                param_match = re.search(r'- \*\*([^:]+):\*\*\s*(.+)', line)
                if param_match:
                    param_name = param_match.group(1).strip()
                    param_desc = param_match.group(2).strip()
                    current_parameters.append({
                        'name': param_name,
                        'description': param_desc,
                        'required': 'required' in param_desc.lower(),
                        'type': 'string'  # Default type
                    })
            
            # Parse request body
            elif current_endpoint and 'request body' in line.lower():
                # Look for JSON examples in next few lines
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip().startswith('```json'):
                        json_content = []
                        k = j + 1
                        while k < len(lines) and not lines[k].strip().endswith('```'):
                            json_content.append(lines[k])
                            k += 1
                        try:
                            current_endpoint.request_body = json.loads('\n'.join(json_content))
                        except json.JSONDecodeError:
                            pass
                        break
            
            # Parse response schema
            elif current_endpoint and 'response' in line.lower():
                # Look for JSON examples in next few lines
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].strip().startswith('```json'):
                        json_content = []
                        k = j + 1
                        while k < len(lines) and not lines[k].strip().endswith('```'):
                            json_content.append(lines[k])
                            k += 1
                        try:
                            current_endpoint.response_schema = json.loads('\n'.join(json_content))
                        except json.JSONDecodeError:
                            pass
                        break
        
        # Add the last endpoint
        if current_endpoint:
            if current_parameters:
                current_endpoint.parameters = current_parameters
            endpoints.append(current_endpoint)
        
        return endpoints
    
    async def parse_schema(self, text: str) -> Dict[str, Any]:
        """Parse schema from markdown content"""
        # Extract code blocks that might contain schema
        code_blocks = re.findall(r'```(?:json|yaml)\s*\n(.*?)\n```', text, re.DOTALL)
        for block in code_blocks:
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                continue
        return {}
    
    async def parse_authentication(self, text: str) -> Dict[str, Any]:
        """Parse authentication information from markdown content"""
        auth_info = {}
        
        # Look for authentication sections
        auth_patterns = [
            r'##\s*Authentication\s*\n(.*?)(?=\n##|\Z)',
            r'###\s*Authentication\s*\n(.*?)(?=\n###|\Z)',
            r'Authorization:\s*(Bearer|Basic|API-Key)\s+([^\s]+)',
            r'X-API-Key:\s*([^\s]+)'
        ]
        
        for pattern in auth_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    auth_info['type'] = match[0].lower()
                    auth_info['key'] = match[1]
                elif isinstance(match, str):
                    auth_info['description'] = match.strip()
        
        return auth_info
