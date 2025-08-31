import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import os

from .models import UserSession, WebsiteAnalysis, APIDiscovery, MCPTool

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.sessions_file = os.path.join(data_dir, "sessions.json")
        self.sessions: Dict[str, UserSession] = {}
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing sessions
        self._load_sessions()
    
    def _load_sessions(self):
        """Load sessions from file"""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    data = json.load(f)
                    for session_id, session_data in data.items():
                        # Convert dict back to UserSession object
                        session = UserSession(**session_data)
                        self.sessions[session_id] = session
                logger.info(f"Loaded {len(self.sessions)} sessions from database")
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
    
    def _save_sessions(self):
        """Save sessions to file"""
        try:
            with open(self.sessions_file, 'w') as f:
                # Convert UserSession objects to dicts
                data = {}
                for session_id, session in self.sessions.items():
                    data[session_id] = session.model_dump() if hasattr(session, 'model_dump') else session.dict()
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def create_session(self, url: str, analysis: WebsiteAnalysis, api_discovery: APIDiscovery) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        
        session = UserSession(
            session_id=session_id,
            url=url,
            analysis=analysis,
            api_discovery=api_discovery
        )
        
        self.sessions[session_id] = session
        self._save_sessions()
        
        logger.info(f"Created session {session_id} for {url}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get a session by ID"""
        return self.sessions.get(session_id)
    
    def update_session_mcp_tools(self, session_id: str, mcp_tools: List[MCPTool]):
        """Update session with MCP tools"""
        if session_id in self.sessions:
            self.sessions[session_id].mcp_tools = mcp_tools
            self.sessions[session_id].updated_at = datetime.now()
            self._save_sessions()
            logger.info(f"Updated session {session_id} with {len(mcp_tools)} MCP tools")
    
    def add_chat_message(self, session_id: str, message: str, role: str = "user"):
        """Add a chat message to a session"""
        if session_id in self.sessions:
            from .models import ChatMessage
            chat_message = ChatMessage(
                role=role,
                content=message
            )
            self.sessions[session_id].chat_history.append(chat_message)
            self.sessions[session_id].updated_at = datetime.now()
            self._save_sessions()
    
    def get_all_sessions(self) -> List[UserSession]:
        """Get all sessions"""
        return list(self.sessions.values())
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
            logger.info(f"Deleted session {session_id}")
            return True
        return False
    
    def cleanup_old_sessions(self, days: int = 7):
        """Clean up sessions older than specified days"""
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
        
        sessions_to_delete = []
        for session_id, session in self.sessions.items():
            if session.created_at < cutoff_date:
                sessions_to_delete.append(session_id)
        
        for session_id in sessions_to_delete:
            self.delete_session(session_id)
        
        logger.info(f"Cleaned up {len(sessions_to_delete)} old sessions")
