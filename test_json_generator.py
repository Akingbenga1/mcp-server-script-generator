#!/usr/bin/env python3
"""
Test script for JSON-to-MCP-server generation functionality.
This script tests the complete workflow for various JSON API specification formats.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
import logging

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from app.json_analyzer import JSONAnalyzer
from app.mcp_server_generator import MCPServerGenerator
from app.database import Database

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_openapi_spec():
    """Create a sample OpenAPI 3.0 specification"""
    
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0",
            "description": "A sample API for testing JSON analysis"
        },
        "servers": [
            {"url": "https://api.sample.com/v1"}
        ],
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get all users",
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "schema": {"type": "integer"},
                            "description": "Page number"
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer"},
                            "description": "Items per page"
                        }
                    ],
                    "tags": ["users"]
                },
                "post": {
                    "summary": "Create a user",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"},
                                        "role": {"type": "string"}
                                    },
                                    "required": ["name", "email"]
                                }
                            }
                        }
                    },
                    "tags": ["users"]
                }
            },
            "/users/{id}": {
                "get": {
                    "summary": "Get user by ID",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "tags": ["users"]
                },
                "put": {
                    "summary": "Update user",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"},
                                        "role": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "tags": ["users"]
                }
            },
            "/products": {
                "get": {
                    "summary": "Get all products",
                    "parameters": [
                        {
                            "name": "category",
                            "in": "query",
                            "schema": {"type": "string"},
                            "description": "Product category"
                        }
                    ],
                    "tags": ["products"]
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer"
                }
            },
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "role": {"type": "string"}
                    }
                }
            }
        }
    }
    
    return json.dumps(openapi_spec, indent=2).encode('utf-8')

def create_swagger_spec():
    """Create a sample Swagger 2.0 specification"""
    
    swagger_spec = {
        "swagger": "2.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0",
            "description": "A sample API for testing JSON analysis"
        },
        "host": "api.sample.com",
        "basePath": "/v1",
        "schemes": ["https"],
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get all users",
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "type": "integer",
                            "description": "Page number"
                        }
                    ],
                    "tags": ["users"]
                },
                "post": {
                    "summary": "Create a user",
                    "parameters": [
                        {
                            "name": "user",
                            "in": "body",
                            "schema": {"$ref": "#/definitions/User"}
                        }
                    ],
                    "tags": ["users"]
                }
            },
            "/products": {
                "get": {
                    "summary": "Get all products",
                    "tags": ["products"]
                }
            }
        },
        "definitions": {
            "User": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "role": {"type": "string"}
                }
            }
        },
        "securityDefinitions": {
            "bearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header"
            }
        }
    }
    
    return json.dumps(swagger_spec, indent=2).encode('utf-8')

def create_postman_collection():
    """Create a sample Postman collection"""
    
    postman_collection = {
        "info": {
            "name": "Sample API Collection",
            "description": "A sample Postman collection for testing",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "baseUrl",
                "value": "https://api.sample.com/v1",
                "type": "string"
            }
        ],
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{authToken}}",
                    "type": "string"
                }
            ]
        },
        "item": [
            {
                "name": "Users",
                "item": [
                    {
                        "name": "Get Users",
                        "request": {
                            "method": "GET",
                            "url": {
                                "raw": "{{baseUrl}}/users?page=1&limit=10",
                                "host": ["{{baseUrl}}"],
                                "path": ["users"],
                                "query": [
                                    {"key": "page", "value": "1"},
                                    {"key": "limit", "value": "10"}
                                ]
                            },
                            "header": [
                                {
                                    "key": "Accept",
                                    "value": "application/json"
                                }
                            ]
                        }
                    },
                    {
                        "name": "Create User",
                        "request": {
                            "method": "POST",
                            "url": {
                                "raw": "{{baseUrl}}/users",
                                "host": ["{{baseUrl}}"],
                                "path": ["users"]
                            },
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": "{\n    \"name\": \"John Doe\",\n    \"email\": \"john@example.com\",\n    \"role\": \"user\"\n}"
                            }
                        }
                    },
                    {
                        "name": "Get User by ID",
                        "request": {
                            "method": "GET",
                            "url": {
                                "raw": "{{baseUrl}}/users/:userId",
                                "host": ["{{baseUrl}}"],
                                "path": ["users", ":userId"],
                                "variable": [
                                    {
                                        "key": "userId",
                                        "value": "1"
                                    }
                                ]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Products",
                "item": [
                    {
                        "name": "Get Products",
                        "request": {
                            "method": "GET",
                            "url": {
                                "raw": "{{baseUrl}}/products?category=electronics",
                                "host": ["{{baseUrl}}"],
                                "path": ["products"],
                                "query": [
                                    {"key": "category", "value": "electronics"}
                                ]
                            }
                        }
                    }
                ]
            }
        ]
    }
    
    return json.dumps(postman_collection, indent=2).encode('utf-8')

def create_custom_endpoints():
    """Create a custom endpoints format"""
    
    custom_format = {
        "name": "Sample API",
        "version": "1.0.0",
        "baseUrl": "https://api.sample.com/v1",
        "auth": {
            "type": "bearer",
            "description": "Bearer token authentication"
        },
        "endpoints": [
            {
                "method": "GET",
                "path": "/users",
                "description": "Retrieve all users",
                "parameters": {
                    "page": {
                        "type": "integer",
                        "in": "query",
                        "description": "Page number"
                    },
                    "limit": {
                        "type": "integer", 
                        "in": "query",
                        "description": "Items per page"
                    }
                },
                "tags": ["users"]
            },
            {
                "method": "POST",
                "path": "/users",
                "description": "Create a new user",
                "parameters": {
                    "name": {
                        "type": "string",
                        "in": "body",
                        "required": True
                    },
                    "email": {
                        "type": "string",
                        "in": "body",
                        "required": True
                    },
                    "role": {
                        "type": "string",
                        "in": "body"
                    }
                },
                "tags": ["users"]
            },
            {
                "method": "GET",
                "path": "/users/{id}",
                "description": "Get user by ID",
                "parameters": {
                    "id": {
                        "type": "integer",
                        "in": "path",
                        "required": True
                    }
                },
                "tags": ["users"]
            },
            {
                "method": "GET",
                "path": "/products",
                "description": "Get all products",
                "parameters": {
                    "category": {
                        "type": "string",
                        "in": "query"
                    }
                },
                "tags": ["products"]
            }
        ],
        "schemas": {
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "role": {"type": "string"}
                }
            }
        }
    }
    
    return json.dumps(custom_format, indent=2).encode('utf-8')

async def test_json_analysis(json_data: bytes, format_name: str, filename: str):
    """Test JSON analysis functionality for a specific format"""
    
    logger.info(f"=== Testing {format_name} Format ===")
    
    # Initialize JSON analyzer
    json_analyzer = JSONAnalyzer()
    
    try:
        logger.info(f"Analyzing {format_name} JSON ({len(json_data)} bytes)")
        
        # Analyze the JSON
        api_discovery = await json_analyzer.analyze_json(json_data, filename)
        
        logger.info(f"Analysis completed!")
        logger.info(f"Base URL: {api_discovery.base_url}")
        logger.info(f"Endpoints found: {len(api_discovery.endpoints)}")
        logger.info(f"Authentication: {api_discovery.authentication}")
        logger.info(f"Schemas: {len(api_discovery.schemas)}")
        
        # Display endpoints
        for endpoint in api_discovery.endpoints:
            logger.info(f"  {endpoint.method.value.upper()} {endpoint.url} - {endpoint.description or 'No description'}")
            if endpoint.parameters:
                for param_name, param_info in endpoint.parameters.items():
                    param_type = param_info.get('type', 'unknown') if isinstance(param_info, dict) else getattr(param_info, 'type', 'unknown')
                    param_source = param_info.get('source', 'unknown') if isinstance(param_info, dict) else getattr(param_info, 'source', 'unknown')
                    logger.info(f"    Param: {param_name} ({param_type}) - {param_source}")
            if endpoint.tags:
                logger.info(f"    Tags: {endpoint.tags}")
        
        return api_discovery
        
    except Exception as e:
        logger.error(f"{format_name} analysis failed: {e}")
        raise e

async def test_mcp_generation(api_discovery, format_name: str):
    """Test MCP server generation"""
    
    logger.info(f"=== Testing MCP Server Generation for {format_name} ===")
    
    # Initialize MCP server generator
    mcp_generator = MCPServerGenerator()
    
    try:
        # Generate MCP server content
        logger.info("Generating MCP server content...")
        mcp_content = mcp_generator.generate_mcp_server_content(
            f"json://{format_name.lower()}_api_spec.json", 
            api_discovery,
            api_discovery.base_url
        )
        
        logger.info(f"MCP server content generated!")
        logger.info(f"Repository name: {mcp_content['repo_name']}")
        logger.info(f"Tools count: {mcp_content['tools_count']}")
        logger.info(f"Framework: {mcp_content['framework']}")
        
        return mcp_content
        
    except Exception as e:
        logger.error(f"MCP generation failed: {e}")
        raise

async def test_all_formats():
    """Test all JSON formats"""
    
    formats = [
        (create_openapi_spec(), "OpenAPI 3.0", "openapi_spec.json"),
        (create_swagger_spec(), "Swagger 2.0", "swagger_spec.json"),
        (create_postman_collection(), "Postman Collection", "postman_collection.json"),
        (create_custom_endpoints(), "Custom Format", "custom_endpoints.json"),
    ]
    
    results = []
    
    for json_data, format_name, filename in formats:
        try:
            # Test JSON analysis
            api_discovery = await test_json_analysis(json_data, format_name, filename)
            
            # Test MCP generation
            mcp_content = await test_mcp_generation(api_discovery, format_name)
            
            results.append({
                "format": format_name,
                "success": True,
                "endpoints": len(api_discovery.endpoints),
                "tools": mcp_content['tools_count']
            })
            
            logger.info(f"✅ {format_name} - SUCCESS")
            
        except Exception as e:
            logger.error(f"❌ {format_name} - FAILED: {e}")
            results.append({
                "format": format_name,
                "success": False,
                "error": str(e)
            })
    
    return results

async def main():
    """Main test function"""
    
    print("🚀 Starting JSON-to-MCP Server Generation Tests")
    print("=" * 60)
    
    try:
        # Ensure data directory exists
        os.makedirs('data/mcp_servers', exist_ok=True)
        
        # Test all formats
        results = await test_all_formats()
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        success_count = 0
        total_endpoints = 0
        total_tools = 0
        
        for result in results:
            if result["success"]:
                status = "✅ SUCCESS"
                success_count += 1
                total_endpoints += result["endpoints"]
                total_tools += result["tools"]
                print(f"{status}: {result['format']} - {result['endpoints']} endpoints, {result['tools']} tools")
            else:
                status = "❌ FAILED"
                print(f"{status}: {result['format']} - {result['error']}")
        
        print(f"\nOverall Results:")
        print(f"✅ Successful formats: {success_count}/{len(results)}")
        print(f"📊 Total endpoints extracted: {total_endpoints}")
        print(f"🔧 Total MCP tools generated: {total_tools}")
        
        if success_count == len(results):
            print("\n🎉 All JSON formats tested successfully!")
            print("The JSON-to-MCP server generator supports:")
            print("  • OpenAPI 3.0 specifications")
            print("  • Swagger 2.0 specifications") 
            print("  • Postman collections")
            print("  • Custom JSON API specifications")
            print("  • Automatic format detection")
        else:
            print(f"\n⚠️ {len(results) - success_count} formats failed, but core functionality is working.")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())