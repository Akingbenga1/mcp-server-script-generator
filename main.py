from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.requests import Request
import uvicorn
import asyncio
import json
import os
import zipfile
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from app.website_analyzer import WebsiteAnalyzer
from app.api_discoverer import APIDiscoverer
from app.github_analyzer import GitHubAnalyzer
from app.mcp_server import MCPServer
from app.mcp_server_generator import MCPServerGenerator
from app.chatbot import Chatbot
from app.models import WebsiteAnalysis, APIDiscovery, ChatMessage, UserSession
from app.database import Database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
import logging.config
import os

# Create required directories if they don't exist
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('data/mcp_servers', exist_ok=True)
os.makedirs('static', exist_ok=True)

# Configure logging
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'logs/app.log',
            'mode': 'a',
            'encoding': 'utf-8'
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': 'logs/error.log',
            'mode': 'a',
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'app': {  # App-specific logger
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'uvicorn': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'fastapi': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Website MCP Chatbot Prototype",
    description="A FastAPI application that analyzes websites, discovers APIs, and creates MCP-powered chatbots",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize components
website_analyzer = WebsiteAnalyzer()
api_discoverer = APIDiscoverer()
github_analyzer = GitHubAnalyzer()
mcp_server = MCPServer()
mcp_server_generator = MCPServerGenerator()

# Initialize chatbot with Ollama configuration
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
model_name = os.getenv("OLLAMA_MODEL_NAME", "llama3.1:latest")
chatbot = Chatbot(ollama_base_url=ollama_base_url, model_name=model_name)
database = Database()

# Store active sessions
active_sessions: Dict[str, UserSession] = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with website analysis form"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze-website")
async def analyze_website(url: str = Form(...)):
    """Analyze a website and discover its structure"""
    try:
        logger.info(f"Analyzing website: {url}")
        
        # Check if it's a GitHub repository URL
        if 'github.com' in url:
            logger.info("Detected GitHub repository URL, using GitHub analyzer")
            return await analyze_github_repository(url)
        
        # Analyze website structure
        analysis = await website_analyzer.analyze(url)
        
        # Discover API endpoints
        api_discovery = await api_discoverer.discover_apis(url, analysis)
        
        # Store analysis results
        session_id = database.create_session(url, analysis, api_discovery)
        
        return {
            "success": True,
            "session_id": session_id,
            "analysis": analysis.model_dump() if hasattr(analysis, 'model_dump') else analysis.dict(),
            "api_discovery": api_discovery.model_dump() if hasattr(api_discovery, 'model_dump') else api_discovery.dict()
        }
    except Exception as e:
        logger.error(f"Error analyzing website: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_github_repository(repo_url: str):
    """Analyze a GitHub repository for API endpoints"""
    try:
        logger.info(f"Analyzing GitHub repository: {repo_url}")
        
        # Analyze GitHub repository
        github_analysis = await github_analyzer.analyze_repository(repo_url)
        
        if not github_analysis:
            logger.warning("GitHub analysis returned empty result, creating basic analysis")
            github_analysis = {
                'repository': {
                    'name': repo_url.split('/')[-1],
                    'description': f'Repository {repo_url}',
                    'topics': []
                },
                'api_endpoints': [],
                'documentation_files': [],
                'code_files': [],
                'openapi_specs': [],
                'readme_content': '',
                'languages': [],
                'topics': []
            }
        
        # Convert GitHub analysis to our standard format
        analysis = WebsiteAnalysis(
            url=repo_url,
            title=github_analysis.get('repository', {}).get('name', 'GitHub Repository'),
            description=github_analysis.get('repository', {}).get('description', ''),
            pages=[],  # GitHub doesn't have traditional pages
            forms=[],  # GitHub doesn't have forms
            api_endpoints=[],  # Will be populated from GitHub analysis
            javascript_files=[],
            css_files=[],
            external_apis=[]
        )
        
        # Create API discovery from GitHub analysis
        api_discovery = APIDiscovery(
            base_url=repo_url,
            endpoints=github_analysis.get('api_endpoints', []),
            authentication=None,  # GitHub repos don't have auth info
            schemas={},
            openapi_specs=github_analysis.get('openapi_specs', [])
        )
        
        # Store analysis results
        session_id = database.create_session(repo_url, analysis, api_discovery)
        
        # Generate MCP server content for GitHub repositories
        if 'github.com' in repo_url and api_discovery.endpoints:
            try:
                logger.info(f"Generating MCP server content for {repo_url}")
                mcp_content = mcp_server_generator.generate_mcp_server_content(repo_url, api_discovery)
                logger.info(f"MCP server content generated successfully for {repo_url}")
            except Exception as e:
                logger.error(f"Error generating MCP server content: {e}")
                mcp_content = {}
        else:
            mcp_content = {}
        
        return {
            "success": True,
            "session_id": session_id,
            "analysis": analysis.dict(),
            "api_discovery": api_discovery.dict(),
            "github_analysis": github_analysis,
            "mcp_server_generated": bool(mcp_content)
        }
    except Exception as e:
        logger.error(f"Error analyzing GitHub repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get analysis results for a session"""
    session = database.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "url": session.url,
        "analysis": session.analysis.model_dump() if hasattr(session.analysis, 'model_dump') else session.analysis.dict(),
        "api_discovery": session.api_discovery.model_dump() if hasattr(session.api_discovery, 'model_dump') else session.api_discovery.dict()
    }

@app.post("/generate-mcp-tools")
async def generate_mcp_tools(request: Request):
    """Generate MCP tools from discovered APIs"""
    try:
        # Get session_id and production_base_url from request body
        body = await request.json()
        session_id = body.get('session_id')
        production_base_url = body.get('production_base_url')
        
        logger.info(f"Generating MCP tools for session: {session_id}")
        if production_base_url:
            logger.info(f"Using production base URL: {production_base_url}")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        session = database.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"Found session for URL: {session.url}")
        logger.info(f"API discovery has {len(session.api_discovery.endpoints)} endpoints")
        
        # Generate MCP tools from API discovery
        mcp_tools = await mcp_server.generate_tools(session.api_discovery, production_base_url)
        
        logger.info(f"Generated {len(mcp_tools)} MCP tools")
        
        # Update session with MCP tools
        database.update_session_mcp_tools(session_id, mcp_tools)
        
        return {
            "success": True,
            "mcp_tools": [tool.model_dump() if hasattr(tool, 'model_dump') else tool.dict() for tool in mcp_tools]
        }
    except Exception as e:
        logger.error(f"Error generating MCP tools: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for chatbot interaction with streaming support"""
    await websocket.accept()
    
    try:
        session = database.get_session(session_id)
        if not session:
            await websocket.send_text(json.dumps({"error": "Session not found"}))
            return
        
        # Initialize chatbot with MCP tools
        await chatbot.initialize(session.api_discovery, session.mcp_tools)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Check if streaming is requested
            use_streaming = message_data.get("streaming", True)  # Default to streaming
            
            if use_streaming:
                # Process message through chatbot with streaming
                async for chunk in chatbot.process_message_streaming(
                    message_data["message"],
                    session_id,
                    message_data.get("context", {})
                ):
                    # Send each chunk to the client
                    await websocket.send_text(json.dumps(chunk))
            else:
                # Process message through chatbot without streaming (legacy mode)
                response = await chatbot.process_message(
                    message_data["message"],
                    session_id,
                    message_data.get("context", {})
                )
                
                # Send response back to client - serialize ChatbotResponse object
                if hasattr(response, 'model_dump'):
                    # If it's a Pydantic model, convert to dict (Pydantic v2)
                    response_data = response.model_dump()
                elif hasattr(response, 'dict'):
                    # If it's a Pydantic model, convert to dict (Pydantic v1)
                    response_data = response.dict()
                else:
                    # If it's already a dict or other serializable type
                    response_data = response
                
                # Custom JSON encoder to handle datetime and other non-serializable types
                class CustomJSONEncoder(json.JSONEncoder):
                    def default(self, obj):
                        if hasattr(obj, 'isoformat'):  # datetime objects
                            return obj.isoformat()
                        elif hasattr(obj, 'value'):  # enum values
                            return obj.value
                        elif hasattr(obj, '__dict__'):  # other objects
                            return obj.__dict__
                        return super().default(obj)
                    
                await websocket.send_text(json.dumps(response_data, cls=CustomJSONEncoder))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"Error in chat websocket: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except Exception as send_error:
            logger.error(f"Error sending error message: {send_error}")

@app.get("/api-endpoints/{session_id}")
async def get_api_endpoints(session_id: str):
    """Get discovered API endpoints for a session"""
    session = database.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "endpoints": session.api_discovery.endpoints,
        "authentication": session.api_discovery.authentication,
        "schemas": session.api_discovery.schemas
    }

@app.post("/test-endpoint")
async def test_endpoint(
    session_id: str = Form(...),
    endpoint_url: str = Form(...),
    method: str = Form(...),
    headers: str = Form("{}"),
    body: str = Form("{}")
):
    """Test a discovered API endpoint"""
    try:
        session = database.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Test the endpoint
        result = await api_discoverer.test_endpoint(
            endpoint_url, 
            method, 
            json.loads(headers), 
            json.loads(body)
        )
        
        return result
    except Exception as e:
        logger.error(f"Error testing endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/analyze-github")
async def analyze_github_repository_endpoint(repo_url: str = Form(...)):
    """Analyze a GitHub repository for API endpoints and documentation"""
    try:
        logger.info(f"Analyzing GitHub repository: {repo_url}")
        
        # Analyze GitHub repository
        github_analysis = await github_analyzer.analyze_repository(repo_url)
        
        if not github_analysis:
            logger.warning("GitHub analysis returned empty result, creating basic analysis")
            github_analysis = {
                'repository': {
                    'name': repo_url.split('/')[-1],
                    'description': f'Repository {repo_url}',
                    'topics': []
                },
                'api_endpoints': [],
                'documentation_files': [],
                'code_files': [],
                'openapi_specs': [],
                'readme_content': '',
                'languages': [],
                'topics': []
            }
        
        # Convert GitHub analysis to our standard format
        analysis = WebsiteAnalysis(
            url=repo_url,
            title=github_analysis.get('repository', {}).get('name', 'GitHub Repository'),
            description=github_analysis.get('repository', {}).get('description', ''),
            pages=[],  # GitHub doesn't have traditional pages
            forms=[],  # GitHub doesn't have forms
            api_endpoints=[],  # Will be populated from GitHub analysis
            javascript_files=[],
            css_files=[],
            external_apis=[]
        )
        
        # Create API discovery from GitHub analysis
        api_discovery = APIDiscovery(
            base_url=repo_url,
            endpoints=github_analysis.get('api_endpoints', []),
            authentication=None,  # GitHub repos don't have auth info
            schemas={},
            openapi_specs=github_analysis.get('openapi_specs', [])
        )
        
        # Store analysis results
        session_id = database.create_session(repo_url, analysis, api_discovery)
        
        return {
            "success": True,
            "session_id": session_id,
            "analysis": analysis.model_dump() if hasattr(analysis, 'model_dump') else analysis.dict(),
            "api_discovery": api_discovery.model_dump() if hasattr(api_discovery, 'model_dump') else api_discovery.dict(),
            "github_analysis": github_analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing GitHub repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp-servers")
async def list_mcp_servers():
    """List all available MCP servers"""
    try:
        servers = mcp_server_generator.list_mcp_servers()
        return {
            "success": True,
            "servers": servers,
            "count": len(servers)
        }
    except Exception as e:
        logger.error(f"Error listing MCP servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp-server/{repo_name}")
async def get_mcp_server_content(repo_name: str):
    """Get MCP server content for a specific repository"""
    try:
        logger.info(f"Requesting MCP server content for repo: {repo_name}")
        
        mcp_content = mcp_server_generator.get_mcp_content(repo_name)
        logger.info(f"Retrieved MCP content: {bool(mcp_content)}")
        
        if not mcp_content:
            logger.warning(f"MCP server content not found for {repo_name}")
            raise HTTPException(status_code=404, detail=f"MCP server content not found for {repo_name}")
        
        # Check if content needs regeneration (FastMCP case)
        if mcp_content.get('needs_regeneration') or not mcp_content.get('python_code'):
            logger.info(f"MCP content needs regeneration for {repo_name}")
            
            # Find the session for this repository to regenerate content
            github_url = mcp_content.get('github_url', '')
            if not github_url:
                # Try to construct URL from repo name
                parts = repo_name.split('_')
                if len(parts) >= 2:
                    github_url = f"https://github.com/{parts[0]}/{parts[1]}"
            
            # Find session by URL
            session = None
            for s in database.sessions.values():
                if s.url == github_url or github_url in s.url:
                    session = s
                    break
            
            if not session:
                logger.error(f"No session found for regenerating {repo_name}")
                raise HTTPException(status_code=500, detail=f"Cannot regenerate MCP server content - session not found")
            
            # Regenerate the full content
            production_base_url = mcp_content.get('production_base_url')
            mcp_content = mcp_server_generator.generate_mcp_server_content(
                github_url, session.api_discovery, production_base_url
            )
            
            if not mcp_content:
                logger.error(f"Failed to regenerate MCP content for {repo_name}")
                raise HTTPException(status_code=500, detail=f"Failed to regenerate MCP server content")
        
        # Final check for python_code
        if not mcp_content.get('python_code'):
            logger.error(f"MCP content exists but python_code is empty for {repo_name}")
            raise HTTPException(status_code=500, detail=f"MCP server content is empty for {repo_name}")
        
        logger.info(f"Successfully retrieved MCP content for {repo_name}")
        return {
            "success": True,
            "repo_name": repo_name,
            "mcp_content": mcp_content
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving MCP server content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-mcp-server")
async def generate_mcp_server_for_session(request: Request):
    """Generate MCP server content for an existing session"""
    try:
        body = await request.json()
        session_id = body.get('session_id')
        production_base_url = body.get('production_base_url')
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        session = database.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Only generate for GitHub repositories
        if 'github.com' not in session.url:
            raise HTTPException(status_code=400, detail="MCP server generation only available for GitHub repositories")
        
        if not session.api_discovery.endpoints:
            raise HTTPException(status_code=400, detail="No API endpoints found in session")
        
        # Generate MCP server content
        mcp_content = mcp_server_generator.generate_mcp_server_content(session.url, session.api_discovery, production_base_url)
        
        return {
            "success": True,
            "session_id": session_id,
            "repo_name": mcp_content.get("repo_name", "unknown"),
            "mcp_content": mcp_content
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating MCP server for session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/download-mcp-files")
async def download_mcp_files(request: Request):
    """Download MCP server files as a zip archive"""
    try:
        body = await request.json()
        session_id = body.get('session_id')
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        session = database.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Only download for GitHub repositories
        if 'github.com' not in session.url:
            raise HTTPException(status_code=400, detail="MCP server download only available for GitHub repositories")
        
        # Get MCP content
        repo_name = session.url.split('/')[-2] + '_' + session.url.split('/')[-1]
        mcp_content = mcp_server_generator.get_mcp_content(repo_name)
        
        # Check if content needs regeneration or doesn't exist
        if not mcp_content or mcp_content.get('needs_regeneration') or not mcp_content.get('python_code'):
            logger.info(f"Generating MCP content for download: {repo_name}")
            # Get production base URL from request if provided
            production_base_url = body.get('production_base_url')
            mcp_content = mcp_server_generator.generate_mcp_server_content(session.url, session.api_discovery, production_base_url)
        
        if not mcp_content or not mcp_content.get('python_code'):
            raise HTTPException(status_code=500, detail="Failed to generate MCP server content")
        
        # Create temporary directory for files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create mcp_server.py
            mcp_server_file = temp_path / "mcp_server.py"
            with open(mcp_server_file, 'w', encoding='utf-8') as f:
                f.write(mcp_content['python_code'])
            
            # Create requirements.txt
            requirements_file = temp_path / "requirements.txt"
            with open(requirements_file, 'w', encoding='utf-8') as f:
                f.write(mcp_content['requirements_txt_content'])
            
            # Create Dockerfile
            dockerfile = temp_path / "Dockerfile"
            with open(dockerfile, 'w', encoding='utf-8') as f:
                f.write(mcp_content['dockerfile_content'])
            
            # Create zip file in memory
            zip_filename = f"{mcp_content['repo_name']}_mcp_server.zip"
            
            # Create zip file in memory
            import io
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(mcp_server_file, "mcp_server.py")
                zipf.write(requirements_file, "requirements.txt")
                zipf.write(dockerfile, "Dockerfile")
            
            # Get the zip content
            zip_content = zip_buffer.getvalue()
            zip_buffer.close()
            
            # Return the zip file as a response
            return Response(
                content=zip_content,
                media_type='application/zip',
                headers={
                    'Content-Disposition': f'attachment; filename="{zip_filename}"'
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading MCP files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
async def test_endpoint():
    """Test endpoint for demonstration"""
    return {
        "message": "Website MCP Chatbot is running!",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze-website",
            "analyze_github": "/analyze-github",
            "generate_tools": "/generate-mcp-tools",
            "mcp_servers": "/mcp-servers",
            "mcp_server": "/mcp-server/{repo_name}",
            "generate_mcp_server": "/generate-mcp-server",
            "download_mcp_files": "/download-mcp-files",
            "chat": "/chat/{session_id}",
            "docs": "/docs"
        },
        "example_usage": {
            "analyze_website": "POST /analyze-website with form data: url=https://example.com",
            "analyze_github": "POST /analyze-github with form data: repo_url=https://github.com/owner/repo",
            "generate_tools": "POST /generate-mcp-tools with JSON: {\"session_id\": \"your-session-id\"}",
            "download_mcp_files": "POST /download-mcp-files with JSON: {\"session_id\": \"your-session-id\"}",
            "chat": "WebSocket connection to /chat/{session_id}"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
