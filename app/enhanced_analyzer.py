#!/usr/bin/env python3
"""
Enhanced API Analyzer with AST-based analysis, framework-specific extractors,
parameter source mapping, type inference, and comprehensive testing.
"""

import ast
import re
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .models import APIEndpoint, HTTPMethod

logger = logging.getLogger(__name__)

class ParameterSource(Enum):
    """Enum for parameter sources"""
    PATH = "path"
    QUERY = "query"
    BODY = "body"
    HEADER = "header"
    COOKIE = "cookie"
    FORM = "form"
    UNKNOWN = "unknown"

class ParameterType(Enum):
    """Enum for parameter types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"
    UNKNOWN = "unknown"

@dataclass
class ParameterInfo:
    """Information about a parameter"""
    name: str
    type: ParameterType
    source: ParameterSource
    required: bool = True
    default_value: Any = None
    description: str = ""
    validation_rules: Dict[str, Any] = None
    pydantic_model: Optional[str] = None

@dataclass
class EnhancedEndpoint:
    """Enhanced endpoint information with detailed parameter analysis"""
    url: str
    method: HTTPMethod
    parameters: List[ParameterInfo]
    request_body: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    authentication_required: bool = False
    description: str = ""
    tags: List[str] = None
    framework: str = "unknown"
    handler_function: Optional[str] = None

class EnhancedAPIAnalyzer:
    """Enhanced API analyzer with AST-based analysis and framework-specific extractors"""
    
    def __init__(self):
        self.type_inferrer = TypeInferrer()
        self.pydantic_analyzer = PydanticAnalyzer()
    
    def analyze_file(self, file_path: str, content: str) -> List[EnhancedEndpoint]:
        """Analyze a file for API endpoints with enhanced parameter extraction"""
        logger.info(f"Analyzing file: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.py':
            return self._analyze_python_file(file_path, content)
        elif file_ext in ['.js', '.ts', '.jsx', '.tsx']:
            return self._analyze_javascript_file(file_path, content)
        elif file_ext == '.java':
            return self._analyze_java_file(file_path, content)
        elif file_ext == '.go':
            return self._analyze_go_file(file_path, content)
        elif file_ext == '.php':
            return self._analyze_php_file(file_path, content)
        elif file_ext == '.rb':
            return self._analyze_ruby_file(file_path, content)
        else:
            logger.debug(f"Unsupported file type: {file_ext}")
            return []
    
    def _analyze_python_file(self, file_path: str, content: str) -> List[EnhancedEndpoint]:
        """Analyze Python file using AST"""
        try:
            tree = ast.parse(content)
            endpoints = []
            
            pydantic_models = self.pydantic_analyzer.extract_pydantic_models(tree)
            router_names = self._find_router_instances(tree)
            
            # Analyze all function and async function definitions (including class methods)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    endpoint = self._analyze_python_function(node, file_path, pydantic_models, router_names)
                    if endpoint:
                        endpoints.append(endpoint)

            # Deduplicate by (method, url)
            unique_endpoints = { (ep.method, ep.url): ep for ep in endpoints }.values()

            logger.info(f"Found {len(unique_endpoints)} unique endpoints in Python file: {file_path}")
            return list(unique_endpoints)
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {e}")
            return []

    def _find_router_instances(self, tree: ast.AST) -> set:
        """Find variable names assigned to FastAPI/APIRouter/Flask instances."""
        router_names = {'app', 'router'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                func = node.value.func
                name = None
                if isinstance(func, ast.Name) and func.id in ['FastAPI', 'APIRouter', 'Flask']:
                    name = func.id
                elif isinstance(func, ast.Attribute) and func.attr in ['FastAPI', 'APIRouter', 'Flask']:
                    name = func.attr
                if name:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            router_names.add(target.id)
        return router_names

    def _analyze_python_function(self, func_node: ast.FunctionDef, file_path: str, pydantic_models: Dict[str, Any], router_names: set) -> Optional[EnhancedEndpoint]:
        """Analyze a Python function for API endpoint information"""
        
        # Check if function has route decorators
        route_info = self._extract_route_from_decorators(func_node, router_names)
        if not route_info:
            return None
        
        # Analyze function parameters with enhanced logic
        parameters = self._analyze_python_parameters_enhanced(func_node, route_info, pydantic_models)
        
        # Analyze function body for request handling patterns
        request_patterns = self._analyze_python_request_handling(func_node)
        
        # Determine framework
        framework = self._detect_python_framework(func_node, file_path, router_names)
        
        # Extract request body schema from Pydantic models
        request_body = self._extract_request_body_from_parameters(parameters, pydantic_models)
        
        return EnhancedEndpoint(
            url=route_info['url'],
            method=route_info['method'],
            parameters=parameters,
            request_body=request_body,
            response_schema=request_patterns.get('response'),
            authentication_required=request_patterns.get('auth_required', False),
            description=self._extract_function_docstring(func_node),
            tags=['python', framework],
            framework=framework,
            handler_function=func_node.name
        )
    
    def _extract_route_from_decorators(self, func_node: ast.FunctionDef, router_names: set) -> Optional[Dict[str, Any]]:
        """Extract route information from function decorators"""
        
        for decorator in func_node.decorator_list:
            route_info = self._analyze_decorator(decorator, router_names)
            if route_info:
                return route_info
        
        return None
    
    def _analyze_decorator(self, decorator: ast.expr, router_names: set) -> Optional[Dict[str, Any]]:
        """Analyze a decorator for route information"""
        
        # Handle different decorator patterns
        if isinstance(decorator, ast.Call):
            return self._analyze_call_decorator(decorator, router_names)
        elif isinstance(decorator, ast.Attribute):
            return self._analyze_attribute_decorator(decorator)
        elif isinstance(decorator, ast.Name):
            return self._analyze_name_decorator(decorator)
        
        return None
    
    def _analyze_call_decorator(self, decorator: ast.Call, router_names: set) -> Optional[Dict[str, Any]]:
        """Analyze a call decorator (e.g., @app.get('/path'))"""
        
        # Check for patterns like @router.get('/path') where router is a known instance
        if isinstance(decorator.func, ast.Attribute) and isinstance(decorator.func.value, ast.Name):
            instance_name = decorator.func.value.id
            if instance_name in router_names:
                method = decorator.func.attr.upper()
                if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'ROUTE']:
                    if decorator.args and isinstance(decorator.args[0], (ast.Constant, ast.Str)):
                        url = decorator.args[0].value if isinstance(decorator.args[0], ast.Constant) else decorator.args[0].s
                        
                        final_method = method
                        if method == 'ROUTE':
                            method_from_kw = self._extract_method_from_keywords(decorator.keywords)
                            if method_from_kw:
                                final_method = method_from_kw.value
                        
                        return {'url': url, 'method': HTTPMethod(final_method)}

        # Fallback for general @route decorator for Flask Blueprints
        if isinstance(decorator.func, ast.Name) and decorator.func.id == 'route':
            if decorator.args and isinstance(decorator.args[0], (ast.Constant, ast.Str)):
                url = decorator.args[0].value if isinstance(decorator.args[0], ast.Constant) else decorator.args[0].s
                method_obj = self._extract_method_from_keywords(decorator.keywords)
                return {'url': url, 'method': method_obj or HTTPMethod.GET}
        
        return None
    
    def _extract_method_from_keywords(self, keywords: List[ast.keyword]) -> Optional[HTTPMethod]:
        """Extract HTTP method from decorator keywords"""
        for keyword in keywords:
            if keyword.arg == 'methods' and isinstance(keyword.value, ast.List):
                for method_el in keyword.value.elts:
                    if isinstance(method_el, ast.Constant):
                        method_str = method_el.value.upper()
                        if method_str in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                            return HTTPMethod(method_str)
                    elif isinstance(method_el, ast.Str):
                        # Handle Python < 3.8 where strings are ast.Str
                        method_str = method_el.s.upper()
                        if method_str in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                            return HTTPMethod(method_str)
        return None
    
    def _analyze_python_parameters_enhanced(self, func_node: ast.FunctionDef, route_info: Dict[str, Any], pydantic_models: Dict[str, Any]) -> List[ParameterInfo]:
        """Enhanced analysis of function parameters to determine their sources and types"""
        parameters = []
        
        # Extract path parameters from URL
        path_params = self._extract_path_parameters_from_url(route_info['url'])
        
        for arg in func_node.args.args:
            param_name = arg.arg
            
            # Skip 'self' parameter
            if param_name == 'self':
                continue
            
            # Extract type hint
            param_type = self._extract_type_hint(arg)
            
            # Extract default value
            default_value = self._extract_default_value(arg, func_node)
            
            # Determine parameter source with enhanced logic
            param_source = self._determine_parameter_source_enhanced(param_name, func_node, route_info, path_params)
            
            # Determine if required
            required = default_value is None and param_name not in [arg.arg for arg in func_node.args.kwonlyargs]
            
            # Check if it's a Pydantic model
            pydantic_model = self._find_pydantic_model_for_parameter(param_name, arg, pydantic_models)
            
            # Create parameter info
            param_info = ParameterInfo(
                name=param_name,
                type=param_type,
                source=param_source,
                required=required,
                default_value=default_value,
                description=self._extract_parameter_description(arg, func_node),
                pydantic_model=pydantic_model
            )
            
            parameters.append(param_info)
        
        # Add path parameters that might not be in function signature
        for path_param in path_params:
            if not any(p.name == path_param for p in parameters):
                param_info = ParameterInfo(
                    name=path_param,
                    type=ParameterType.STRING,
                    source=ParameterSource.PATH,
                    required=True,
                    description=f"Path parameter: {path_param}"
                )
                parameters.append(param_info)
        
        return parameters
    
    def _extract_path_parameters_from_url(self, url: str) -> List[str]:
        """Extract path parameters from URL patterns"""
        path_params = []
        
        # FastAPI/Starlette style: /users/{user_id}
        fastapi_params = re.findall(r'\{([^}]+)\}', url)
        path_params.extend(fastapi_params)
        
        # Flask style: /users/<user_id>
        flask_params = re.findall(r'<([^>]+)>', url)
        path_params.extend(flask_params)
        
        # Django style: /users/<int:user_id>
        django_params = re.findall(r'<[^:]*:([^>]+)>', url)
        path_params.extend(django_params)
        
        return list(set(path_params))  # Remove duplicates
    
    def _determine_parameter_source_enhanced(self, param_name: str, func_node: ast.FunctionDef, route_info: Dict[str, Any], path_params: List[str]) -> ParameterSource:
        """Enhanced parameter source determination"""
        
        # Check if it's a path parameter
        if param_name in path_params:
            return ParameterSource.PATH
        
        # Check if parameter name matches common request object patterns
        if param_name in ['request', 'req']:
            return ParameterSource.BODY
        
        # Check default values for FastAPI parameter types (Query, Header, etc.)
        default_value = self._get_parameter_default_value(param_name, func_node)
        if default_value:
            if default_value.startswith('Query(') or 'Query(' in default_value:
                return ParameterSource.QUERY
            elif default_value.startswith('Header(') or 'Header(' in default_value:
                return ParameterSource.HEADER
            elif default_value.startswith('Cookie(') or 'Cookie(' in default_value:
                return ParameterSource.COOKIE
            elif default_value.startswith('Form(') or 'Form(' in default_value:
                return ParameterSource.FORM
            elif default_value.startswith('Path(') or 'Path(' in default_value:
                return ParameterSource.PATH
            elif default_value.startswith('Body(') or 'Body(' in default_value:
                return ParameterSource.BODY
        
        # Check function body for parameter usage patterns
        if self._parameter_used_in_request_body(param_name, func_node):
            return ParameterSource.BODY
        
        # Check for query parameter patterns
        if self._parameter_used_as_query_param(param_name, func_node):
            return ParameterSource.QUERY
        
        # Check for header parameter patterns
        if self._parameter_used_as_header_param(param_name, func_node):
            return ParameterSource.HEADER
        
        # Check for form parameter patterns
        if self._parameter_used_as_form_param(param_name, func_node):
            return ParameterSource.FORM
        
        # Check type hints for common patterns
        param_type = self._get_parameter_type_hint(param_name, func_node)
        if param_type:
            if 'Form' in param_type:
                return ParameterSource.FORM
            elif 'Header' in param_type:
                return ParameterSource.HEADER
            elif 'Query' in param_type:
                return ParameterSource.QUERY
            elif 'Path' in param_type:
                return ParameterSource.PATH
            elif 'Body' in param_type or 'Depends' in param_type:
                return ParameterSource.BODY
        
        # Default based on HTTP method and parameter type
        if route_info['method'] in [HTTPMethod.GET, HTTPMethod.DELETE]:
            return ParameterSource.QUERY
        else:
            return ParameterSource.BODY
    
    def _get_parameter_type_hint(self, param_name: str, func_node: ast.FunctionDef) -> Optional[str]:
        """Get the type hint string for a parameter"""
        for arg in func_node.args.args:
            if arg.arg == param_name and arg.annotation:
                return ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else self._ast_to_string(arg.annotation)
        return None
    
    def _get_parameter_default_value(self, param_name: str, func_node: ast.FunctionDef) -> Optional[str]:
        """Get the default value string for a parameter (e.g., Query(...), Header(...))"""
        # Find parameter index
        param_index = None
        for i, arg in enumerate(func_node.args.args):
            if arg.arg == param_name:
                param_index = i
                break
        
        if param_index is None:
            return None
        
        # Check if there's a default value
        defaults_start = len(func_node.args.args) - len(func_node.args.defaults)
        if param_index >= defaults_start:
            default_index = param_index - defaults_start
            default = func_node.args.defaults[default_index]
            
            # Convert AST node to string
            if hasattr(ast, 'unparse'):
                return ast.unparse(default)
            else:
                return self._ast_to_string(default)
        
        return None
    
    def _ast_to_string(self, node: ast.expr) -> str:
        """Convert AST node to string representation"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._ast_to_string(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._ast_to_string(node.value)}[{self._ast_to_string(node.slice)}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return "unknown"
    
    def _parameter_used_in_request_body(self, param_name: str, func_node: ast.FunctionDef) -> bool:
        """Check if parameter is used in request body handling"""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Attribute):
                if (isinstance(node.value, ast.Name) and 
                    node.value.id == param_name and 
                    node.attr in ['json', 'data', 'body']):
                    return True
        return False
    
    def _parameter_used_as_query_param(self, param_name: str, func_node: ast.FunctionDef) -> bool:
        """Check if parameter is used as query parameter"""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Attribute):
                if (isinstance(node.value, ast.Name) and 
                    node.value.id == param_name and 
                    node.attr in ['query', 'params', 'args']):
                    return True
        return False
    
    def _parameter_used_as_header_param(self, param_name: str, func_node: ast.FunctionDef) -> bool:
        """Check if parameter is used as header parameter"""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Attribute):
                if (isinstance(node.value, ast.Name) and 
                    node.value.id == param_name and 
                    node.attr in ['headers', 'header']):
                    return True
        return False
    
    def _parameter_used_as_form_param(self, param_name: str, func_node: ast.FunctionDef) -> bool:
        """Check if parameter is used as form parameter"""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Attribute):
                if (isinstance(node.value, ast.Name) and 
                    node.value.id == param_name and 
                    node.attr in ['form', 'files']):
                    return True
        return False
    
    def _find_pydantic_model_for_parameter(self, param_name: str, arg: ast.arg, pydantic_models: Dict[str, Any]) -> Optional[str]:
        """Find Pydantic model for a parameter"""
        if arg.annotation:
            type_str = self._ast_to_string(arg.annotation)
            for model_name in pydantic_models.keys():
                if model_name in type_str:
                    return model_name
        return None
    
    def _extract_request_body_from_parameters(self, parameters: List[ParameterInfo], pydantic_models: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract request body schema from parameters"""
        body_params = [p for p in parameters if p.source == ParameterSource.BODY]
        
        if not body_params:
            return None
        
        # If we have a Pydantic model, use its schema
        for param in body_params:
            if param.pydantic_model and param.pydantic_model in pydantic_models:
                return pydantic_models[param.pydantic_model]
        
        # Otherwise, create a basic schema from parameters
        properties = {}
        required = []
        
        for param in body_params:
            properties[param.name] = {
                "type": param.type.value,
                "description": param.description
            }
            if param.required:
                required.append(param.name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _extract_type_hint(self, arg: ast.arg) -> ParameterType:
        """Extract type hint from function argument"""
        if arg.annotation:
            return self.type_inferrer.infer_type_from_annotation(arg.annotation)
        return ParameterType.UNKNOWN
    
    def _extract_default_value(self, arg: ast.arg, func_node: ast.FunctionDef) -> Any:
        """Extract default value for a parameter"""
        # Find the parameter index
        param_index = None
        for i, func_arg in enumerate(func_node.args.args):
            if func_arg.arg == arg.arg:
                param_index = i
                break
        
        if param_index is not None and param_index >= len(func_node.args.defaults):
            return None
        
        # Get default value
        if func_node.args.defaults and param_index < len(func_node.args.defaults):
            default_node = func_node.args.defaults[param_index]
            return self._extract_constant_value(default_node)
        
        return None
    
    def _extract_constant_value(self, node: ast.expr) -> Any:
        """Extract constant value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            if node.id in ['True', 'False']:
                return node.id == 'True'
            elif node.id == 'None':
                return None
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.List):
            return [self._extract_constant_value(el) for el in node.elts]
        elif isinstance(node, ast.Dict):
            return {
                self._extract_constant_value(k): self._extract_constant_value(v)
                for k, v in zip(node.keys, node.values)
            }
        elif isinstance(node, ast.NameConstant):
            # Handle Python < 3.8 where True/False/None are NameConstant
            if node.value is True:
                return True
            elif node.value is False:
                return False
            elif node.value is None:
                return None
        
        return None
    
    def _extract_parameter_description(self, arg: ast.arg, func_node: ast.FunctionDef) -> str:
        """Extract parameter description from docstring or comments"""
        docstring = self._extract_function_docstring(func_node)
        if docstring:
            # Look for parameter documentation in docstring
            lines = docstring.split('\n')
            for line in lines:
                if f':param {arg.arg}:' in line or f':param {arg.arg} ' in line:
                    return line.split(':', 2)[-1].strip()
        return ""
    
    def _extract_function_docstring(self, func_node: ast.FunctionDef) -> str:
        """Extract docstring from function"""
        if func_node.body and isinstance(func_node.body[0], ast.Expr):
            if isinstance(func_node.body[0].value, ast.Constant):
                return func_node.body[0].value.value
            elif isinstance(func_node.body[0].value, ast.Str):
                # Handle Python < 3.8 where strings are ast.Str
                return func_node.body[0].value.s
        return ""
    
    def _analyze_python_request_handling(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze function body for request handling patterns"""
        patterns = {
            'body': None,
            'response': None,
            'auth_required': False
        }
        
        for node in ast.walk(func_node):
            # Check for request body handling
            if isinstance(node, ast.Attribute):
                if node.attr in ['json', 'data', 'body']:
                    patterns['body'] = self._extract_request_body_schema(node)
            
            # Check for authentication patterns
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr in ['require_auth', 'login_required', 'authenticate']):
                    patterns['auth_required'] = True
        
        return patterns
    
    def _extract_request_body_schema(self, node: ast.Attribute) -> Optional[Dict[str, Any]]:
        """Extract request body schema from AST node"""
        # This is a simplified implementation
        # In a full implementation, you would analyze the actual schema
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def _detect_python_framework(self, func_node: ast.FunctionDef, file_path: str, router_names: set) -> str:
        """Detect the Python web framework being used"""
        
        # Check decorators for framework-specific patterns
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                    return 'fastapi'
                elif decorator.func.attr == 'route':
                    return 'flask'
        
        # Check imports and file structure
        if 'django' in file_path.lower() or 'views.py' in file_path:
            return 'django'
        elif 'fastapi' in file_path.lower():
            return 'fastapi'
        elif 'flask' in file_path.lower():
            return 'flask'
        
        return 'unknown'
    
    def _analyze_python_class(self, class_node: ast.ClassDef, file_path: str, pydantic_models: Dict[str, Any], router_names: set) -> List[EnhancedEndpoint]:
        """Analyze a Python class for API endpoint methods"""
        endpoints = []
        
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                # Check if it's a method that could be an endpoint
                endpoint = self._analyze_python_function(node, file_path, pydantic_models, router_names)
                if endpoint:
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _analyze_attribute_decorator(self, decorator: ast.Attribute) -> Optional[Dict[str, Any]]:
        """Analyze attribute decorator"""
        return None
    
    def _analyze_name_decorator(self, decorator: ast.Name) -> Optional[Dict[str, Any]]:
        """Analyze name decorator"""
        return None
    
    def _analyze_javascript_file(self, file_path: str, content: str) -> List[EnhancedEndpoint]:
        """Analyze JavaScript/TypeScript file for API endpoints with improved framework detection"""
        endpoints = []
        
        # Detect framework first
        framework = self._detect_javascript_framework(content, file_path)
        
        # Use framework-specific patterns
        if framework == 'express':
            patterns = [
                r'\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'router\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'app\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'express\.Router\(\)\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
            ]
        elif framework == 'koa':
            patterns = [
                r'router\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
            ]
        elif framework == 'hapi':
            patterns = [
                r'server\.route\(\s*\{[\s\S]*?path:\s*[\'"`]([^\'"`]+)[\'"`][\s\S]*?method:\s*[\'"`]([^\'"`]+)[\'"`]',
            ]
        elif framework == 'nestjs':
            patterns = [
                r'@(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]\)',
                r'@Controller\([\'"`]([^\'"`]+)[\'"`]\)',
            ]
        else:
            # Generic patterns
            patterns = [
                r'\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'router\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'app\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
            ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) >= 2:
                        method = match[0].upper()
                        url = match[1]
                    else:
                        method = 'GET'
                        url = match[0]
                else:
                    method = 'GET'
                    url = match
                
                if url and not url.startswith('#'):
                    # Clean up the path
                    url = url.strip()
                    if not url.startswith('/'):
                        url = '/' + url
                    
                    endpoint = EnhancedEndpoint(
                        url=url,
                        method=HTTPMethod(method),
                        parameters=self._extract_js_parameters(content, url, framework),
                        framework=framework,
                        tags=['javascript', framework]
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _detect_javascript_framework(self, content: str, file_path: str) -> str:
        """Detect JavaScript framework with improved accuracy"""
        content_lower = content.lower()
        
        # Framework-specific indicators
        framework_indicators = {
            'express': [
                'require(\'express\')', 'import express', 'const express', 'var express',
                'express.router', 'express()', 'app.use', 'app.get', 'app.post',
                'router.get', 'router.post', 'express.static'
            ],
            'koa': [
                'require(\'koa\')', 'import koa', 'const koa', 'var koa',
                'koa-router', 'koa()', '@koa/', 'koa-bodyparser'
            ],
            'hapi': [
                'require(\'@hapi/hapi\')', 'import hapi', 'const hapi', 'var hapi',
                'server.route', 'hapi.server', '@hapi/hapi'
            ],
            'nestjs': [
                '@nestjs', 'nestjs/common', '@controller', '@get', '@post',
                'nestjs/core', 'nestjs/platform-express'
            ],
            'fastify': [
                'require(\'fastify\')', 'import fastify', 'const fastify', 'var fastify',
                'fastify()', 'fastify.get', 'fastify.post'
            ]
        }
        
        # Count indicators for each framework
        framework_scores = {}
        for framework, indicators in framework_indicators.items():
            score = sum(1 for indicator in indicators if indicator in content_lower)
            if score > 0:
                framework_scores[framework] = score
        
        # Return the highest scoring framework
        if framework_scores:
            return max(framework_scores.items(), key=lambda x: x[1])[0]
        
        return 'express'  # Default to express
    
    def _extract_js_parameters(self, content: str, url: str, framework: str) -> List[ParameterInfo]:
        """Extract parameters from JavaScript endpoint with framework-specific logic"""
        parameters = []
        
        # Extract path parameters from URL
        path_params = re.findall(r':(\w+)', url)
        for param in path_params:
            parameters.append(ParameterInfo(
                name=param,
                type=ParameterType.STRING,
                source=ParameterSource.PATH,
                required=True
            ))
        
        # Framework-specific parameter extraction
        if framework == 'express':
            # Look for req.params, req.query, req.body usage
            param_patterns = [
                (r'req\.params\.(\w+)', ParameterSource.PATH),
                (r'req\.query\.(\w+)', ParameterSource.QUERY),
                (r'req\.body\.(\w+)', ParameterSource.BODY),
                (r'req\.headers\.(\w+)', ParameterSource.HEADER),
            ]
        elif framework == 'koa':
            # Look for ctx.params, ctx.query, ctx.request.body usage
            param_patterns = [
                (r'ctx\.params\.(\w+)', ParameterSource.PATH),
                (r'ctx\.query\.(\w+)', ParameterSource.QUERY),
                (r'ctx\.request\.body\.(\w+)', ParameterSource.BODY),
                (r'ctx\.headers\.(\w+)', ParameterSource.HEADER),
            ]
        else:
            param_patterns = []
        
        for pattern, source in param_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for param_name in matches:
                if not any(p.name == param_name for p in parameters):
                    parameters.append(ParameterInfo(
                        name=param_name,
                        type=ParameterType.STRING,
                        source=source,
                        required=True
                    ))
        
        return parameters
    
    def _analyze_java_file(self, file_path: str, content: str) -> List[EnhancedEndpoint]:
        """Analyze Java file for API endpoints with improved framework detection"""
        endpoints = []
        
        # Detect framework first
        framework = self._detect_java_framework(content, file_path)
        
        # Use framework-specific patterns
        if framework == 'spring':
            patterns = [
                r'@(Get|Post|Put|Delete|Patch)Mapping\([\'"`]([^\'"`]+)[\'"`]',
                r'@RequestMapping\([\'"`]([^\'"`]+)[\'"`]',
                r'@RestController.*?@RequestMapping\([\'"`]([^\'"`]+)[\'"`]',
                r'@Controller.*?@RequestMapping\([\'"`]([^\'"`]+)[\'"`]',
                r'@(Get|Post|Put|Delete|Patch)Mapping\(value\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
                r'@RequestMapping\(value\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
            ]
        elif framework == 'jaxrs':
            patterns = [
                r'@(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'@Path\([\'"`]([^\'"`]+)[\'"`]',
            ]
        elif framework == 'micronaut':
            patterns = [
                r'@(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'@Controller\([\'"`]([^\'"`]+)[\'"`]',
            ]
        else:
            # Generic patterns
            patterns = [
                r'@(Get|Post|Put|Delete|Patch)Mapping\([\'"`]([^\'"`]+)[\'"`]',
                r'@RequestMapping\([\'"`]([^\'"`]+)[\'"`]',
            ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) >= 2:
                        method = match[0].upper()
                        url = match[1]
                    else:
                        method = 'GET'
                        url = match[0]
                else:
                    method = 'GET'
                    url = match
                
                if url and not url.startswith('#'):
                    # Clean up the path
                    url = url.strip()
                    if not url.startswith('/'):
                        url = '/' + url
                    
                    endpoint = EnhancedEndpoint(
                        url=url,
                        method=HTTPMethod(method),
                        parameters=self._extract_java_parameters(content, url, framework),
                        framework=framework,
                        tags=['java', framework]
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _detect_java_framework(self, content: str, file_path: str) -> str:
        """Detect Java framework with improved accuracy"""
        content_lower = content.lower()
        
        # Framework-specific indicators
        framework_indicators = {
            'spring': [
                '@springbootapplication', '@restcontroller', '@controller',
                '@requestmapping', '@getmapping', '@postmapping', 'springframework',
                'spring.boot', 'spring.web', 'spring.data'
            ],
            'jaxrs': [
                '@path', '@get', '@post', '@put', '@delete', '@produces', '@consumes',
                'javax.ws.rs', 'jaxrs', 'jersey'
            ],
            'micronaut': [
                '@micronaut', '@controller', '@get', '@post', '@put', '@delete',
                'micronaut.http', 'micronaut.web'
            ],
            'quarkus': [
                '@path', '@get', '@post', '@put', '@delete', '@produces', '@consumes',
                'quarkus', 'io.quarkus'
            ]
        }
        
        # Count indicators for each framework
        framework_scores = {}
        for framework, indicators in framework_indicators.items():
            score = sum(1 for indicator in indicators if indicator in content_lower)
            if score > 0:
                framework_scores[framework] = score
        
        # Return the highest scoring framework
        if framework_scores:
            return max(framework_scores.items(), key=lambda x: x[1])[0]
        
        return 'spring'  # Default to spring
    
    def _extract_java_parameters(self, content: str, url: str, framework: str) -> List[ParameterInfo]:
        """Extract parameters from Java endpoint with framework-specific logic"""
        parameters = []
        
        # Extract path parameters from URL
        path_params = re.findall(r'\{(\w+)\}', url)
        for param in path_params:
            parameters.append(ParameterInfo(
                name=param,
                type=ParameterType.STRING,
                source=ParameterSource.PATH,
                required=True
            ))
        
        # Framework-specific parameter extraction
        if framework == 'spring':
            # Look for @PathVariable, @RequestParam, @RequestBody, @RequestHeader
            param_patterns = [
                (r'@PathVariable\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.PATH),
                (r'@RequestParam\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.QUERY),
                (r'@RequestBody', ParameterSource.BODY),
                (r'@RequestHeader\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.HEADER),
            ]
        elif framework == 'jaxrs':
            # Look for @PathParam, @QueryParam, @HeaderParam
            param_patterns = [
                (r'@PathParam\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.PATH),
                (r'@QueryParam\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.QUERY),
                (r'@HeaderParam\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.HEADER),
            ]
        else:
            param_patterns = []
        
        for pattern, source in param_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for param_name in matches:
                if not any(p.name == param_name for p in parameters):
                    parameters.append(ParameterInfo(
                        name=param_name,
                        type=ParameterType.STRING,
                        source=source,
                        required=True
                    ))
        
        return parameters
    
    def _analyze_go_file(self, file_path: str, content: str) -> List[EnhancedEndpoint]:
        """Analyze Go file for API endpoints with improved framework detection"""
        endpoints = []
        
        # Detect framework first
        framework = self._detect_go_framework(content, file_path)
        
        # Use framework-specific patterns
        if framework == 'gin':
            patterns = [
                r'\.(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'router\.(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'group\.(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
            ]
        elif framework == 'echo':
            patterns = [
                r'\.(GET|POST|PUT|DELETE|PATCH)\([\'"`]([^\'"`]+)[\'"`]',
                r'group\.(GET|POST|PUT|DELETE|PATCH)\([\'"`]([^\'"`]+)[\'"`]',
            ]
        elif framework == 'gorilla':
            patterns = [
                r'\.HandleFunc\([\'"`]([^\'"`]+)[\'"`]',
                r'\.Methods\([\'"`]([^\'"`]+)[\'"`]',
            ]
        else:
            # Generic patterns
            patterns = [
                r'\.(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'router\.(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
            ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) >= 2:
                        method = match[0].upper()
                        url = match[1]
                    else:
                        method = 'GET'
                        url = match[0]
                else:
                    method = 'GET'
                    url = match
                
                if url and not url.startswith('#'):
                    # Clean up the path
                    url = url.strip()
                    if not url.startswith('/'):
                        url = '/' + url
                    
                    endpoint = EnhancedEndpoint(
                        url=url,
                        method=HTTPMethod(method),
                        parameters=self._extract_go_parameters(content, url, framework),
                        framework=framework,
                        tags=['go', framework]
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _detect_go_framework(self, content: str, file_path: str) -> str:
        """Detect Go framework with improved accuracy"""
        content_lower = content.lower()
        
        # Framework-specific indicators
        framework_indicators = {
            'gin': [
                'gin.engine', 'gin.new()', 'gin.default()', 'gin.group',
                'router.get', 'router.post', 'gin.context', 'github.com/gin-gonic/gin'
            ],
            'echo': [
                'echo.new()', 'echo.group', 'e.get', 'e.post', 'e.put',
                'github.com/labstack/echo', 'labstack/echo'
            ],
            'gorilla': [
                'gorilla/mux', 'mux.router', 'mux.newrouter', 'github.com/gorilla/mux'
            ],
            'fiber': [
                'fiber.new()', 'fiber.app', 'app.get', 'app.post', 'github.com/gofiber/fiber'
            ]
        }
        
        # Count indicators for each framework
        framework_scores = {}
        for framework, indicators in framework_indicators.items():
            score = sum(1 for indicator in indicators if indicator in content_lower)
            if score > 0:
                framework_scores[framework] = score
        
        # Return the highest scoring framework
        if framework_scores:
            return max(framework_scores.items(), key=lambda x: x[1])[0]
        
        return 'gin'  # Default to gin
    
    def _extract_go_parameters(self, content: str, url: str, framework: str) -> List[ParameterInfo]:
        """Extract parameters from Go endpoint with framework-specific logic"""
        parameters = []
        
        # Extract path parameters from URL
        path_params = re.findall(r':(\w+)', url)
        for param in path_params:
            parameters.append(ParameterInfo(
                name=param,
                type=ParameterType.STRING,
                source=ParameterSource.PATH,
                required=True
            ))
        
        # Framework-specific parameter extraction
        if framework == 'gin':
            # Look for c.Param, c.Query, c.BindJSON usage
            param_patterns = [
                (r'c\.Param\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.PATH),
                (r'c\.Query\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.QUERY),
                (r'c\.BindJSON', ParameterSource.BODY),
                (r'c\.GetHeader\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.HEADER),
            ]
        elif framework == 'echo':
            # Look for c.Param, c.QueryParam, c.Bind usage
            param_patterns = [
                (r'c\.Param\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.PATH),
                (r'c\.QueryParam\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.QUERY),
                (r'c\.Bind', ParameterSource.BODY),
                (r'c\.Request\(\)\.Header\.Get\([\'"`]([^\'"`]+)[\'"`]\)', ParameterSource.HEADER),
            ]
        else:
            param_patterns = []
        
        for pattern, source in param_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for param_name in matches:
                if not any(p.name == param_name for p in parameters):
                    parameters.append(ParameterInfo(
                        name=param_name,
                        type=ParameterType.STRING,
                        source=source,
                        required=True
                    ))
        
        return parameters
    
    def _analyze_php_file(self, file_path: str, content: str) -> List[EnhancedEndpoint]:
        """Analyze PHP file for API endpoints"""
        endpoints = []
        
        # PHP Laravel patterns
        patterns = [
            r'Route::(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    method = match[0].upper()
                    url = match[1]
                    
                    endpoint = EnhancedEndpoint(
                        url=url,
                        method=HTTPMethod(method),
                        parameters=self._extract_php_parameters(content, url),
                        framework='laravel',
                        tags=['php']
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_php_parameters(self, content: str, url: str) -> List[ParameterInfo]:
        """Extract parameters from PHP endpoint"""
        parameters = []
        
        # Extract path parameters from URL
        path_params = re.findall(r'\{(\w+)\}', url)
        for param in path_params:
            parameters.append(ParameterInfo(
                name=param,
                type=ParameterType.STRING,
                source=ParameterSource.PATH,
                required=True
            ))
        
        return parameters
    
    def _analyze_ruby_file(self, file_path: str, content: str) -> List[EnhancedEndpoint]:
        """Analyze Ruby file for API endpoints"""
        endpoints = []
        
        # Ruby Rails patterns
        patterns = [
            r'(get|post|put|delete|patch)\s+[\'"`]([^\'"`]+)[\'"`]',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    method = match[0].upper()
                    url = match[1]
                    
                    endpoint = EnhancedEndpoint(
                        url=url,
                        method=HTTPMethod(method),
                        parameters=self._extract_ruby_parameters(content, url),
                        framework='rails',
                        tags=['ruby']
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_ruby_parameters(self, content: str, url: str) -> List[ParameterInfo]:
        """Extract parameters from Ruby endpoint"""
        parameters = []
        
        # Extract path parameters from URL
        path_params = re.findall(r':(\w+)', url)
        for param in path_params:
            parameters.append(ParameterInfo(
                name=param,
                type=ParameterType.STRING,
                source=ParameterSource.PATH,
                required=True
            ))
        
        return parameters
    
    def convert_to_api_endpoints(self, enhanced_endpoints: List[EnhancedEndpoint]) -> List[APIEndpoint]:
        """Convert enhanced endpoints to standard APIEndpoint objects"""
        api_endpoints = []
        
        for enhanced_endpoint in enhanced_endpoints:
            # Convert parameters to the format expected by APIEndpoint
            parameters = {}
            for param in enhanced_endpoint.parameters:
                parameters[param.name] = {
                    'type': param.type.value,
                    'source': param.source.value,
                    'required': param.required,
                    'default': param.default_value,
                    'description': param.description
                }
            
            api_endpoint = APIEndpoint(
                url=enhanced_endpoint.url,
                method=enhanced_endpoint.method,
                description=enhanced_endpoint.description,
                parameters=parameters,
                request_body=enhanced_endpoint.request_body,
                response_schema=enhanced_endpoint.response_schema,
                authentication_required=enhanced_endpoint.authentication_required,
                tags=enhanced_endpoint.tags or []
            )
            
            api_endpoints.append(api_endpoint)
        
        return api_endpoints


class PydanticAnalyzer:
    """Analyzer for Pydantic models to extract request/response schemas"""
    
    def extract_pydantic_models(self, tree: ast.AST) -> Dict[str, Any]:
        """Extract Pydantic models from AST"""
        models = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_pydantic_model(node):
                    model_name = node.name
                    model_schema = self._extract_model_schema(node)
                    models[model_name] = model_schema
        
        return models
    
    def _is_pydantic_model(self, class_node: ast.ClassDef) -> bool:
        """Check if a class is a Pydantic model"""
        # Check for BaseModel inheritance
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id == 'BaseModel':
                return True
            elif isinstance(base, ast.Attribute):
                if base.attr == 'BaseModel':
                    return True
        
        # Check for Pydantic imports
        for node in ast.walk(class_node):
            if isinstance(node, ast.ImportFrom):
                if node.module == 'pydantic' and any(alias.name == 'BaseModel' for alias in node.names):
                    return True
        
        return False
    
    def _extract_model_schema(self, class_node: ast.ClassDef) -> Dict[str, Any]:
        """Extract schema from Pydantic model"""
        properties = {}
        required = []
        
        # Extract fields from class attributes
        for node in class_node.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                field_name = node.target.id
                field_type = self._extract_field_type(node.annotation)
                field_required = not (isinstance(node.value, ast.Constant) and node.value.value is None)
                
                properties[field_name] = {
                    "type": field_type,
                    "description": ""
                }
                
                if field_required:
                    required.append(field_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _extract_field_type(self, annotation: ast.expr) -> str:
        """Extract field type from annotation"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return annotation.attr
        elif isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                return annotation.value.id
        return "string"


class TypeInferrer:
    """Type inference utility for analyzing parameter types"""
    
    def infer_type_from_annotation(self, annotation: ast.expr) -> ParameterType:
        """Infer parameter type from AST annotation"""
        
        if isinstance(annotation, ast.Name):
            return self._infer_from_name(annotation.id)
        elif isinstance(annotation, ast.Attribute):
            return self._infer_from_attribute(annotation)
        elif isinstance(annotation, ast.Subscript):
            return self._infer_from_subscript(annotation)
        elif isinstance(annotation, ast.Constant):
            return self._infer_from_constant(annotation.value)
        
        return ParameterType.UNKNOWN
    
    def _infer_from_name(self, name: str) -> ParameterType:
        """Infer type from annotation name"""
        type_mapping = {
            'str': ParameterType.STRING,
            'int': ParameterType.INTEGER,
            'float': ParameterType.FLOAT,
            'bool': ParameterType.BOOLEAN,
            'list': ParameterType.ARRAY,
            'dict': ParameterType.OBJECT,
            'List': ParameterType.ARRAY,
            'Dict': ParameterType.OBJECT,
            'Optional': ParameterType.UNKNOWN,
            'Union': ParameterType.UNKNOWN,
        }
        
        return type_mapping.get(name, ParameterType.UNKNOWN)
    
    def _infer_from_attribute(self, attribute: ast.Attribute) -> ParameterType:
        """Infer type from attribute annotation"""
        if isinstance(attribute.value, ast.Name):
            if attribute.value.id == 'typing':
                return self._infer_from_name(attribute.attr)
            elif attribute.value.id == 'pydantic':
                if attribute.attr in ['BaseModel', 'Field']:
                    return ParameterType.OBJECT
            elif attribute.value.id == 'fastapi':
                if attribute.attr in ['Form', 'File', 'UploadFile']:
                    return ParameterType.FILE
                elif attribute.attr in ['Query', 'Path', 'Header', 'Cookie']:
                    return ParameterType.STRING
        
        return ParameterType.UNKNOWN
    
    def _infer_from_subscript(self, subscript: ast.Subscript) -> ParameterType:
        """Infer type from subscript annotation (e.g., List[str])"""
        if isinstance(subscript.value, ast.Name):
            return self._infer_from_name(subscript.value.id)
        elif isinstance(subscript.value, ast.Attribute):
            return self._infer_from_attribute(subscript.value)
        
        return ParameterType.UNKNOWN
    
    def _infer_from_constant(self, value: Any) -> ParameterType:
        """Infer type from constant value"""
        if isinstance(value, str):
            return ParameterType.STRING
        elif isinstance(value, int):
            return ParameterType.INTEGER
        elif isinstance(value, float):
            return ParameterType.FLOAT
        elif isinstance(value, bool):
            return ParameterType.BOOLEAN
        elif isinstance(value, list):
            return ParameterType.ARRAY
        elif isinstance(value, dict):
            return ParameterType.OBJECT
        
        return ParameterType.UNKNOWN
