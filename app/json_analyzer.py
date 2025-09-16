#!/usr/bin/env python3
"""
JSON Analyzer for extracting API specifications from JSON files.
This module parses JSON files containing API documentation in various formats
(OpenAPI/Swagger, Postman Collections, custom formats) and converts them into structured data
that can be used to generate MCP server files.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from .models import APIDiscovery, APIEndpoint, HTTPMethod, AuthType, AuthenticationInfo

logger = logging.getLogger(__name__)

class JSONAnalyzer:
    """Analyzes JSON files to extract API specifications and convert to structured format"""
    
    def __init__(self):
        logger.info("JSON Analyzer initialized")
    
    async def analyze_json(self, json_content: bytes, filename: str = "api_spec.json") -> APIDiscovery:
        """
        Main method to analyze JSON and extract API specifications
        
        Args:
            json_content: Raw JSON file content as bytes
            filename: Name of the JSON file
            
        Returns:
            APIDiscovery object with extracted endpoints and documentation
        """
        logger.info(f"Starting JSON analysis for file: {filename}")
        
        try:
            # Parse JSON content
            json_data = json.loads(json_content.decode('utf-8'))
            
            logger.info(f"Successfully parsed JSON with {len(str(json_data))} characters")
            
            # Detect the JSON format and extract API specification
            api_spec_format = self._detect_json_format(json_data)
            logger.info(f"Detected JSON format: {api_spec_format}")
            
            # Extract API endpoints based on the detected format
            if api_spec_format == "openapi":
                api_discovery = await self._parse_openapi_spec(json_data, filename)
            elif api_spec_format == "swagger":
                api_discovery = await self._parse_swagger_spec(json_data, filename)
            elif api_spec_format == "postman":
                api_discovery = await self._parse_postman_collection(json_data, filename)
            elif api_spec_format == "insomnia":
                api_discovery = await self._parse_insomnia_collection(json_data, filename)
            elif api_spec_format == "custom_endpoints":
                api_discovery = await self._parse_custom_endpoints(json_data, filename)
            else:
                # Try generic parsing as fallback
                api_discovery = await self._parse_generic_json(json_data, filename)
            
            logger.info(f"JSON analysis completed: found {len(api_discovery.endpoints)} endpoints")
            return api_discovery
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in {filename}: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"Error analyzing JSON {filename}: {e}")
            raise e
    
    def _detect_json_format(self, json_data: Dict[str, Any]) -> str:
        """Detect the format of the JSON API specification"""
        
        # Check for OpenAPI 3.x
        if "openapi" in json_data and json_data.get("openapi", "").startswith("3."):
            return "openapi"
        
        # Check for Swagger 2.0
        if "swagger" in json_data and json_data.get("swagger") == "2.0":
            return "swagger"
        
        # Check for Postman collection
        if "info" in json_data and "item" in json_data and json_data.get("info", {}).get("schema"):
            return "postman"
        
        # Check for Insomnia collection
        if "resources" in json_data and isinstance(json_data["resources"], list):
            return "insomnia"
        
        # Check for custom endpoints format
        if "endpoints" in json_data or "apis" in json_data or "routes" in json_data:
            return "custom_endpoints"
        
        # Check if it looks like a direct API endpoint list
        if isinstance(json_data, list) and len(json_data) > 0:
            first_item = json_data[0]
            if isinstance(first_item, dict) and ("path" in first_item or "url" in first_item or "method" in first_item):
                return "custom_endpoints"
        
        return "generic"
    
    async def _parse_openapi_spec(self, json_data: Dict[str, Any], filename: str) -> APIDiscovery:
        """Parse OpenAPI 3.x specification"""
        logger.info("Parsing OpenAPI 3.x specification")
        
        # Extract base URL
        base_url = "https://api.example.com"
        if "servers" in json_data and json_data["servers"]:
            base_url = json_data["servers"][0].get("url", base_url)
        
        # Extract endpoints
        endpoints = []
        paths = json_data.get("paths", {})
        
        for path, path_data in paths.items():
            if not isinstance(path_data, dict):
                continue
                
            for method, method_data in path_data.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
                    continue
                
                try:
                    http_method = HTTPMethod(method.upper())
                except ValueError:
                    continue
                
                # Extract endpoint information
                description = method_data.get("summary", method_data.get("description", ""))
                
                # Extract parameters
                parameters = self._extract_openapi_parameters(method_data, path)
                
                # Extract tags
                tags = method_data.get("tags", [])
                
                endpoint = APIEndpoint(
                    url=path,
                    method=http_method,
                    description=description,
                    parameters=parameters,
                    tags=tags
                )
                endpoints.append(endpoint)
        
        # Extract authentication info
        auth_info = self._extract_openapi_auth(json_data)
        
        # Extract schemas
        schemas = json_data.get("components", {}).get("schemas", {})
        
        return APIDiscovery(
            base_url=base_url,
            endpoints=endpoints,
            authentication=auth_info,
            schemas=schemas,
            openapi_specs=[json_data]
        )
    
    async def _parse_swagger_spec(self, json_data: Dict[str, Any], filename: str) -> APIDiscovery:
        """Parse Swagger 2.0 specification"""
        logger.info("Parsing Swagger 2.0 specification")
        
        # Extract base URL
        host = json_data.get("host", "api.example.com")
        schemes = json_data.get("schemes", ["https"])
        base_path = json_data.get("basePath", "")
        base_url = f"{schemes[0]}://{host}{base_path}"
        
        # Extract endpoints
        endpoints = []
        paths = json_data.get("paths", {})
        
        for path, path_data in paths.items():
            if not isinstance(path_data, dict):
                continue
                
            for method, method_data in path_data.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
                    continue
                
                try:
                    http_method = HTTPMethod(method.upper())
                except ValueError:
                    continue
                
                # Extract endpoint information
                description = method_data.get("summary", method_data.get("description", ""))
                
                # Extract parameters
                parameters = self._extract_swagger_parameters(method_data, path)
                
                # Extract tags
                tags = method_data.get("tags", [])
                
                endpoint = APIEndpoint(
                    url=path,
                    method=http_method,
                    description=description,
                    parameters=parameters,
                    tags=tags
                )
                endpoints.append(endpoint)
        
        # Extract authentication info
        auth_info = self._extract_swagger_auth(json_data)
        
        # Extract schemas
        schemas = json_data.get("definitions", {})
        
        return APIDiscovery(
            base_url=base_url,
            endpoints=endpoints,
            authentication=auth_info,
            schemas=schemas,
            openapi_specs=[json_data]
        )
    
    async def _parse_postman_collection(self, json_data: Dict[str, Any], filename: str) -> APIDiscovery:
        """Parse Postman collection"""
        logger.info("Parsing Postman collection")
        
        endpoints = []
        base_url = "https://api.example.com"
        
        # Extract base URL from variables if available
        variables = json_data.get("variable", [])
        for var in variables:
            if var.get("key") in ["baseUrl", "host", "base_url"]:
                base_url = var.get("value", base_url)
                break
        
        # Parse items recursively
        items = json_data.get("item", [])
        self._parse_postman_items(items, endpoints, "")
        
        # Extract authentication info
        auth_info = self._extract_postman_auth(json_data)
        
        return APIDiscovery(
            base_url=base_url,
            endpoints=endpoints,
            authentication=auth_info,
            schemas={},
            openapi_specs=[]
        )
    
    def _parse_postman_items(self, items: List[Dict[str, Any]], endpoints: List[APIEndpoint], folder_path: str):
        """Recursively parse Postman collection items"""
        
        for item in items:
            if "item" in item:
                # This is a folder, recurse into it
                folder_name = item.get("name", "")
                new_folder_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
                self._parse_postman_items(item["item"], endpoints, new_folder_path)
            elif "request" in item:
                # This is a request
                request = item["request"]
                
                # Extract method
                method_str = request.get("method", "GET").upper()
                try:
                    http_method = HTTPMethod(method_str)
                except ValueError:
                    continue
                
                # Extract URL
                url_data = request.get("url", {})
                if isinstance(url_data, str):
                    url_path = url_data
                elif isinstance(url_data, dict):
                    path_parts = url_data.get("path", [])
                    url_path = "/" + "/".join(path_parts) if path_parts else "/"
                else:
                    url_path = "/"
                
                # Clean up URL path
                if not url_path.startswith("/"):
                    url_path = "/" + url_path
                
                # Extract description
                description = item.get("name", "") or request.get("description", "")
                
                # Extract parameters
                parameters = self._extract_postman_parameters(request, url_path)
                
                # Extract tags from folder path
                tags = [tag for tag in folder_path.split("/") if tag] if folder_path else []
                
                endpoint = APIEndpoint(
                    url=url_path,
                    method=http_method,
                    description=description,
                    parameters=parameters,
                    tags=tags
                )
                endpoints.append(endpoint)
    
    async def _parse_insomnia_collection(self, json_data: Dict[str, Any], filename: str) -> APIDiscovery:
        """Parse Insomnia collection"""
        logger.info("Parsing Insomnia collection")
        
        endpoints = []
        base_url = "https://api.example.com"
        
        resources = json_data.get("resources", [])
        
        for resource in resources:
            if resource.get("_type") == "request":
                # Extract method
                method_str = resource.get("method", "GET").upper()
                try:
                    http_method = HTTPMethod(method_str)
                except ValueError:
                    continue
                
                # Extract URL
                url = resource.get("url", "")
                if url.startswith("{{"):
                    # Handle Insomnia variables - extract the path part
                    url_parts = url.split("/")
                    url_path = "/" + "/".join([part for part in url_parts if not part.startswith("{{")])
                else:
                    url_path = url.replace("https://", "").replace("http://", "")
                    if "/" in url_path:
                        url_path = "/" + "/".join(url_path.split("/")[1:])
                    else:
                        url_path = "/"
                
                # Extract description
                description = resource.get("name", "") or resource.get("description", "")
                
                # Extract parameters
                parameters = self._extract_insomnia_parameters(resource, url_path)
                
                endpoint = APIEndpoint(
                    url=url_path,
                    method=http_method,
                    description=description,
                    parameters=parameters,
                    tags=[]
                )
                endpoints.append(endpoint)
        
        return APIDiscovery(
            base_url=base_url,
            endpoints=endpoints,
            authentication=None,
            schemas={},
            openapi_specs=[]
        )
    
    async def _parse_custom_endpoints(self, json_data: Dict[str, Any], filename: str) -> APIDiscovery:
        """Parse custom endpoint format"""
        logger.info("Parsing custom endpoints format")
        
        endpoints = []
        
        # Handle different custom formats
        endpoint_data = []
        if isinstance(json_data, list):
            endpoint_data = json_data
        elif "endpoints" in json_data:
            endpoint_data = json_data["endpoints"]
        elif "apis" in json_data:
            endpoint_data = json_data["apis"]
        elif "routes" in json_data:
            endpoint_data = json_data["routes"]
        
        for item in endpoint_data:
            if not isinstance(item, dict):
                continue
            
            # Extract method
            method_str = item.get("method", item.get("httpMethod", "GET")).upper()
            try:
                http_method = HTTPMethod(method_str)
            except ValueError:
                continue
            
            # Extract URL/path
            url_path = item.get("path", item.get("url", item.get("route", "/")))
            if not url_path.startswith("/"):
                url_path = "/" + url_path
            
            # Extract description
            description = item.get("description", item.get("summary", item.get("name", "")))
            
            # Extract parameters
            parameters = self._extract_custom_parameters(item)
            
            # Extract tags
            tags = item.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            
            endpoint = APIEndpoint(
                url=url_path,
                method=http_method,
                description=description,
                parameters=parameters,
                tags=tags
            )
            endpoints.append(endpoint)
        
        # Extract base URL
        base_url = json_data.get("baseUrl", json_data.get("host", "https://api.example.com"))
        
        # Extract authentication
        auth_info = None
        if "auth" in json_data or "authentication" in json_data:
            auth_data = json_data.get("auth", json_data.get("authentication", {}))
            auth_info = self._parse_custom_auth(auth_data)
        
        return APIDiscovery(
            base_url=base_url,
            endpoints=endpoints,
            authentication=auth_info,
            schemas=json_data.get("schemas", {}),
            openapi_specs=[]
        )
    
    async def _parse_generic_json(self, json_data: Dict[str, Any], filename: str) -> APIDiscovery:
        """Parse generic JSON format as fallback"""
        logger.info("Parsing generic JSON format")
        
        endpoints = []
        base_url = "https://api.example.com"
        
        # Try to find endpoint-like structures anywhere in the JSON
        self._extract_endpoints_recursively(json_data, endpoints)
        
        return APIDiscovery(
            base_url=base_url,
            endpoints=endpoints,
            authentication=None,
            schemas={},
            openapi_specs=[]
        )
    
    def _extract_endpoints_recursively(self, data: Any, endpoints: List[APIEndpoint], path_prefix: str = ""):
        """Recursively search for endpoint-like structures in JSON"""
        
        if isinstance(data, dict):
            # Check if this looks like an endpoint definition
            if self._looks_like_endpoint(data):
                endpoint = self._create_endpoint_from_dict(data, path_prefix)
                if endpoint:
                    endpoints.append(endpoint)
            else:
                # Recurse into the dictionary
                for key, value in data.items():
                    new_prefix = f"{path_prefix}/{key}" if path_prefix else key
                    self._extract_endpoints_recursively(value, endpoints, new_prefix)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._extract_endpoints_recursively(item, endpoints, path_prefix)
    
    def _looks_like_endpoint(self, data: Dict[str, Any]) -> bool:
        """Check if a dictionary looks like an endpoint definition"""
        
        # Check for common endpoint indicators
        endpoint_indicators = ["method", "path", "url", "route", "endpoint"]
        method_indicators = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        
        # Has method and path/url
        if any(key in data for key in endpoint_indicators):
            method_value = data.get("method", "")
            if isinstance(method_value, str) and method_value.upper() in method_indicators:
                return True
        
        # Check if keys themselves are HTTP methods
        if any(key.upper() in method_indicators for key in data.keys()):
            return True
        
        return False
    
    def _create_endpoint_from_dict(self, data: Dict[str, Any], path_prefix: str = "") -> Optional[APIEndpoint]:
        """Create an APIEndpoint from a dictionary"""
        
        try:
            # Extract method
            method_str = data.get("method", "GET")
            if not isinstance(method_str, str):
                return None
            
            try:
                http_method = HTTPMethod(method_str.upper())
            except ValueError:
                return None
            
            # Extract path
            path = data.get("path", data.get("url", data.get("route", f"/{path_prefix}")))
            if not path.startswith("/"):
                path = "/" + path
            
            # Extract description
            description = data.get("description", data.get("summary", ""))
            
            # Extract parameters
            parameters = self._extract_generic_parameters(data)
            
            # Extract tags
            tags = data.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            
            return APIEndpoint(
                url=path,
                method=http_method,
                description=description,
                parameters=parameters,
                tags=tags
            )
        
        except Exception as e:
            logger.debug(f"Failed to create endpoint from dict: {e}")
            return None
    
    def _extract_openapi_parameters(self, method_data: Dict[str, Any], path: str) -> Dict[str, Any]:
        """Extract parameters from OpenAPI method data"""
        
        parameters = {}
        
        # Extract from parameters array
        for param in method_data.get("parameters", []):
            param_name = param.get("name")
            if not param_name:
                continue
            
            param_type = param.get("schema", {}).get("type", "string")
            param_in = param.get("in", "query")
            required = param.get("required", False)
            description = param.get("description", f"{param_name} parameter")
            
            # Map OpenAPI 'in' to our source format
            source_map = {
                "query": "query",
                "path": "path", 
                "header": "header",
                "cookie": "header"
            }
            source = source_map.get(param_in, "query")
            
            parameters[param_name] = {
                "name": param_name,
                "type": param_type,
                "source": source,
                "required": required,
                "description": description
            }
        
        # Extract path parameters from URL pattern
        import re
        path_params = re.findall(r'\{([^}]+)\}', path)
        for param_name in path_params:
            if param_name not in parameters:
                parameters[param_name] = {
                    "name": param_name,
                    "type": "string",
                    "source": "path",
                    "required": True,
                    "description": f"{param_name} path parameter"
                }
        
        # Extract request body parameters
        if "requestBody" in method_data:
            request_body = method_data["requestBody"]
            content = request_body.get("content", {})
            for content_type, content_data in content.items():
                if "application/json" in content_type:
                    schema = content_data.get("schema", {})
                    properties = schema.get("properties", {})
                    for prop_name, prop_data in properties.items():
                        parameters[prop_name] = {
                            "name": prop_name,
                            "type": prop_data.get("type", "string"),
                            "source": "body",
                            "required": prop_name in schema.get("required", []),
                            "description": prop_data.get("description", f"{prop_name} body parameter")
                        }
        
        return parameters
    
    def _extract_swagger_parameters(self, method_data: Dict[str, Any], path: str) -> Dict[str, Any]:
        """Extract parameters from Swagger 2.0 method data"""
        
        parameters = {}
        
        # Extract from parameters array
        for param in method_data.get("parameters", []):
            param_name = param.get("name")
            if not param_name:
                continue
            
            param_type = param.get("type", "string")
            param_in = param.get("in", "query")
            required = param.get("required", False)
            description = param.get("description", f"{param_name} parameter")
            
            # Map Swagger 'in' to our source format
            source_map = {
                "query": "query",
                "path": "path",
                "header": "header",
                "formData": "body",
                "body": "body"
            }
            source = source_map.get(param_in, "query")
            
            parameters[param_name] = {
                "name": param_name,
                "type": param_type,
                "source": source,
                "required": required,
                "description": description
            }
        
        return parameters
    
    def _extract_postman_parameters(self, request: Dict[str, Any], url_path: str) -> Dict[str, Any]:
        """Extract parameters from Postman request"""
        
        parameters = {}
        
        # Extract query parameters
        url_data = request.get("url", {})
        if isinstance(url_data, dict):
            query_params = url_data.get("query", [])
            for param in query_params:
                if isinstance(param, dict):
                    param_name = param.get("key")
                    if param_name:
                        parameters[param_name] = {
                            "name": param_name,
                            "type": "string",
                            "source": "query",
                            "required": not param.get("disabled", False),
                            "description": param.get("description", f"{param_name} query parameter")
                        }
        
        # Extract path parameters
        import re
        path_params = re.findall(r':([a-zA-Z_][a-zA-Z0-9_]*)', url_path)
        for param_name in path_params:
            parameters[param_name] = {
                "name": param_name,
                "type": "string",
                "source": "path",
                "required": True,
                "description": f"{param_name} path parameter"
            }
        
        # Extract header parameters
        headers = request.get("header", [])
        for header in headers:
            if isinstance(header, dict):
                header_name = header.get("key")
                if header_name and header_name.lower() not in ["content-type", "accept"]:
                    parameters[header_name] = {
                        "name": header_name,
                        "type": "string",
                        "source": "header",
                        "required": not header.get("disabled", False),
                        "description": header.get("description", f"{header_name} header")
                    }
        
        # Extract body parameters
        body = request.get("body", {})
        if body.get("mode") == "raw":
            try:
                raw_body = body.get("raw", "")
                if raw_body:
                    body_data = json.loads(raw_body)
                    if isinstance(body_data, dict):
                        for key in body_data.keys():
                            parameters[key] = {
                                "name": key,
                                "type": "string",
                                "source": "body",
                                "required": True,
                                "description": f"{key} body parameter"
                            }
            except json.JSONDecodeError:
                pass
        
        return parameters
    
    def _extract_insomnia_parameters(self, resource: Dict[str, Any], url_path: str) -> Dict[str, Any]:
        """Extract parameters from Insomnia resource"""
        
        parameters = {}
        
        # Extract query parameters
        params = resource.get("parameters", [])
        for param in params:
            param_name = param.get("name")
            if param_name:
                parameters[param_name] = {
                    "name": param_name,
                    "type": "string",
                    "source": "query",
                    "required": not param.get("disabled", False),
                    "description": f"{param_name} query parameter"
                }
        
        # Extract path parameters
        import re
        path_params = re.findall(r'\{([^}]+)\}', url_path)
        for param_name in path_params:
            parameters[param_name] = {
                "name": param_name,
                "type": "string",
                "source": "path",
                "required": True,
                "description": f"{param_name} path parameter"
            }
        
        # Extract headers
        headers = resource.get("headers", [])
        for header in headers:
            header_name = header.get("name")
            if header_name and header_name.lower() not in ["content-type", "accept"]:
                parameters[header_name] = {
                    "name": header_name,
                    "type": "string",
                    "source": "header",
                    "required": not header.get("disabled", False),
                    "description": f"{header_name} header"
                }
        
        return parameters
    
    def _extract_custom_parameters(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from custom format"""
        
        parameters = {}
        
        # Extract from various parameter formats
        param_sources = ["parameters", "params", "args", "fields"]
        
        for source in param_sources:
            if source in item:
                param_data = item[source]
                if isinstance(param_data, dict):
                    for param_name, param_info in param_data.items():
                        if isinstance(param_info, dict):
                            parameters[param_name] = {
                                "name": param_name,
                                "type": param_info.get("type", "string"),
                                "source": param_info.get("in", param_info.get("source", "query")),
                                "required": param_info.get("required", False),
                                "description": param_info.get("description", f"{param_name} parameter")
                            }
                        else:
                            parameters[param_name] = {
                                "name": param_name,
                                "type": "string",
                                "source": "query",
                                "required": False,
                                "description": f"{param_name} parameter"
                            }
        
        return parameters
    
    def _extract_generic_parameters(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from generic format"""
        
        parameters = {}
        
        # Look for common parameter patterns
        param_keys = ["parameters", "params", "args", "query", "body", "headers"]
        
        for key in param_keys:
            if key in data:
                param_data = data[key]
                if isinstance(param_data, dict):
                    for param_name, param_value in param_data.items():
                        source = "query" if key in ["query", "params"] else key
                        if key == "headers":
                            source = "header"
                        elif key == "body":
                            source = "body"
                        
                        parameters[param_name] = {
                            "name": param_name,
                            "type": "string",
                            "source": source,
                            "required": False,
                            "description": f"{param_name} parameter"
                        }
        
        return parameters
    
    def _extract_openapi_auth(self, json_data: Dict[str, Any]) -> Optional[AuthenticationInfo]:
        """Extract authentication info from OpenAPI spec"""
        
        components = json_data.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        
        if not security_schemes:
            return None
        
        # Get the first security scheme
        scheme_name, scheme_data = next(iter(security_schemes.items()))
        scheme_type = scheme_data.get("type", "").lower()
        
        auth_type_map = {
            "apikey": AuthType.API_KEY,
            "http": AuthType.BEARER,
            "oauth2": AuthType.OAUTH,
            "openidconnect": AuthType.OAUTH
        }
        
        auth_type = auth_type_map.get(scheme_type, AuthType.BEARER)
        
        return AuthenticationInfo(
            type=auth_type,
            endpoints=[],
            parameters={"scheme": scheme_data},
            headers=None
        )
    
    def _extract_swagger_auth(self, json_data: Dict[str, Any]) -> Optional[AuthenticationInfo]:
        """Extract authentication info from Swagger spec"""
        
        security_definitions = json_data.get("securityDefinitions", {})
        
        if not security_definitions:
            return None
        
        # Get the first security definition
        scheme_name, scheme_data = next(iter(security_definitions.items()))
        scheme_type = scheme_data.get("type", "").lower()
        
        auth_type_map = {
            "apikey": AuthType.API_KEY,
            "basic": AuthType.BASIC,
            "oauth2": AuthType.OAUTH
        }
        
        auth_type = auth_type_map.get(scheme_type, AuthType.BEARER)
        
        return AuthenticationInfo(
            type=auth_type,
            endpoints=[],
            parameters={"scheme": scheme_data},
            headers=None
        )
    
    def _extract_postman_auth(self, json_data: Dict[str, Any]) -> Optional[AuthenticationInfo]:
        """Extract authentication info from Postman collection"""
        
        auth = json_data.get("auth", {})
        if not auth:
            return None
        
        auth_type_str = auth.get("type", "").lower()
        
        auth_type_map = {
            "bearer": AuthType.BEARER,
            "basic": AuthType.BASIC,
            "apikey": AuthType.API_KEY,
            "oauth2": AuthType.OAUTH
        }
        
        auth_type = auth_type_map.get(auth_type_str, AuthType.BEARER)
        
        return AuthenticationInfo(
            type=auth_type,
            endpoints=[],
            parameters=auth,
            headers=None
        )
    
    def _parse_custom_auth(self, auth_data: Dict[str, Any]) -> Optional[AuthenticationInfo]:
        """Parse custom authentication format"""
        
        auth_type_str = auth_data.get("type", "").lower()
        
        auth_type_map = {
            "bearer": AuthType.BEARER,
            "basic": AuthType.BASIC,
            "apikey": AuthType.API_KEY,
            "api_key": AuthType.API_KEY,
            "oauth": AuthType.OAUTH,
            "oauth2": AuthType.OAUTH
        }
        
        auth_type = auth_type_map.get(auth_type_str, AuthType.BEARER)
        
        return AuthenticationInfo(
            type=auth_type,
            endpoints=[],
            parameters=auth_data,
            headers=None
        )