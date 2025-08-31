import aiohttp
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
import re
from urllib.parse import urljoin, urlparse
import yaml

from .models import APIDiscovery, APIEndpoint, AuthenticationInfo, AuthType, HTTPMethod

logger = logging.getLogger(__name__)

class APIDiscoverer:
    def __init__(self):
        self.session = None
        self.common_api_paths = [
            '/api',
            '/api/v1',
            '/api/v2',
            '/rest',
            '/rest/v1',
            '/rest/v2',
            '/graphql',
            '/swagger',
            '/swagger-ui',
            '/docs',
            '/openapi',
            '/openapi.json',
            '/swagger.json'
        ]
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
        
    async def discover_apis(self, base_url: str, analysis) -> APIDiscovery:
        """Discover API endpoints from a website"""
        logger.info(f"Discovering APIs for {base_url}")
        logger.info(f"Analysis contains: {len(analysis.forms)} forms, {len(analysis.javascript_files)} JS files, {len(analysis.api_endpoints)} potential endpoints")
        
        endpoints = []
        authentication = None
        
        # Try to find OpenAPI/Swagger documentation
        logger.info("Searching for OpenAPI/Swagger documentation...")
        openapi_spec = await self._find_openapi_spec(base_url)
        if openapi_spec:
            logger.info("Found OpenAPI/Swagger specification")
            openapi_endpoints = await self._parse_openapi_spec(openapi_spec, base_url)
            endpoints.extend(openapi_endpoints)
            logger.info(f"Extracted {len(openapi_endpoints)} endpoints from OpenAPI spec")
            authentication = await self._extract_auth_from_openapi(openapi_spec)
        else:
            logger.info("No OpenAPI/Swagger documentation found")
        
        # Discover endpoints from forms
        logger.info("Discovering endpoints from forms...")
        form_endpoints = await self._discover_from_forms(analysis.forms, base_url)
        endpoints.extend(form_endpoints)
        logger.info(f"Found {len(form_endpoints)} endpoints from forms")
        
        # Try common API paths
        logger.info("Trying common API paths...")
        common_endpoints = await self._try_common_paths(base_url)
        endpoints.extend(common_endpoints)
        logger.info(f"Found {len(common_endpoints)} endpoints from common paths")
        
        # Discover from JavaScript files
        logger.info("Discovering endpoints from JavaScript files...")
        js_endpoints = await self._discover_from_javascript(analysis.javascript_files)
        endpoints.extend(js_endpoints)
        logger.info(f"Found {len(js_endpoints)} endpoints from JavaScript files")
        
        # Remove duplicates
        logger.info(f"Removing duplicates from {len(endpoints)} total endpoints...")
        unique_endpoints = self._deduplicate_endpoints(endpoints)
        logger.info(f"Final unique endpoints: {len(unique_endpoints)}")
        
        # Generate schemas from endpoints
        logger.info("Generating schemas from endpoints...")
        schemas = await self._generate_schemas(unique_endpoints)
        
        logger.info(f"API discovery completed. Found {len(unique_endpoints)} unique endpoints")
        return APIDiscovery(
            base_url=base_url,
            endpoints=unique_endpoints,
            authentication=authentication,
            schemas=schemas,
            openapi_spec=openapi_spec
        )
    
    async def _find_openapi_spec(self, base_url: str) -> Optional[Dict[str, Any]]:
        """Try to find OpenAPI/Swagger specification"""
        openapi_paths = [
            '/openapi.json',
            '/swagger.json',
            '/api-docs',
            '/docs/openapi.json',
            '/swagger/v1/swagger.json'
        ]
        
        logger.info(f"Searching for OpenAPI spec at {len(openapi_paths)} common paths")
        
        session = await self._get_session()
        for path in openapi_paths:
            try:
                url = urljoin(base_url, path)
                logger.debug(f"Trying OpenAPI path: {url}")
                async with session.get(url, timeout=5) as response:
                    logger.debug(f"Response status for {url}: {response.status}")
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        logger.debug(f"Content-Type for {url}: {content_type}")
                        if 'json' in content_type:
                            logger.info(f"Found JSON OpenAPI spec at: {url}")
                            return await response.json()
                        elif 'yaml' in content_type or 'yml' in content_type:
                            logger.info(f"Found YAML OpenAPI spec at: {url}")
                            text = await response.text()
                            return yaml.safe_load(text)
                        else:
                            logger.debug(f"Unexpected content type for {url}: {content_type}")
                    else:
                        logger.debug(f"Failed to fetch {url}, status: {response.status}")
            except Exception as e:
                logger.debug(f"Failed to fetch {path}: {e}")
                continue
        
        logger.info("No OpenAPI/Swagger specification found")
        return None
    
    async def _parse_openapi_spec(self, spec: Dict[str, Any], base_url: str) -> List[APIEndpoint]:
        """Parse OpenAPI specification into APIEndpoint objects"""
        endpoints = []
        
        if 'paths' not in spec:
            return endpoints
        
        for path, methods in spec['paths'].items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    endpoint = APIEndpoint(
                        url=urljoin(base_url, path),
                        method=HTTPMethod(method.upper()),
                        description=details.get('summary', details.get('description', '')),
                        parameters=self._extract_parameters(details),
                        request_body=self._extract_request_body(details),
                        response_schema=self._extract_response_schema(details),
                        authentication_required=self._has_auth_requirement(details),
                        tags=details.get('tags', [])
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_parameters(self, details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract parameters from OpenAPI endpoint details"""
        params = details.get('parameters', [])
        if not params:
            return None
        
        extracted = {}
        for param in params:
            name = param.get('name', '')
            if name:
                extracted[name] = {
                    'type': param.get('type', 'string'),
                    'required': param.get('required', False),
                    'description': param.get('description', ''),
                    'in': param.get('in', 'query')
                }
        
        return extracted
    
    def _extract_request_body(self, details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract request body schema from OpenAPI endpoint details"""
        request_body = details.get('requestBody', {})
        if not request_body:
            return None
        
        content = request_body.get('content', {})
        for content_type, schema_info in content.items():
            if 'application/json' in content_type:
                return schema_info.get('schema', {})
        
        return None
    
    def _extract_response_schema(self, details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract response schema from OpenAPI endpoint details"""
        responses = details.get('responses', {})
        for status_code, response in responses.items():
            if status_code.startswith('2'):  # Success responses
                content = response.get('content', {})
                for content_type, schema_info in content.items():
                    if 'application/json' in content_type:
                        return schema_info.get('schema', {})
        
        return None
    
    def _has_auth_requirement(self, details: Dict[str, Any]) -> bool:
        """Check if endpoint requires authentication"""
        security = details.get('security', [])
        return len(security) > 0
    
    async def _extract_auth_from_openapi(self, spec: Dict[str, Any]) -> Optional[AuthenticationInfo]:
        """Extract authentication information from OpenAPI spec"""
        components = spec.get('components', {})
        security_schemes = components.get('securitySchemes', {})
        
        if not security_schemes:
            return None
        
        # Find the first security scheme
        for scheme_name, scheme in security_schemes.items():
            scheme_type = scheme.get('type', '').lower()
            
            if scheme_type == 'http':
                auth_type = scheme.get('scheme', '').lower()
                if auth_type == 'bearer':
                    return AuthenticationInfo(
                        type=AuthType.BEARER,
                        parameters={'token': 'string'}
                    )
                elif auth_type == 'basic':
                    return AuthenticationInfo(
                        type=AuthType.BASIC,
                        parameters={'username': 'string', 'password': 'string'}
                    )
            elif scheme_type == 'apiKey':
                return AuthenticationInfo(
                    type=AuthType.API_KEY,
                    parameters={'api_key': 'string'},
                    headers={scheme.get('name', 'X-API-Key'): '{api_key}'}
                )
            elif scheme_type == 'oauth2':
                return AuthenticationInfo(
                    type=AuthType.OAUTH,
                    parameters={'client_id': 'string', 'client_secret': 'string'}
                )
        
        return None
    
    async def _discover_from_forms(self, forms: List[Dict[str, Any]], base_url: str) -> List[APIEndpoint]:
        """Discover API endpoints from HTML forms"""
        endpoints = []
        
        logger.info(f"Analyzing {len(forms)} forms for API endpoints")
        
        for i, form in enumerate(forms):
            action = form.get('action', '')
            method = form.get('method', 'GET').upper()
            
            logger.debug(f"Analyzing form {i+1}: action='{action}', method='{method}'")
            
            if action:
                # Determine if this looks like an API endpoint
                if self._looks_like_api(action):
                    full_url = urljoin(base_url, action)
                    logger.info(f"Found API-like form endpoint: {full_url}")
                    endpoint = APIEndpoint(
                        url=full_url,
                        method=HTTPMethod(method),
                        description=f"Form submission endpoint",
                        parameters=self._extract_form_parameters(form),
                        authentication_required=False,
                        tags=['form']
                    )
                    endpoints.append(endpoint)
                else:
                    logger.debug(f"Form action '{action}' doesn't look like an API endpoint")
            else:
                logger.debug(f"Form {i+1} has no action attribute")
        
        logger.info(f"Found {len(endpoints)} API endpoints from forms")
        return endpoints
    
    def _looks_like_api(self, url: str) -> bool:
        """Check if URL looks like an API endpoint"""
        api_indicators = ['api', 'rest', 'ajax', 'json', 'v1', 'v2', 'endpoint']
        url_lower = url.lower()
        
        for indicator in api_indicators:
            if indicator in url_lower:
                logger.debug(f"URL '{url}' matches API indicator: '{indicator}'")
                return True
        
        logger.debug(f"URL '{url}' doesn't match any API indicators")
        return False
    
    def _extract_form_parameters(self, form: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract parameters from form fields"""
        fields = form.get('fields', [])
        if not fields:
            return None
        
        parameters = {}
        for field in fields:
            name = field.get('name', '')
            if name:
                parameters[name] = {
                    'type': field.get('type', 'string'),
                    'required': field.get('required', False),
                    'description': field.get('placeholder', '')
                }
        
        return parameters
    
    async def _try_common_paths(self, base_url: str) -> List[APIEndpoint]:
        """Try common API paths to discover endpoints"""
        endpoints = []
        
        logger.info(f"Trying {len(self.common_api_paths)} common API paths")
        
        session = await self._get_session()
        for path in self.common_api_paths:
            try:
                url = urljoin(base_url, path)
                logger.debug(f"Trying common path: {url}")
                async with session.get(url, timeout=5) as response:
                    logger.debug(f"Response status for {url}: {response.status}")
                    if response.status == 200:
                        # This might be an API endpoint
                        logger.info(f"Found potential API endpoint at: {url}")
                        endpoint = APIEndpoint(
                            url=url,
                            method=HTTPMethod.GET,
                            description=f"Discovered API endpoint at {path}",
                            authentication_required=False,
                            tags=['discovered']
                        )
                        endpoints.append(endpoint)
                    else:
                        logger.debug(f"Path {url} returned status {response.status}")
            except Exception as e:
                logger.debug(f"Failed to check {path}: {e}")
                continue
        
        logger.info(f"Found {len(endpoints)} endpoints from common paths")
        return endpoints
    
    async def _discover_from_javascript(self, js_files: List[str]) -> List[APIEndpoint]:
        """Discover API endpoints from JavaScript files"""
        endpoints = []
        
        logger.info(f"Analyzing {min(len(js_files), 5)} JavaScript files for API endpoints")
        
        session = await self._get_session()
        for i, js_url in enumerate(js_files[:5]):  # Limit to first 5 JS files
            logger.debug(f"Analyzing JS file {i+1}: {js_url}")
            try:
                async with session.get(js_url, timeout=10) as response:
                    logger.debug(f"Response status for {js_url}: {response.status}")
                    if response.status == 200:
                        content = await response.text()
                        logger.debug(f"Fetched {len(content)} characters from {js_url}")
                        js_endpoints = self._extract_api_from_js(content, js_url)
                        endpoints.extend(js_endpoints)
                        logger.debug(f"Found {len(js_endpoints)} endpoints in {js_url}")
                    else:
                        logger.debug(f"Failed to fetch {js_url}, status: {response.status}")
            except Exception as e:
                logger.debug(f"Failed to analyze JS file {js_url}: {e}")
                continue
        
        logger.info(f"Found {len(endpoints)} API endpoints from JavaScript files")
        return endpoints
    
    def _extract_api_from_js(self, content: str, base_url: str) -> List[APIEndpoint]:
        """Extract API endpoints from JavaScript content with enhanced parameter analysis"""
        endpoints = []
        
        logger.debug(f"Extracting API endpoints from JavaScript content ({len(content)} characters)")
        
        try:
            # Try to use enhanced analyzer for better parameter extraction
            from .enhanced_analyzer_v2 import EnhancedAPIAnalyzerV2
            enhanced_analyzer = EnhancedAPIAnalyzerV2()
            
            # Create a temporary file path for analysis
            temp_file_path = "temp_js_file.js"
            enhanced_endpoints = enhanced_analyzer.analyze_file(temp_file_path, content)
            
            if enhanced_endpoints:
                # Convert enhanced endpoints to standard APIEndpoint format
                enhanced_api_endpoints = enhanced_analyzer.convert_to_api_endpoints(enhanced_endpoints)
                
                # Update URLs to be absolute
                for endpoint in enhanced_api_endpoints:
                    if not endpoint.url.startswith(('http://', 'https://')):
                        endpoint.url = urljoin(base_url, endpoint.url)
                
                endpoints.extend(enhanced_api_endpoints)
                logger.debug(f"Enhanced analysis found {len(enhanced_api_endpoints)} endpoints in JavaScript")
                return endpoints
                
        except Exception as e:
            logger.debug(f"Enhanced analysis failed for JavaScript content: {e}")
            logger.debug("Falling back to regex-based analysis")
        
        # Fallback to original regex-based analysis
        # Common patterns for API calls
        patterns = [
            r'fetch\([\'"`]([^\'"`]+)[\'"`]',
            r'\.ajax\([\'"`]([^\'"`]+)[\'"`]',
            r'axios\.(get|post|put|delete)\([\'"`]([^\'"`]+)[\'"`]',
            r'\.get\([\'"`]([^\'"`]+)[\'"`]',
            r'\.post\([\'"`]([^\'"`]+)[\'"`]',
            r'\.put\([\'"`]([^\'"`]+)[\'"`]',
            r'\.delete\([\'"`]([^\'"`]+)[\'"`]'
        ]
        
        logger.debug(f"Using {len(patterns)} regex patterns to find API calls")
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, content, re.IGNORECASE)
            logger.debug(f"Pattern {i+1} found {len(matches)} matches")
            
            for j, match in enumerate(matches):
                if isinstance(match, tuple):
                    url = match[1] if len(match) > 1 else match[0]
                else:
                    url = match
                
                logger.debug(f"Checking match {j+1}: {url}")
                
                if self._looks_like_api(url):
                    full_url = urljoin(base_url, url)
                    logger.info(f"Found API endpoint in JavaScript: {full_url}")
                    endpoint = APIEndpoint(
                        url=full_url,
                        method=HTTPMethod.GET,  # Default to GET
                        description=f"Discovered from JavaScript",
                        authentication_required=False,
                        tags=['javascript']
                    )
                    endpoints.append(endpoint)
                else:
                    logger.debug(f"URL '{url}' doesn't look like an API endpoint")
        
        logger.debug(f"Extracted {len(endpoints)} API endpoints from JavaScript content")
        return endpoints
    
    def _deduplicate_endpoints(self, endpoints: List[APIEndpoint]) -> List[APIEndpoint]:
        """Remove duplicate endpoints"""
        seen = set()
        unique = []
        
        for endpoint in endpoints:
            key = f"{endpoint.url}:{endpoint.method}"
            if key not in seen:
                seen.add(key)
                unique.append(endpoint)
        
        return unique
    
    async def _generate_schemas(self, endpoints: List[APIEndpoint]) -> Dict[str, Any]:
        """Generate schemas from discovered endpoints"""
        schemas = {}
        
        for endpoint in endpoints:
            if endpoint.request_body:
                schemas[f"{endpoint.method}_{endpoint.url.split('/')[-1]}_request"] = endpoint.request_body
            
            if endpoint.response_schema:
                schemas[f"{endpoint.method}_{endpoint.url.split('/')[-1]}_response"] = endpoint.response_schema
        
        return schemas
    
    async def test_endpoint(self, url: str, method: str, headers: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
        """Test an API endpoint"""
        try:
            session = await self._get_session()
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body else None,
                timeout=10
            ) as response:
                response_data = {
                    'status_code': response.status,
                    'headers': dict(response.headers),
                    'url': str(response.url)
                }
                
                try:
                    response_data['body'] = await response.json()
                except:
                    response_data['body'] = await response.text()
                
                return response_data
        except Exception as e:
            return {
                'error': str(e),
                'status_code': None
            }
