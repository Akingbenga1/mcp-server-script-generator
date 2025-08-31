import aiohttp
import asyncio
import json
import logging
import re
import os
import stat
import tempfile
import shutil
import subprocess
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
import yaml
import base64
from pathlib import Path

from .models import APIEndpoint, HTTPMethod

logger = logging.getLogger(__name__)

class GitHubAnalyzer:
    def __init__(self):
        self.session = None
        self.github_api_base = "https://api.github.com"
        # Add GitHub token support for higher rate limits
        self.github_token = None
        # Alternative analysis methods
        self.use_raw_github = True  # Use raw.githubusercontent.com as fallback
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    def set_github_token(self, token: str):
        """Set GitHub token for higher rate limits"""
        self.github_token = token
        logger.info("GitHub token set for higher rate limits")
    
    async def _analyze_with_fallback(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Analyze repository using fallback methods when API is rate limited"""
        logger.info(f"Using fallback analysis for {owner}/{repo_name}")
        
        analysis = {
            'repository': {
                'name': repo_name,
                'full_name': f"{owner}/{repo_name}",
                'description': f'Repository {owner}/{repo_name}',
                'topics': [],
                'html_url': f'https://github.com/{owner}/{repo_name}'
            },
            'api_endpoints': [],
            'documentation_files': [],
            'code_files': [],
            'openapi_specs': [],
            'readme_content': '',
            'languages': [],
            'topics': []
        }
        
        # Try to get README content using raw GitHub
        try:
            readme_content = await self._get_readme_raw_github(owner, repo_name)
            if readme_content:
                analysis['readme_content'] = readme_content
                logger.info("Found README content using raw GitHub")
        except Exception as e:
            logger.warning(f"Failed to get README via raw GitHub: {e}")
        
        # Try to analyze repository structure using raw GitHub
        try:
            await self._analyze_repo_structure_raw_github(owner, repo_name, analysis)
        except Exception as e:
            logger.warning(f"Failed to analyze repo structure via raw GitHub: {e}")
        
        # If no README found, perform deeper analysis
        if not analysis['readme_content']:
            logger.info("No README found, performing deeper repository analysis")
            await self._analyze_repository_without_readme(owner, repo_name, analysis)
        
        return analysis
        
    async def analyze_repository(self, repo_url: str) -> Dict[str, Any]:
        """Analyze a GitHub repository for API endpoints and documentation"""
        logger.info(f"Analyzing GitHub repository: {repo_url}")
        
        # Extract owner and repo name from URL
        owner, repo_name = self._extract_repo_info(repo_url)
        if not owner or not repo_name:
            logger.error(f"Invalid GitHub repository URL: {repo_url}")
            return {}
        
        logger.info(f"Repository: {owner}/{repo_name}")
        
        # PRIMARY METHOD: Clone repository locally and analyze
        try:
            logger.info("Attempting local repository analysis (primary method)")
            analysis = await self._analyze_repository_locally(repo_url, owner, repo_name)
            if analysis and (analysis.get('api_endpoints') or analysis.get('code_files')):
                logger.info("Local analysis successful, returning results")
                return analysis
        except Exception as e:
            logger.warning(f"Local repository analysis failed: {e}")
        
        # FALLBACK: Use GitHub API and online methods
        logger.info("Falling back to online analysis methods")
        
        # Get repository information
        repo_info = await self._get_repository_info(owner, repo_name)
        if not repo_info:
            logger.warning(f"Failed to get repository info for {owner}/{repo_name}, using fallback analysis")
            return await self._analyze_with_fallback(owner, repo_name)
        
        # Analyze repository content
        analysis = {
            'repository': repo_info,
            'api_endpoints': [],
            'documentation_files': [],
            'code_files': [],
            'openapi_specs': [],
            'readme_content': '',
            'languages': [],
            'topics': repo_info.get('topics', [])
        }
        
        # Get repository languages
        try:
            analysis['languages'] = await self._get_repository_languages(owner, repo_name)
            logger.info(f"Repository languages: {analysis['languages']}")
        except Exception as e:
            logger.warning(f"Failed to get languages: {e}")
            analysis['languages'] = []
        
        # Get README content
        try:
            readme_content = await self._get_readme_content(owner, repo_name)
            if readme_content:
                analysis['readme_content'] = readme_content
                logger.info("Found README content")
        except Exception as e:
            logger.warning(f"Failed to get README content: {e}")
        
        # Search for API-related files
        try:
            await self._search_api_files(owner, repo_name, analysis)
        except Exception as e:
            logger.warning(f"Failed to search API files: {e}")
        
        # Extract API endpoints from code files
        try:
            await self._extract_endpoints_from_code(owner, repo_name, analysis)
        except Exception as e:
            logger.warning(f"Failed to extract endpoints from code: {e}")
        
        # Search for OpenAPI/Swagger specifications
        try:
            await self._search_openapi_specs(owner, repo_name, analysis)
        except Exception as e:
            logger.warning(f"Failed to search OpenAPI specs: {e}")
        
        # If no endpoints found, try fallback analysis
        if not analysis['api_endpoints'] and not analysis['documentation_files']:
            logger.info("No endpoints found in main analysis, trying fallback analysis")
            fallback_analysis = await self._analyze_with_fallback(owner, repo_name)
            analysis['api_endpoints'].extend(fallback_analysis['api_endpoints'])
            analysis['documentation_files'].extend(fallback_analysis['documentation_files'])
            analysis['code_files'].extend(fallback_analysis['code_files'])
            analysis['openapi_specs'].extend(fallback_analysis['openapi_specs'])
            if not analysis['readme_content'] and fallback_analysis['readme_content']:
                analysis['readme_content'] = fallback_analysis['readme_content']
        
        logger.info(f"Analysis completed. Found {len(analysis['api_endpoints'])} API endpoints")
        return analysis
    
    async def _analyze_repository_locally(self, repo_url: str, owner: str, repo_name: str) -> Dict[str, Any]:
        """Analyze repository by cloning it locally and performing file system analysis"""
        logger.info("Starting local repository analysis")
        
        # Create temporary directory for cloning
        temp_dir = None
        repo_path = None
        
        try:
            temp_dir = tempfile.mkdtemp(prefix=f"github_analysis_{owner}_{repo_name}_")
            repo_path = os.path.join(temp_dir, repo_name)
            
            logger.info(f"Cloning repository to: {repo_path}")
            
            # Clone the repository
            clone_result = await self._clone_repository(repo_url, repo_path)
            if not clone_result:
                logger.error("Failed to clone repository")
                return {}
            
            logger.info("Repository cloned successfully, starting file system analysis")
            
            # Initialize analysis structure
            analysis = {
                'repository': {
                    'name': repo_name,
                    'full_name': f"{owner}/{repo_name}",
                    'description': f'Repository {owner}/{repo_name}',
                    'topics': [],
                    'html_url': repo_url
                },
                'api_endpoints': [],
                'documentation_files': [],
                'code_files': [],
                'openapi_specs': [],
                'readme_content': '',
                'languages': [],
                'topics': []
            }
            
            # Perform comprehensive file system analysis
            await self._analyze_repository_filesystem(repo_path, analysis)
            
            logger.info(f"Local analysis completed. Found {len(analysis['api_endpoints'])} API endpoints")
            return analysis
            
        except Exception as e:
            logger.error(f"Error during local repository analysis: {e}")
            return {}
        finally:
            # Clean up temporary directory with retry mechanism
            if temp_dir and os.path.exists(temp_dir):
                await self._cleanup_temp_directory(temp_dir)
    
    async def _cleanup_temp_directory(self, temp_dir: str):
        """Clean up temporary directory with retry mechanism and cross-platform support"""
        import time
        
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # On Windows, we need to handle file permissions and locks
                if os.name == 'nt':  # Windows
                    self._cleanup_windows_directory(temp_dir)
                else:  # Unix-like systems
                    shutil.rmtree(temp_dir)
                
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
                return
                
            except PermissionError as e:
                if attempt < max_retries - 1:
                    logger.debug(f"Permission error on attempt {attempt + 1}, retrying in {retry_delay}s: {e}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.warning(f"Failed to clean up temporary directory after {max_retries} attempts: {e}")
                    
            except OSError as e:
                if attempt < max_retries - 1:
                    logger.debug(f"OS error on attempt {attempt + 1}, retrying in {retry_delay}s: {e}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.warning(f"Failed to clean up temporary directory after {max_retries} attempts: {e}")
                    
            except Exception as e:
                logger.warning(f"Unexpected error cleaning up temporary directory: {e}")
                break
    
    def _cleanup_windows_directory(self, temp_dir: str):
        """Windows-specific directory cleanup that handles file locks and permissions"""
        def on_error(func, path, exc_info):
            """Error handler for shutil.rmtree on Windows"""
            if not os.access(path, os.W_OK):
                # Make file writable
                os.chmod(path, stat.S_IWRITE)
            if os.path.exists(path):
                try:
                    # Try to remove read-only files
                    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
                    os.unlink(path)
                except:
                    pass
        
        # First, try to remove .git directory specifically (common source of locks)
        git_dir = os.path.join(temp_dir, '.git')
        if os.path.exists(git_dir):
            try:
                # Remove .git directory with error handling
                shutil.rmtree(git_dir, onerror=on_error)
            except Exception as e:
                logger.debug(f"Could not remove .git directory: {e}")
        
        # Then remove the entire directory
        shutil.rmtree(temp_dir, onerror=on_error)
    
    async def _clone_repository(self, repo_url: str, repo_path: str) -> bool:
        """Clone repository using git"""
        try:
            # Ensure git is available
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Git is not available on the system")
                return False
            
            # Clone the repository
            cmd = ['git', 'clone', '--depth', '1', repo_url, repo_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            if result.returncode == 0:
                logger.info("Repository cloned successfully")
                return True
            else:
                logger.error(f"Failed to clone repository: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Repository cloning timed out")
            return False
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            return False
    
    async def _analyze_repository_filesystem(self, repo_path: str, analysis: Dict[str, Any]):
        """Analyze repository using file system operations"""
        logger.info(f"Analyzing repository filesystem: {repo_path}")
        
        if not os.path.exists(repo_path):
            logger.error(f"Repository path does not exist: {repo_path}")
            return
        
        # Get README content
        await self._extract_readme_from_filesystem(repo_path, analysis)
        
        # Find and analyze all code files
        await self._find_and_analyze_code_files(repo_path, analysis)
        
        # Find and analyze documentation files
        await self._find_and_analyze_documentation_files(repo_path, analysis)
        
        # Find and analyze configuration files
        await self._find_and_analyze_config_files(repo_path, analysis)
        
        # Find and analyze API specification files
        await self._find_and_analyze_api_specs(repo_path, analysis)
    
    async def _extract_readme_from_filesystem(self, repo_path: str, analysis: Dict[str, Any]):
        """Extract README content from filesystem"""
        readme_files = [
            'README.md', 'readme.md', 'README.txt', 'readme.txt',
            'README.rst', 'readme.rst', 'README.adoc', 'readme.adoc'
        ]
        
        for readme_file in readme_files:
            readme_path = os.path.join(repo_path, readme_file)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        analysis['readme_content'] = content
                        logger.info(f"Found README: {readme_file}")
                        break
                except Exception as e:
                    logger.warning(f"Failed to read README {readme_file}: {e}")
    
    async def _find_and_analyze_code_files(self, repo_path: str, analysis: Dict[str, Any]):
        """Find and analyze all code files in the repository"""
        logger.info("Searching for code files in repository")
        
        # Code file extensions to search for
        code_extensions = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.jsx': 'javascript', '.tsx': 'typescript', '.java': 'java',
            '.go': 'go', '.rb': 'ruby', '.php': 'php', '.cs': 'csharp',
            '.swift': 'swift', '.kt': 'kotlin', '.rs': 'rust',
            '.scala': 'scala', '.clj': 'clojure', '.hs': 'haskell',
            '.ml': 'ocaml', '.cpp': 'cpp', '.c': 'c', '.h': 'c',
            '.hpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp',
            # GraphQL and schema files
            '.graphql': 'graphql', '.gql': 'graphql', '.schema': 'graphql'
        }
        
        # API-related directories to prioritize
        api_directories = [
            'api', 'apis', 'routes', 'controllers', 'handlers', 'endpoints',
            'services', 'views', 'src', 'app', 'lib', 'backend', 'server',
            'graphql', 'resolvers', 'schemas', 'types', 'queries', 'mutations'
        ]
        
        code_files = []
        
        # Walk through the repository
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories that don't contain code
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.pytest_cache', 'target', 'build', 'dist']]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in code_extensions:
                    code_files.append({
                        'path': rel_path,
                        'full_path': file_path,
                        'language': code_extensions[file_ext],
                        'is_api_related': any(api_dir in rel_path.lower() for api_dir in api_directories)
                    })
        
        logger.info(f"Found {len(code_files)} code files")
        
        # Analyze code files for API endpoints
        for code_file in code_files:
            try:
                await self._analyze_code_file_for_endpoints(code_file, analysis)
            except Exception as e:
                logger.debug(f"Failed to analyze {code_file['path']}: {e}")
    
    async def _analyze_code_file_for_endpoints(self, code_file: Dict[str, Any], analysis: Dict[str, Any]):
        """Analyze a single code file for API endpoints with framework detection"""
        try:
            with open(code_file['full_path'], 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Detect framework and apply specialized analysis
            framework = self._detect_framework(content, code_file['path'])
            if framework:
                logger.debug(f"Detected framework: {framework} in {code_file['path']}")
            
            # Extract endpoints from the file content
            endpoints = self._extract_endpoints_from_file_content(content, code_file['path'])
            
            # Apply framework-specific analysis
            if framework == 'graphql':
                graphql_endpoints = self._analyze_graphql_file(content, code_file['path'])
                endpoints.extend(graphql_endpoints)
            elif framework == 'apollo':
                apollo_endpoints = self._analyze_apollo_file(content, code_file['path'])
                endpoints.extend(apollo_endpoints)
            elif framework == 'koa':
                koa_endpoints = self._analyze_koa_file(content, code_file['path'])
                endpoints.extend(koa_endpoints)
            
            if endpoints:
                analysis['api_endpoints'].extend(endpoints)
                logger.info(f"Found {len(endpoints)} endpoints in {code_file['path']} (framework: {framework})")
            
            # Add to code files list
            analysis['code_files'].append({
                'name': os.path.basename(code_file['path']),
                'path': code_file['path'],
                'type': 'code',
                'language': code_file['language'],
                'framework': framework,
                'branch': 'local'
            })
            
        except Exception as e:
            logger.debug(f"Failed to read or analyze {code_file['path']}: {e}")
    
    def _detect_framework(self, content: str, file_path: str) -> Optional[str]:
        """Detect the framework used in the file with improved accuracy"""
        content_lower = content.lower()
        file_lower = file_path.lower()
        
        # First, check for explicit framework imports/requires to avoid false positives
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
            'fastapi': [
                'from fastapi import', 'import fastapi', 'fastapi()', 'fastapi.fastapi',
                '@app.get', '@app.post', '@app.put', '@app.delete', '@app.patch'
            ],
            'flask': [
                'from flask import', 'import flask', 'flask()', 'flask.flask',
                '@app.route', '@blueprint.route', 'flask.blueprint'
            ],
            'django': [
                'from django', 'import django', 'django.conf', 'django.http',
                'path(', 'url(', 'include(', 'django.urls'
            ],
            'spring': [
                '@springbootapplication', '@restcontroller', '@controller',
                '@requestmapping', '@getmapping', '@postmapping', 'springframework'
            ],
            'gin': [
                'gin.engine', 'gin.new()', 'gin.default()', 'gin.group',
                'router.get', 'router.post', 'gin.context'
            ],
            'laravel': [
                'use laravel', 'laravel\\', 'route::', 'controller::',
                'middleware', 'laravel.foundation'
            ],
            'rails': [
                'rails.application', 'rails::application', 'resources :',
                'get \'', 'post \'', 'rails generate'
            ],
            'graphql': [
                'graphql', 'gql`', 'type query', 'type mutation', 'type subscription',
                'apollo-server', 'apolloserver', 'typedefs', 'resolvers'
            ]
        }
        
        # Count indicators for each framework
        framework_scores = {}
        for framework, indicators in framework_indicators.items():
            score = sum(1 for indicator in indicators if indicator in content_lower)
            if score > 0:
                framework_scores[framework] = score
        
        # If we have clear framework indicators, return the highest scoring one
        if framework_scores:
            # Prioritize REST frameworks over GraphQL to avoid false positives
            rest_frameworks = ['express', 'koa', 'fastapi', 'flask', 'django', 'spring', 'gin', 'laravel', 'rails']
            rest_scores = {k: v for k, v in framework_scores.items() if k in rest_frameworks}
            
            if rest_scores:
                return max(rest_scores.items(), key=lambda x: x[1])[0]
            elif 'graphql' in framework_scores:
                return 'graphql'
        
        # Fallback to file extension and content patterns
        if file_lower.endswith(('.graphql', '.gql', '.schema')):
            return 'graphql'
        
        # Check for specific patterns that indicate REST APIs
        rest_patterns = [
            r'\.(get|post|put|delete|patch)\([\'"`]',  # Express/Koa patterns
            r'@(get|post|put|delete|patch)\([\'"`]',   # FastAPI patterns
            r'@route\([\'"`]',                         # Flask patterns
            r'@(get|post|put|delete|patch)mapping',    # Spring patterns
            r'\.(get|post|put|delete|patch)\([\'"`]',  # Gin patterns
            r'route::(get|post|put|delete|patch)',     # Laravel patterns
            r'(get|post|put|delete|patch)\s+[\'"`]',   # Rails patterns
        ]
        
        for pattern in rest_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # Determine framework based on context
                if 'express' in content_lower or 'require(' in content_lower:
                    return 'express'
                elif 'koa' in content_lower:
                    return 'koa'
                elif 'fastapi' in content_lower or '@app.' in content_lower:
                    return 'fastapi'
                elif 'flask' in content_lower or '@route' in content_lower:
                    return 'flask'
                elif 'django' in content_lower or 'path(' in content_lower:
                    return 'django'
                elif 'spring' in content_lower or '@' in content_lower:
                    return 'spring'
                elif 'gin' in content_lower:
                    return 'gin'
                elif 'laravel' in content_lower or 'route::' in content_lower:
                    return 'laravel'
                elif 'rails' in content_lower:
                    return 'rails'
        
        return None
    
    def _analyze_graphql_file(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Specialized analysis for GraphQL files"""
        endpoints = []
        
        # Extract GraphQL schema definitions
        schema_patterns = [
            r'type\s+(\w+)\s*\{([^}]+)\}',
            r'input\s+(\w+)\s*\{([^}]+)\}',
            r'interface\s+(\w+)\s*\{([^}]+)\}',
            r'enum\s+(\w+)\s*\{([^}]+)\}'
        ]
        
        for pattern in schema_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for type_name, fields in matches:
                if type_name.lower() in ['query', 'mutation', 'subscription']:
                    # Extract field names from the type definition
                    field_matches = re.findall(r'(\w+)(?:\s*:\s*\w+)?(?:\s*\([^)]*\))?', fields)
                    for field in field_matches:
                        if field and field not in ['type', 'input', 'interface', 'enum']:
                            endpoint = APIEndpoint(
                                url=f"/graphql",
                                method=HTTPMethod.POST,
                                description=f"GraphQL {type_name}: {field}",
                                authentication_required=False,
                                tags=['graphql', type_name.lower(), field.lower()]
                            )
                            endpoints.append(endpoint)
        
        return endpoints
    
    def _analyze_apollo_file(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Specialized analysis for Apollo Server files"""
        endpoints = []
        
        # Extract Apollo Server resolvers
        resolver_patterns = [
            r'Query\s*:\s*\{([^}]+)\}',
            r'Mutation\s*:\s*\{([^}]+)\}',
            r'Subscription\s*:\s*\{([^}]+)\}',
            r'resolvers\s*=\s*\{([^}]+)\}'
        ]
        
        for pattern in resolver_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Extract resolver function names
                resolver_matches = re.findall(r'(\w+)\s*:\s*function|\w+\s*:\s*\([^)]*\)\s*=>|\w+\s*:\s*async\s*\([^)]*\)', match)
                for resolver in resolver_matches:
                    if resolver and resolver not in ['Query', 'Mutation', 'Subscription']:
                        endpoint = APIEndpoint(
                            url=f"/graphql",
                            method=HTTPMethod.POST,
                            description=f"Apollo resolver: {resolver}",
                            authentication_required=False,
                            tags=['apollo', 'resolver', resolver.lower()]
                        )
                        endpoints.append(endpoint)
        
        return endpoints
    
    def _analyze_koa_file(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Specialized analysis for Koa.js files"""
        endpoints = []
        
        # Koa router patterns
        koa_patterns = [
            r'router\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
            r'\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
            r'@koa/(\w+)',
            r'koa-router'
        ]
        
        for pattern in koa_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    method = match[0].upper()
                    path = match[1]
                    endpoint = APIEndpoint(
                        url=path,
                        method=HTTPMethod(method),
                        description=f"Koa {method} endpoint: {path}",
                        authentication_required=False,
                        tags=['koa', method.lower(), path.lower()]
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    async def _find_and_analyze_documentation_files(self, repo_path: str, analysis: Dict[str, Any]):
        """Find and analyze documentation files"""
        logger.info("Searching for documentation files")
        
        doc_patterns = [
            'api.md', 'API.md', 'endpoints.md', 'routes.md', 'api-docs.md',
            'rest-api.md', 'graphql.md', 'swagger.md', 'postman.md',
            'insomnia.md', 'setup.md', 'installation.md'
        ]
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]
            
            for file in files:
                if any(pattern in file.lower() for pattern in doc_patterns):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Extract API endpoints from documentation
                        await self._extract_apis_from_docs(content, analysis)
                        
                        analysis['documentation_files'].append({
                            'name': file,
                            'path': rel_path,
                            'type': 'documentation'
                        })
                        
                        logger.info(f"Analyzed documentation file: {rel_path}")
                        
                    except Exception as e:
                        logger.debug(f"Failed to read documentation file {rel_path}: {e}")
    
    async def _find_and_analyze_config_files(self, repo_path: str, analysis: Dict[str, Any]):
        """Find and analyze configuration files"""
        logger.info("Searching for configuration files")
        
        config_files = [
            'package.json', 'requirements.txt', 'go.mod', 'Cargo.toml',
            'pom.xml', 'composer.json', 'Gemfile', 'build.gradle',
            'docker-compose.yml', 'Dockerfile', 'nginx.conf', 'apache.conf',
            '.env.example', 'config.yml', 'config.yaml'
        ]
        
        for config_file in config_files:
            config_path = os.path.join(repo_path, config_file)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Parse configuration file
                    if config_file == 'package.json':
                        await self._parse_package_json(content, analysis)
                    elif config_file == 'requirements.txt':
                        await self._parse_requirements_txt(content, analysis)
                    
                    analysis['code_files'].append({
                        'name': config_file,
                        'path': config_file,
                        'type': 'config',
                        'branch': 'local'
                    })
                    
                    logger.info(f"Analyzed configuration file: {config_file}")
                    
                except Exception as e:
                    logger.debug(f"Failed to read config file {config_file}: {e}")
    
    async def _find_and_analyze_api_specs(self, repo_path: str, analysis: Dict[str, Any]):
        """Find and analyze API specification files"""
        logger.info("Searching for API specification files")
        
        spec_patterns = [
            'swagger.json', 'swagger.yaml', 'swagger.yml',
            'openapi.json', 'openapi.yaml', 'openapi.yml',
            'api-docs.json', 'api-docs.yaml', 'api-docs.yml'
        ]
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules']]
            
            for file in files:
                if any(pattern in file.lower() for pattern in spec_patterns):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Parse API specification
                        await self._parse_api_spec(content, file, analysis)
                        
                        logger.info(f"Analyzed API spec: {rel_path}")
                        
                    except Exception as e:
                        logger.debug(f"Failed to read API spec {rel_path}: {e}")
    
    async def _get_readme_raw_github(self, owner: str, repo_name: str) -> Optional[str]:
        """Get README content using raw GitHub URLs"""
        try:
            session = await self._get_session()
            readme_urls = [
                f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/README.md",
                f"https://raw.githubusercontent.com/{owner}/{repo_name}/master/README.md",
                f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/readme.md",
                f"https://raw.githubusercontent.com/{owner}/{repo_name}/master/readme.md"
            ]
            
            for url in readme_urls:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            logger.info(f"Found README at {url}")
                            return content
                except Exception as e:
                    logger.debug(f"Failed to fetch {url}: {e}")
                    continue
            
            logger.debug("No README found via raw GitHub")
            return None
        except Exception as e:
            logger.error(f"Error getting README via raw GitHub: {e}")
            return None
    
    async def _analyze_repo_structure_raw_github(self, owner: str, repo_name: str, analysis: Dict[str, Any]):
        """Analyze repository structure using raw GitHub URLs with comprehensive search"""
        logger.info("Performing comprehensive repository structure analysis")
        
        # Extended file patterns for deeper search
        file_patterns = [
            # API-related files
            ('package.json', 'javascript'),
            ('requirements.txt', 'python'),
            ('go.mod', 'go'),
            ('Cargo.toml', 'rust'),
            ('pom.xml', 'java'),
            ('composer.json', 'php'),
            ('Gemfile', 'ruby'),
            ('swagger.json', 'api'),
            ('openapi.json', 'api'),
            ('swagger.yaml', 'api'),
            ('openapi.yaml', 'api'),
            ('api.md', 'documentation'),
            ('README.md', 'documentation'),
            ('API.md', 'documentation'),
            ('docs/api.md', 'documentation'),
            ('docs/API.md', 'documentation'),
            ('documentation/api.md', 'documentation'),
            ('api-docs.md', 'documentation'),
            ('endpoints.md', 'documentation'),
            ('routes.md', 'documentation'),
            # Common directories and files
            ('src/', 'code'),
            ('app/', 'code'),
            ('api/', 'code'),
            ('routes/', 'code'),
            ('controllers/', 'code'),
            ('services/', 'code'),
            ('handlers/', 'code'),
            ('views/', 'code'),
            ('endpoints/', 'code'),
            ('main.py', 'python'),
            ('app.py', 'python'),
            ('server.py', 'python'),
            ('index.js', 'javascript'),
            ('server.js', 'javascript'),
            ('app.js', 'javascript'),
            ('main.go', 'go'),
            ('main.rs', 'rust'),
            ('Application.java', 'java'),
            ('index.php', 'php'),
            ('config/', 'config'),
            ('tests/', 'tests'),
            ('test/', 'tests')
        ]
        
        branches = ['main', 'master', 'develop']
        
        for branch in branches:
            for filename, file_type in file_patterns:
                try:
                    url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{branch}/{filename}"
                    session = await self._get_session()
                    
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            content = await response.text()
                            logger.info(f"Found {filename} in {branch} branch")
                            
                            if file_type == 'api':
                                # Parse API specifications
                                await self._parse_api_spec(content, filename, analysis)
                            elif file_type == 'javascript':
                                # Parse package.json for API info
                                await self._parse_package_json(content, analysis)
                            elif file_type == 'python':
                                # Parse requirements.txt for API libraries
                                await self._parse_requirements_txt(content, analysis)
                            elif file_type == 'documentation':
                                # Extract API endpoints from documentation
                                await self._extract_apis_from_docs(content, analysis)
                            
                            # Add to code files
                            analysis['code_files'].append({
                                'name': filename,
                                'path': filename,
                                'type': file_type,
                                'branch': branch
                            })
                            
                except Exception as e:
                    logger.debug(f"Failed to check {filename} in {branch}: {e}")
                    continue
        
        # Perform deep code analysis
        await self._deep_code_analysis(owner, repo_name, analysis)
    
    def _extract_repo_info(self, repo_url: str) -> tuple[Optional[str], Optional[str]]:
        """Extract owner and repository name from GitHub URL"""
        try:
            # Handle various GitHub URL formats
            if 'github.com' in repo_url:
                path = urlparse(repo_url).path.strip('/')
                parts = path.split('/')
                if len(parts) >= 2:
                    return parts[0], parts[1]
            elif 'api.github.com' in repo_url:
                # Handle GitHub API URLs
                path = urlparse(repo_url).path.strip('/')
                parts = path.split('/')
                if len(parts) >= 3 and parts[0] == 'repos':
                    return parts[1], parts[2]
        except Exception as e:
            logger.error(f"Error extracting repo info from {repo_url}: {e}")
        
        return None, None
    
    async def _get_repository_info(self, owner: str, repo_name: str) -> Optional[Dict[str, Any]]:
        """Get repository information from GitHub API"""
        try:
            session = await self._get_session()
            url = f"{self.github_api_base}/repos/{owner}/{repo_name}"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to get repo info: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting repository info: {e}")
            return None
    
    async def _get_repository_languages(self, owner: str, repo_name: str) -> List[str]:
        """Get repository programming languages"""
        try:
            session = await self._get_session()
            url = f"{self.github_api_base}/repos/{owner}/{repo_name}/languages"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    languages_data = await response.json()
                    return list(languages_data.keys())
                else:
                    logger.warning(f"Failed to get languages: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting repository languages: {e}")
            return []
    
    async def _get_readme_content(self, owner: str, repo_name: str) -> Optional[str]:
        """Get README content from repository"""
        try:
            session = await self._get_session()
            url = f"{self.github_api_base}/repos/{owner}/{repo_name}/readme"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    readme_data = await response.json()
                    if 'content' in readme_data:
                        # Decode base64 content
                        content = base64.b64decode(readme_data['content']).decode('utf-8')
                        return content
                else:
                    logger.debug(f"No README found: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting README content: {e}")
            return None
    
    async def _search_api_files(self, owner: str, repo_name: str, analysis: Dict[str, Any]):
        """Search for API-related files in the repository"""
        logger.info("Searching for API-related files...")
        
        # Search for common API documentation files
        api_file_patterns = [
            'api.md', 'api.txt', 'api.rst', 'api.adoc',
            'endpoints.md', 'endpoints.txt',
            'swagger.json', 'swagger.yaml', 'swagger.yml',
            'openapi.json', 'openapi.yaml', 'openapi.yml',
            'postman.json', 'insomnia.json',
            'api-docs.md', 'api-docs.txt',
            'rest-api.md', 'rest-api.txt',
            'graphql.md', 'graphql.txt'
        ]
        
        for pattern in api_file_patterns:
            files = await self._search_repository_files(owner, repo_name, pattern)
            analysis['documentation_files'].extend(files)
        
        logger.info(f"Found {len(analysis['documentation_files'])} documentation files")
    
    async def _search_openapi_specs(self, owner: str, repo_name: str, analysis: Dict[str, Any]):
        """Search for OpenAPI/Swagger specifications"""
        logger.info("Searching for OpenAPI/Swagger specifications...")
        
        openapi_patterns = [
            'swagger.json', 'swagger.yaml', 'swagger.yml',
            'openapi.json', 'openapi.yaml', 'openapi.yml',
            'api-docs.json', 'api-docs.yaml', 'api-docs.yml'
        ]
        
        for pattern in openapi_patterns:
            files = await self._search_repository_files(owner, repo_name, pattern)
            for file_info in files:
                spec_content = await self._get_file_content(owner, repo_name, file_info['path'])
                if spec_content:
                    try:
                        if pattern.endswith('.json'):
                            spec_data = json.loads(spec_content)
                        else:
                            spec_data = yaml.safe_load(spec_content)
                        
                        analysis['openapi_specs'].append({
                            'file': file_info,
                            'spec': spec_data
                        })
                        logger.info(f"Found OpenAPI spec: {file_info['path']}")
                        
                        # Extract endpoints from the spec
                        endpoints = self._extract_endpoints_from_openapi(spec_data, file_info['path'])
                        analysis['api_endpoints'].extend(endpoints)
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse OpenAPI spec {file_info['path']}: {e}")
        
        logger.info(f"Found {len(analysis['openapi_specs'])} OpenAPI specifications")
    
    async def _extract_endpoints_from_code(self, owner: str, repo_name: str, analysis: Dict[str, Any]):
        """Extract API endpoints from code files"""
        logger.info("Extracting API endpoints from code files...")
        
        # Search for code files that might contain API endpoints
        code_patterns = [
            '*.py', '*.js', '*.ts', '*.java', '*.go', '*.rb', '*.php',
            '*.cs', '*.swift', '*.kt', '*.rs', '*.scala', '*.clj'
        ]
        
        for pattern in code_patterns:
            files = await self._search_repository_files(owner, repo_name, pattern)
            analysis['code_files'].extend(files)
        
        # Analyze a subset of code files for API endpoints
        code_files_to_analyze = analysis['code_files'][:20]  # Limit to first 20 files
        
        for file_info in code_files_to_analyze:
            content = await self._get_file_content(owner, repo_name, file_info['path'])
            if content:
                endpoints = self._extract_endpoints_from_file_content(content, file_info['path'])
                analysis['api_endpoints'].extend(endpoints)
        
        logger.info(f"Analyzed {len(code_files_to_analyze)} code files")
    
    async def _search_repository_files(self, owner: str, repo_name: str, pattern: str) -> List[Dict[str, Any]]:
        """Search for files in repository using GitHub API"""
        try:
            session = await self._get_session()
            url = f"{self.github_api_base}/search/code"
            params = {
                'q': f'repo:{owner}/{repo_name} filename:{pattern}',
                'per_page': 100
            }
            
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('items', [])
                else:
                    logger.warning(f"Search failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching repository files: {e}")
            return []
    
    async def _get_file_content(self, owner: str, repo_name: str, file_path: str) -> Optional[str]:
        """Get file content from repository"""
        try:
            session = await self._get_session()
            url = f"{self.github_api_base}/repos/{owner}/{repo_name}/contents/{file_path}"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    file_data = await response.json()
                    if 'content' in file_data:
                        # Decode base64 content
                        content = base64.b64decode(file_data['content']).decode('utf-8')
                        return content
                else:
                    logger.debug(f"Failed to get file content for {file_path}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting file content for {file_path}: {e}")
            return None
    
    def _extract_endpoints_from_openapi(self, spec: Dict[str, Any], file_path: str) -> List[APIEndpoint]:
        """Extract API endpoints from OpenAPI specification"""
        endpoints = []
        
        if 'paths' not in spec:
            return endpoints
        
        for path, methods in spec['paths'].items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    endpoint = APIEndpoint(
                        url=path,  # This will be relative path
                        method=HTTPMethod(method.upper()),
                        description=details.get('summary', details.get('description', '')),
                        parameters=self._extract_parameters_from_openapi(details),
                        request_body=details.get('requestBody'),
                        response_schema=self._extract_response_schema_from_openapi(details),
                        authentication_required=self._has_auth_requirement(details),
                        tags=details.get('tags', []) + ['openapi']
                    )
                    endpoints.append(endpoint)
        
        logger.info(f"Extracted {len(endpoints)} endpoints from OpenAPI spec: {file_path}")
        return endpoints
    
    def _extract_parameters_from_openapi(self, details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
    
    def _extract_response_schema_from_openapi(self, details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
    
    def _extract_endpoints_from_file_content(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Extract API endpoints from file content using AST-first with robust fallbacks."""
        # 1) Try Enhanced V2 (preferred)
        try:
            from .enhanced_analyzer_v2 import EnhancedAPIAnalyzerV2
            v2 = EnhancedAPIAnalyzerV2()
            enhanced = v2.analyze_file(file_path, content)
            if enhanced:
                eps = v2.convert_to_api_endpoints(enhanced)
                logger.info(f"AST v2 extracted {len(eps)} endpoints from {file_path}")
                return eps
        except Exception as e:
            logger.debug(f"AST v2 failed on {file_path}: {e}")

        # 2) Try Enhanced V1
        try:
            from .enhanced_analyzer import EnhancedAPIAnalyzer
            v1 = EnhancedAPIAnalyzer()
            enhanced = v1.analyze_file(file_path, content)
            if enhanced:
                eps = v1.convert_to_api_endpoints(enhanced)
                logger.info(f"AST v1 extracted {len(eps)} endpoints from {file_path}")
                return eps
        except Exception as e:
            logger.debug(f"AST v1 failed on {file_path}: {e}")

        # 3) Parameter-aware regex extraction
        try:
            regex_eps = self._extract_endpoints_with_params_regex(content, file_path)
            if regex_eps:
                logger.info(f"Regex extracted {len(regex_eps)} endpoints from {file_path}")
                return regex_eps
        except Exception as e:
            logger.debug(f"Regex with params failed on {file_path}: {e}")

        # 4) Legacy regex fallback
        logger.info(f"Falling back to legacy regex for {file_path}")
        return self._extract_endpoints_regex_fallback(content, file_path)
    
    def _extract_endpoints_with_params_regex(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Extracts API endpoints and their parameter signatures using targeted regex."""
        endpoints = []
        # Regex to find decorators (@router.get, etc.) and the entire function signature
        decorator_and_func_sig_pattern = re.compile(
            r"@(\w+)\.(get|post|put|delete|patch)\s*\(\s*\"([^\"]+)\"[\s\S]*?\)\s*"
            r"async def\s+(\w+)\s*\(([\s\S]*?)\):",
            re.MULTILINE
        )

        matches = decorator_and_func_sig_pattern.finditer(content)

        for match in matches:
            router_var, method, url, func_name, params_str = match.groups()
            method = method.upper()
            
            parameters = {}
            # Regex to extract individual parameters from the signature string
            param_pattern = re.compile(r"(\w+)\s*:\s*([\w\.\[\]]+)")
            param_matches = param_pattern.finditer(params_str)
            for param_match in param_matches:
                param_name, param_type = param_match.groups()
                parameters[param_name] = {
                    "type": param_type,
                    "source": "body" if method in ["POST", "PUT", "PATCH"] else "query", # Simplified source detection
                    "required": True # Assume required for simplicity
                }

            endpoint = APIEndpoint(
                url=url,
                method=HTTPMethod(method),
                description=f"Extracted via regex from {func_name} in {file_path}",
                parameters=parameters,
            )
            endpoints.append(endpoint)
            
        return endpoints
    
    def _extract_endpoints_regex_fallback(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Fallback regex-based endpoint extraction with improved patterns"""
        endpoints = []
        
        # Enhanced API endpoint patterns for different languages and frameworks
        patterns = {
            'python': [
                # FastAPI patterns
                r'@app\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'@api\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'@router\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'@(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                # Flask patterns
                r'@route\([\'"`]([^\'"`]+)[\'"`],\s*methods\s*=\s*\[[^\]]*[\'"`](GET|POST|PUT|DELETE|PATCH)[\'"`]',
                r'@(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'Blueprint\([\'"`]([^\'"`]+)[\'"`]',
                r'@(get|post|put|delete|patch)_(endpoint|route)\([\'"`]([^\'"`]+)[\'"`]',
                # Django patterns
                r'path\([\'"`]([^\'"`]+)[\'"`],\s*views\.([^,\s]+)',
                r'url\([\'"`]([^\'"`]+)[\'"`],\s*views\.([^,\s]+)',
                r're_path\([\'"`]([^\'"`]+)[\'"`],\s*views\.([^,\s]+)',
                # Generic patterns
                r'router\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'api\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]'
            ],
            'javascript': [
                # Express.js patterns
                r'\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'router\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'app\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'express\.Router\(\)\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'const\s+router\s*=\s*express\.Router\(\)',
                # Koa patterns
                r'router\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                # Hapi patterns
                r'server\.route\(\s*\{[\s\S]*?path:\s*[\'"`]([^\'"`]+)[\'"`][\s\S]*?method:\s*[\'"`]([^\'"`]+)[\'"`]',
                # NestJS patterns
                r'@(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]\)',
                r'@Controller\([\'"`]([^\'"`]+)[\'"`]\)',
                # Generic patterns
                r'@(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'@(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'api\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]'
            ],
            'java': [
                # Spring Boot patterns
                r'@(Get|Post|Put|Delete|Patch)Mapping\([\'"`]([^\'"`]+)[\'"`]',
                r'@RequestMapping\([\'"`]([^\'"`]+)[\'"`]',
                r'@RestController.*?@RequestMapping\([\'"`]([^\'"`]+)[\'"`]',
                r'@Controller.*?@RequestMapping\([\'"`]([^\'"`]+)[\'"`]',
                r'@(Get|Post|Put|Delete|Patch)Mapping\(value\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
                r'@RequestMapping\(value\s*=\s*[\'"`]([^\'"`]+)[\'"`]',
                # JAX-RS patterns
                r'@(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'@Path\([\'"`]([^\'"`]+)[\'"`]',
                # Micronaut patterns
                r'@(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'@Controller\([\'"`]([^\'"`]+)[\'"`]'
            ],
            'csharp': [
                # ASP.NET Core patterns
                r'\[(Get|Post|Put|Delete|Patch)\("([^"]+)"\)\]',
                r'\[Route\("([^"]+)"\)\]',
                r'\[ApiController\]',
                r'\[Controller\]',
                r'public\s+class\s+\w+Controller\s*:\s*ControllerBase',
                r'public\s+class\s+\w+Controller\s*:\s*Controller',
                # Web API patterns
                r'\[HttpGet\("([^"]+)"\)\]',
                r'\[HttpPost\("([^"]+)"\)\]',
                r'\[HttpPut\("([^"]+)"\)\]',
                r'\[HttpDelete\("([^"]+)"\)\]',
                r'\[HttpPatch\("([^"]+)"\)\]'
            ],
            'go': [
                # Gin patterns
                r'\.(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'router\.(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'group\.(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                # Echo patterns
                r'\.(GET|POST|PUT|DELETE|PATCH)\([\'"`]([^\'"`]+)[\'"`]',
                r'group\.(GET|POST|PUT|DELETE|PATCH)\([\'"`]([^\'"`]+)[\'"`]',
                # Gorilla Mux patterns
                r'\.HandleFunc\([\'"`]([^\'"`]+)[\'"`]',
                r'\.Methods\([\'"`]([^\'"`]+)[\'"`]',
                # Standard library patterns
                r'http\.(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'HandleFunc\([\'"`]([^\'"`]+)[\'"`]',
                r'\.Handle\([\'"`]([^\'"`]+)[\'"`]'
            ],
            'php': [
                # Laravel patterns
                r'Route::(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'\$router->(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'Route::group\([\'"`]([^\'"`]+)[\'"`]',
                # Symfony patterns
                r'@Route\([\'"`]([^\'"`]+)[\'"`]',
                r'@(Get|Post|Put|Delete|Patch)\([\'"`]([^\'"`]+)[\'"`]',
                # Slim patterns
                r'\$app->(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'\$app->group\([\'"`]([^\'"`]+)[\'"`]'
            ],
            'ruby': [
                # Rails patterns
                r'(get|post|put|delete|patch)\s+[\'"`]([^\'"`]+)[\'"`]',
                r'resources\s+:([^\s]+)',
                r'resource\s+:([^\s]+)',
                r'namespace\s+:([^\s]+)',
                r'scope\s+:([^\s]+)',
                # Sinatra patterns
                r'(get|post|put|delete|patch)\s+[\'"`]([^\'"`]+)[\'"`]',
                r'before\s+[\'"`]([^\'"`]+)[\'"`]'
            ],
            'rust': [
                # Actix-web patterns
                r'\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'web::resource\([\'"`]([^\'"`]+)[\'"`]',
                r'web::scope\([\'"`]([^\'"`]+)[\'"`]',
                # Rocket patterns
                r'#\[(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'#\[launch\]',
                # Warp patterns
                r'warp::path\([\'"`]([^\'"`]+)[\'"`]',
                r'\.and\(warp::(get|post|put|delete|patch)\(\)\)'
            ],
            'swift': [
                # Vapor patterns
                r'\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'router\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
                r'group\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]'
            ],
            'kotlin': [
                # Spring Boot Kotlin patterns
                r'@(Get|Post|Put|Delete|Patch)Mapping\([\'"`]([^\'"`]+)[\'"`]',
                r'@RequestMapping\([\'"`]([^\'"`]+)[\'"`]',
                r'@RestController',
                r'@Controller',
                # Ktor patterns
                r'get\([\'"`]([^\'"`]+)[\'"`]',
                r'post\([\'"`]([^\'"`]+)[\'"`]',
                r'put\([\'"`]([^\'"`]+)[\'"`]',
                r'delete\([\'"`]([^\'"`]+)[\'"`]',
                r'patch\([\'"`]([^\'"`]+)[\'"`]'
            ]
        }
        
        # Determine language from file extension with improved mapping
        file_ext = file_path.split('.')[-1].lower()
        language_patterns = {
            'py': patterns['python'],
            'js': patterns['javascript'],
            'ts': patterns['javascript'],
            'jsx': patterns['javascript'],
            'tsx': patterns['javascript'],
            'java': patterns['java'],
            'cs': patterns['csharp'],
            'go': patterns['go'],
            'php': patterns['php'],
            'rb': patterns['ruby'],
            'rs': patterns['rust'],
            'swift': patterns['swift'],
            'kt': patterns['kotlin'],
            'scala': patterns['java'],  # Scala similar to Java patterns
            'clj': patterns['ruby'],   # Clojure similar to Ruby patterns
            'hs': patterns['ruby'],    # Haskell similar to Ruby patterns
            'ml': patterns['ruby'],    # OCaml similar to Ruby patterns
            'cpp': patterns['java'],   # C++ similar to Java patterns
            'c': patterns['java'],     # C similar to Java patterns
            'h': patterns['java'],     # C header similar to Java patterns
            'hpp': patterns['java'],   # C++ header similar to Java patterns
            'cc': patterns['java'],    # C++ similar to Java patterns
            'cxx': patterns['java'],   # C++ similar to Java patterns
        }
        
        if file_ext in language_patterns:
            for pattern in language_patterns[file_ext]:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        method = match[0].upper()
                        path = match[1]
                    else:
                        method = 'GET'  # Default
                        path = match
                    
                    if path and not path.startswith('#'):  # Skip comments
                        endpoint = APIEndpoint(
                            url=path,
                            method=HTTPMethod(method),
                            description=f"Extracted from {file_path}",
                            authentication_required=False,
                            tags=['code', file_ext]
                        )
                        endpoints.append(endpoint)
        
        if endpoints:
            logger.debug(f"Regex fallback extracted {len(endpoints)} endpoints from {file_path}")
        
        # Only apply GraphQL analysis if the file is actually GraphQL-related and not a REST API
        if self._is_graphql_file(content, file_path) and not self._is_rest_api_file(content, file_path):
            graphql_endpoints = self._extract_graphql_endpoints(content, file_path)
            endpoints.extend(graphql_endpoints)
            logger.debug(f"Extracted {len(graphql_endpoints)} GraphQL endpoints from {file_path}")
        
        return endpoints
    
    def _is_rest_api_file(self, content: str, file_path: str) -> bool:
        """Check if a file is a REST API file to avoid GraphQL false positives"""
        content_lower = content.lower()
        
        # Strong REST API indicators
        rest_indicators = [
            'express', 'koa', 'fastapi', 'flask', 'django', 'spring', 'gin', 'laravel', 'rails',
            'router.get', 'router.post', 'app.get', 'app.post', '@app.get', '@app.post',
            'controller', 'restcontroller', 'api controller', 'web api',
            'route::', 'resources :', 'get \'', 'post \'',
            'httpget', 'httppost', 'requestmapping', 'getmapping', 'postmapping'
        ]
        
        # Count REST indicators
        rest_count = sum(1 for indicator in rest_indicators if indicator in content_lower)
        
        # If we have strong REST indicators, it's likely a REST API
        return rest_count >= 2
    
    def _is_graphql_file(self, content: str, file_path: str) -> bool:
        """Check if a file is GraphQL-related"""
        content_lower = content.lower()
        file_lower = file_path.lower()
        
        # Check file extension
        if file_lower.endswith(('.graphql', '.gql', '.schema')):
            return True
        
        # Check for GraphQL-specific patterns
        graphql_indicators = [
            'graphql',
            'gql`',
            'type query',
            'type mutation',
            'type subscription',
            'apollo-server',
            'apolloserver',
            'typedefs',
            'resolvers',
            'schema {',
            'extend type',
            'input type',
            'interface',
            'enum'
        ]
        
        # Count how many GraphQL indicators are present
        indicator_count = sum(1 for indicator in graphql_indicators if indicator in content_lower)
        
        # Consider it a GraphQL file if multiple indicators are present
        return indicator_count >= 2
    
    def _extract_graphql_endpoints(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Extract GraphQL endpoints and operations from file content"""
        endpoints = []
        content_lower = content.lower()
        
        # GraphQL schema patterns
        graphql_patterns = [
            # Type definitions
            r'type\s+Query\s*\{([^}]+)\}',
            r'type\s+Mutation\s*\{([^}]+)\}',
            r'type\s+Subscription\s*\{([^}]+)\}',
            # Field definitions
            r'(\w+)\s*:\s*(\w+)(?:\([^)]*\))?\s*:?\s*(\w+)',
            # Resolver patterns
            r'Query\s*:\s*\{([^}]+)\}',
            r'Mutation\s*:\s*\{([^}]+)\}',
            r'Subscription\s*:\s*\{([^}]+)\}',
            # Apollo Server patterns
            r'typeDefs\s*=\s*gql`([^`]+)`',
            r'resolvers\s*=\s*\{([^}]+)\}',
            # GraphQL operation patterns
            r'query\s+(\w+)\s*\{([^}]+)\}',
            r'mutation\s+(\w+)\s*\{([^}]+)\}',
            r'subscription\s+(\w+)\s*\{([^}]+)\}'
        ]
        
        for pattern in graphql_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) >= 2:
                        operation_name = match[0].strip()
                        operation_content = match[1].strip()
                        
                        # Extract field names from operation content
                        field_matches = re.findall(r'(\w+)\s*\([^)]*\)', operation_content)
                        if not field_matches:
                            field_matches = re.findall(r'(\w+)(?:\s*:\s*\w+)?', operation_content)
                        
                        for field in field_matches:
                            if field and field not in ['type', 'Query', 'Mutation', 'Subscription']:
                                endpoint = APIEndpoint(
                                    url=f"/graphql",
                                    method=HTTPMethod.POST,
                                    description=f"GraphQL {operation_name}: {field}",
                                    authentication_required=False,
                                    tags=['graphql', operation_name.lower(), field]
                                )
                                endpoints.append(endpoint)
                else:
                    # Handle single match case
                    if match and match not in ['type', 'Query', 'Mutation', 'Subscription']:
                        endpoint = APIEndpoint(
                            url=f"/graphql",
                            method=HTTPMethod.POST,
                            description=f"GraphQL operation: {match}",
                            authentication_required=False,
                            tags=['graphql', match.lower()]
                        )
                        endpoints.append(endpoint)
        
        # Look for specific GraphQL field patterns - only in GraphQL context
        if 'type' in content_lower or 'query' in content_lower or 'mutation' in content_lower:
            field_patterns = [
                r'(\w+)\s*:\s*\{[^}]*\}',  # Nested fields
                r'(\w+)\s*:\s*\[[^\]]*\]',  # Array fields
                r'(\w+)\s*:\s*\w+',        # Simple fields
            ]
            
            for pattern in field_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match and match not in ['type', 'Query', 'Mutation', 'Subscription', 'resolvers', 'input', 'interface', 'enum']:
                        endpoint = APIEndpoint(
                            url=f"/graphql",
                            method=HTTPMethod.POST,
                            description=f"GraphQL field: {match}",
                            authentication_required=False,
                            tags=['graphql', 'field', match.lower()]
                        )
                        endpoints.append(endpoint)
        
        if endpoints:
            logger.debug(f"Extracted {len(endpoints)} GraphQL endpoints from {file_path}")
        
        return endpoints
    
    async def _parse_api_spec(self, content: str, filename: str, analysis: Dict[str, Any]):
        """Parse API specification files"""
        try:
            if filename.endswith('.json'):
                spec_data = json.loads(content)
            else:
                spec_data = yaml.safe_load(content)
            
            analysis['openapi_specs'].append({
                'file': {'name': filename, 'path': filename},
                'spec': spec_data
            })
            
            # Extract endpoints from the spec
            endpoints = self._extract_endpoints_from_openapi(spec_data, filename)
            analysis['api_endpoints'].extend(endpoints)
            
            logger.info(f"Parsed API spec {filename}, found {len(endpoints)} endpoints")
        except Exception as e:
            logger.warning(f"Failed to parse API spec {filename}: {e}")
    
    async def _parse_package_json(self, content: str, analysis: Dict[str, Any]):
        """Parse package.json for API-related information"""
        try:
            package_data = json.loads(content)
            
            # Check for API-related dependencies
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            
            api_indicators = [
                'express', 'fastapi', 'flask', 'django', 'koa', 'hapi',
                'swagger', 'openapi', 'api', 'rest', 'graphql', 'apollo',
                'axios', 'fetch', 'request', 'superagent'
            ]
            
            found_apis = []
            for dep_name in dependencies:
                if any(indicator in dep_name.lower() for indicator in api_indicators):
                    found_apis.append(dep_name)
            
            for dep_name in dev_dependencies:
                if any(indicator in dep_name.lower() for indicator in api_indicators):
                    found_apis.append(dep_name)
            
            if found_apis:
                logger.info(f"Found API-related dependencies: {found_apis}")
                # Create a generic API endpoint based on dependencies
                endpoint = APIEndpoint(
                    url="/api",
                    method=HTTPMethod.GET,
                    description=f"API endpoints using {', '.join(found_apis[:3])}",
                    authentication_required=False,
                    tags=['package.json', 'dependencies']
                )
                analysis['api_endpoints'].append(endpoint)
                
        except Exception as e:
            logger.warning(f"Failed to parse package.json: {e}")
    
    async def _parse_requirements_txt(self, content: str, analysis: Dict[str, Any]):
        """Parse requirements.txt for API-related libraries"""
        try:
            lines = content.split('\n')
            api_indicators = [
                'fastapi', 'flask', 'django', 'rest', 'api', 'swagger',
                'openapi', 'requests', 'aiohttp', 'httpx'
            ]
            
            found_apis = []
            for line in lines:
                line = line.strip().lower()
                if any(indicator in line for indicator in api_indicators):
                    found_apis.append(line.split('==')[0].split('>=')[0].split('<=')[0])
            
            if found_apis:
                logger.info(f"Found API-related Python libraries: {found_apis}")
                # Create a generic API endpoint based on libraries
                endpoint = APIEndpoint(
                    url="/api",
                    method=HTTPMethod.GET,
                    description=f"API endpoints using {', '.join(found_apis[:3])}",
                    authentication_required=False,
                    tags=['requirements.txt', 'python']
                )
                analysis['api_endpoints'].append(endpoint)
                
        except Exception as e:
            logger.warning(f"Failed to parse requirements.txt: {e}")
    
    async def _extract_apis_from_docs(self, content: str, analysis: Dict[str, Any]):
        """Extract API endpoints from documentation"""
        try:
            # Enhanced API endpoint patterns for documentation
            api_patterns = [
                r'`([A-Z]+)\s+([^\s`]+)`',  # `GET /api/users`
                r'([A-Z]+)\s+([^\s\n]+)',   # GET /api/users
                r'endpoint[:\s]+([^\s\n]+)', # endpoint: /api/users
                r'route[:\s]+([^\s\n]+)',   # route: /api/users
                r'path[:\s]+([^\s\n]+)',    # path: /api/users
                r'URL[:\s]+([^\s\n]+)',     # URL: /api/users
                r'uri[:\s]+([^\s\n]+)',     # uri: /api/users
                r'endpoint[:\s]*`([^`]+)`', # endpoint: `/api/users`
                r'route[:\s]*`([^`]+)`',    # route: `/api/users`
                r'path[:\s]*`([^`]+)`',     # path: `/api/users`
                r'###\s*([A-Z]+)\s+([^\n]+)', # ### GET /api/users
                r'##\s*([A-Z]+)\s+([^\n]+)',  # ## POST /api/users
                r'#\s*([A-Z]+)\s+([^\n]+)',   # # PUT /api/users
                r'\[([A-Z]+)\s+([^\]]+)\]',   # [GET /api/users]
                r'\(([A-Z]+)\s+([^\)]+)\)',   # (POST /api/users)
            ]
            
            found_endpoints = []
            for pattern in api_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        method = match[0].upper()
                        path = match[1]
                    else:
                        method = 'GET'
                        path = match
                    
                    if path.startswith('/') and any(api_word in path.lower() for api_word in ['api', 'rest', 'v1', 'v2', 'endpoint']):
                        found_endpoints.append((method, path))
            
            # Remove duplicates
            unique_endpoints = list(set(found_endpoints))
            
            for method, path in unique_endpoints:
                endpoint = APIEndpoint(
                    url=path,
                    method=HTTPMethod(method),
                    description=f"API endpoint found in documentation",
                    authentication_required=False,
                    tags=['documentation']
                )
                analysis['api_endpoints'].append(endpoint)
            
            if found_endpoints:
                logger.info(f"Found {len(unique_endpoints)} API endpoints in documentation")
                
        except Exception as e:
            logger.warning(f"Failed to extract APIs from documentation: {e}")
    
    async def _deep_code_analysis(self, owner: str, repo_name: str, analysis: Dict[str, Any]):
        """Perform deep code analysis by exploring repository structure"""
        logger.info("Starting deep code analysis")
        
        # Common code file extensions to search for
        code_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb', '.php',
            '.cs', '.swift', '.kt', '.rs', '.scala', '.clj', '.hs', '.ml',
            '.cpp', '.c', '.h', '.hpp', '.cc', '.cxx'
        ]
        
        # Common API-related directories to explore
        api_directories = [
            'api', 'apis', 'routes', 'controllers', 'handlers', 'endpoints',
            'services', 'views', 'src', 'app', 'lib', 'backend', 'server'
        ]
        
        branches = ['main', 'master', 'develop', 'dev']
        
        for branch in branches:
            logger.info(f"Analyzing {branch} branch for code files")
            
            # First, try to get directory listing using GitHub's tree API
            try:
                await self._explore_directory_structure(owner, repo_name, branch, analysis, api_directories, code_extensions)
            except Exception as e:
                logger.warning(f"Failed to explore directory structure for {branch}: {e}")
            
            # Always try fallback file search as well
            await self._fallback_file_search(owner, repo_name, branch, analysis, code_extensions)
    
    async def _explore_directory_structure(self, owner: str, repo_name: str, branch: str, analysis: Dict[str, Any], api_dirs: List[str], code_exts: List[str]):
        """Explore repository directory structure recursively"""
        try:
            session = await self._get_session()
            
            # Get root directory contents
            url = f"https://api.github.com/repos/{owner}/{repo_name}/git/trees/{branch}?recursive=1"
            
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    tree_data = await response.json()
                    files = tree_data.get('tree', [])
                    
                    logger.info(f"Found {len(files)} files in {branch} branch")
                    
                    # Filter for code files and API-related directories
                    code_files = []
                    api_files = []
                    
                    for file_info in files:
                        file_path = file_info.get('path', '')
                        file_type = file_info.get('type', '')
                        
                        if file_type == 'blob':  # Regular file
                            # Check if it's a code file
                            if any(file_path.endswith(ext) for ext in code_exts):
                                code_files.append(file_path)
                            
                            # Check if it's in an API-related directory
                            if any(api_dir in file_path.lower() for api_dir in api_dirs):
                                api_files.append(file_path)
                    
                    logger.info(f"Found {len(code_files)} code files and {len(api_files)} API-related files")
                    
                    # Analyze code files for API endpoints
                    await self._analyze_code_files_for_apis(owner, repo_name, code_files, analysis)
                    
                    # Analyze API-related files specifically
                    await self._analyze_api_files(owner, repo_name, api_files, analysis)
                    
                else:
                    logger.warning(f"Failed to get tree for {branch}: {response.status}")
                    
        except Exception as e:
            logger.warning(f"Error exploring directory structure: {e}")
    
    async def _fallback_file_search(self, owner: str, repo_name: str, branch: str, analysis: Dict[str, Any], code_exts: List[str]):
        """Fallback method to search for common code files"""
        logger.info(f"Using fallback file search for {branch} branch")
        
        # Common file patterns to try
        common_files = [
            'main.py', 'app.py', 'server.py', 'api.py', 'routes.py',
            'index.js', 'server.js', 'app.js', 'api.js', 'routes.js',
            'main.go', 'server.go', 'api.go', 'routes.go',
            'main.rs', 'lib.rs', 'api.rs',
            'Application.java', 'Controller.java', 'Service.java',
            'index.php', 'api.php', 'routes.php'
        ]
        
        for filename in common_files:
            try:
                url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{branch}/{filename}"
                session = await self._get_session()
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"Found and analyzing {filename}")
                        
                        # Extract API endpoints from the file
                        endpoints = self._extract_endpoints_from_file_content(content, filename)
                        analysis['api_endpoints'].extend(endpoints)
                        
                        # Add to code files
                        analysis['code_files'].append({
                            'name': filename,
                            'path': filename,
                            'type': 'code',
                            'branch': branch
                        })
                        
            except Exception as e:
                logger.debug(f"Failed to fetch {filename}: {e}")
                continue
    
    async def _analyze_code_files_for_apis(self, owner: str, repo_name: str, code_files: List[str], analysis: Dict[str, Any]):
        """Analyze code files for API endpoints"""
        logger.info(f"Analyzing {len(code_files)} code files for API endpoints")
        
        # Limit to first 50 files to avoid overwhelming
        files_to_analyze = code_files[:50]
        
        for file_path in files_to_analyze:
            try:
                content = await self._get_file_content_raw_github(owner, repo_name, file_path)
                if content:
                    endpoints = self._extract_endpoints_from_file_content(content, file_path)
                    if endpoints:
                        analysis['api_endpoints'].extend(endpoints)
                        logger.info(f"Found {len(endpoints)} endpoints in {file_path}")
                        
                        # Add to code files
                        analysis['code_files'].append({
                            'name': file_path.split('/')[-1],
                            'path': file_path,
                            'type': 'code',
                            'branch': 'main'
                        })
                        
            except Exception as e:
                logger.debug(f"Failed to analyze {file_path}: {e}")
                continue
    
    async def _analyze_api_files(self, owner: str, repo_name: str, api_files: List[str], analysis: Dict[str, Any]):
        """Analyze files in API-related directories"""
        logger.info(f"Analyzing {len(api_files)} API-related files")
        
        for file_path in api_files:
            try:
                content = await self._get_file_content_raw_github(owner, repo_name, file_path)
                if content:
                    endpoints = self._extract_endpoints_from_file_content(content, file_path)
                    if endpoints:
                        analysis['api_endpoints'].extend(endpoints)
                        logger.info(f"Found {len(endpoints)} endpoints in API file {file_path}")
                        
            except Exception as e:
                logger.debug(f"Failed to analyze API file {file_path}: {e}")
                continue
    
    async def _analyze_repository_without_readme(self, owner: str, repo_name: str, analysis: Dict[str, Any]):
        """Analyze repository when no README is found"""
        logger.info("Analyzing repository without README file")
        
        # Try to find alternative documentation files
        doc_files = [
            'docs/README.md', 'docs/readme.md', 'documentation/README.md',
            'doc/README.md', 'api.md', 'API.md', 'endpoints.md', 'routes.md',
            'api-docs.md', 'rest-api.md', 'graphql.md', 'swagger.md',
            'postman.md', 'insomnia.md', 'setup.md', 'installation.md'
        ]
        
        for doc_file in doc_files:
            try:
                content = await self._get_file_content_raw_github(owner, repo_name, doc_file)
                if content:
                    logger.info(f"Found documentation file: {doc_file}")
                    await self._extract_apis_from_docs(content, analysis)
                    break
            except Exception as e:
                logger.debug(f"Failed to fetch {doc_file}: {e}")
                continue
        
        # Try to find configuration files that might indicate API structure
        config_files = [
            'package.json', 'requirements.txt', 'go.mod', 'Cargo.toml',
            'pom.xml', 'composer.json', 'Gemfile', 'build.gradle',
            'docker-compose.yml', 'dockerfile', 'Dockerfile',
            'nginx.conf', 'apache.conf', '.env.example', 'config.yml'
        ]
        
        for config_file in config_files:
            try:
                content = await self._get_file_content_raw_github(owner, repo_name, config_file)
                if content:
                    logger.info(f"Found configuration file: {config_file}")
                    if config_file == 'package.json':
                        await self._parse_package_json(content, analysis)
                    elif config_file == 'requirements.txt':
                        await self._parse_requirements_txt(content, analysis)
                    break
            except Exception as e:
                logger.debug(f"Failed to fetch {config_file}: {e}")
                continue
    
    async def _get_file_content_raw_github(self, owner: str, repo_name: str, file_path: str) -> Optional[str]:
        """Get file content using raw GitHub URLs"""
        try:
            session = await self._get_session()
            branches = ['main', 'master', 'develop']
            
            for branch in branches:
                url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{branch}/{file_path}"
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            return content
                except Exception as e:
                    logger.debug(f"Failed to fetch {url}: {e}")
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Error getting file content via raw GitHub: {e}")
            return None
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
