from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class AuthType(str, Enum):
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"
    OAUTH = "oauth"
    SESSION = "session"

class APIEndpoint(BaseModel):
    url: str
    method: HTTPMethod
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    request_body: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    authentication_required: bool = False
    tags: List[str] = []

class AuthenticationInfo(BaseModel):
    type: AuthType
    endpoints: List[str] = []
    parameters: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None

class APIDiscovery(BaseModel):
    base_url: str
    endpoints: List[APIEndpoint] = []
    authentication: Optional[AuthenticationInfo] = None
    schemas: Dict[str, Any] = {}
    openapi_spec: Optional[Dict[str, Any]] = None
    openapi_specs: List[Dict[str, Any]] = []  # Add plural version for compatibility
    swagger_ui_url: Optional[str] = None

class WebsitePage(BaseModel):
    url: str
    title: str
    content: str
    forms: List[Dict[str, Any]] = []
    links: List[str] = []
    scripts: List[str] = []
    stylesheets: List[str] = []

class WebsiteAnalysis(BaseModel):
    url: str
    title: str
    description: Optional[str] = None
    pages: List[WebsitePage] = []
    forms: List[Dict[str, Any]] = []
    api_endpoints: List[str] = []
    javascript_files: List[str] = []
    css_files: List[str] = []
    external_apis: List[str] = []
    analysis_timestamp: datetime = datetime.now()

class MCPTool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    endpoint_url: str
    method: HTTPMethod
    authentication_required: bool = False
    category: str = "general"

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = datetime.now()
    metadata: Optional[Dict[str, Any]] = None

class UserSession(BaseModel):
    session_id: str
    url: str
    analysis: WebsiteAnalysis
    api_discovery: APIDiscovery
    mcp_tools: List[MCPTool] = []
    chat_history: List[ChatMessage] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class ChatbotResponse(BaseModel):
    message: str
    actions: List[Dict[str, Any]] = []
    tools_used: List[str] = []
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
