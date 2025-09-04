import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import APIDiscovery, MCPTool, ChatMessage, ChatbotResponse
from .ai_agent import AIAgent

logger = logging.getLogger(__name__)

class Chatbot:
    """AI-powered chatbot using Ollama with Mistral 7B and LangChain agents"""
    
    def __init__(self, ollama_base_url: str = None, model_name: str = None):
        self.api_discovery: Optional[APIDiscovery] = None
        self.mcp_tools: List[MCPTool] = []
        self.ai_agent: Optional[AIAgent] = None
        # Use environment variables if not provided
        self.ollama_base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL_NAME", "gemma3:1b")
        
    async def initialize(self, api_discovery: APIDiscovery, mcp_tools: List[MCPTool]):
        """Initialize chatbot with API discovery and MCP tools"""
        self.api_discovery = api_discovery
        self.mcp_tools = mcp_tools
        
        logger.info(f"=== CHATBOT INITIALIZATION ===")
        logger.info(f"API Discovery: {len(api_discovery.endpoints)} endpoints")
        logger.info(f"MCP Tools: {len(mcp_tools)} tools")
        logger.info(f"Ollama Base URL: {self.ollama_base_url}")
        logger.info(f"LLM Model: {self.model_name}")
        
        # Log MCP tools details
        for i, tool in enumerate(mcp_tools):
            logger.info(f"Tool {i+1}: {tool.name} - {tool.category} - {tool.method.value} {tool.endpoint_url}")
        
        # Initialize AI agent
        logger.info("Initializing AI Agent with Ollama...")
        self.ai_agent = AIAgent(ollama_base_url=self.ollama_base_url, model_name=self.model_name)
        await self.ai_agent.initialize(mcp_tools)
        
        logger.info(f"AI-powered chatbot initialized with {len(mcp_tools)} MCP tools")
        logger.info(f"=== CHATBOT LLM CONFIGURATION ===")
        logger.info(f"Ollama Base URL: {self.ollama_base_url}")
        logger.info(f"LLM Model: {self.ai_agent.llm.model}")
        logger.info(f"LLM Model Name: {self.ai_agent.model_name}")
        logger.info(f"LLM Temperature: {self.ai_agent.llm.temperature}")
    
    async def process_message(self, message: str, session_id: str, context: Dict[str, Any] = None) -> ChatbotResponse:
        """Process a user message using the AI agent"""
        try:
            logger.info(f"=== CHATBOT MESSAGE PROCESSING ===")
            logger.info(f"Session ID: {session_id}")
            logger.info(f"User Message: {message}")
            logger.info(f"Context: {context}")
            
            if not self.ai_agent:
                logger.warning("AI Agent not initialized - returning error response")
                return ChatbotResponse(
                    message="Chatbot not initialized. Please generate MCP tools first.",
                    confidence=0.0
                )
            
            # Process message through AI agent
            logger.info("Forwarding message to AI Agent...")
            response = await self.ai_agent.process_message(message, context)
            
            # Log the final response
            logger.info(f"=== CHATBOT RESPONSE ===")
            logger.info(f"Response Message: {response.message[:200]}...")  # First 200 chars
            logger.info(f"Confidence: {response.confidence}")
            logger.info(f"Tools Used: {response.tools_used}")
            logger.info(f"Actions: {len(response.actions)} actions")
            logger.info(f"Metadata Keys: {list(response.metadata.keys()) if response.metadata else 'None'}")
            logger.info(f"LLM Model Used: {response.metadata.get('model', 'Unknown') if response.metadata else 'Unknown'}")
            logger.info(f"Response Time: {response.metadata.get('response_time', 'Unknown') if response.metadata else 'Unknown'} seconds")
            
            return response
            
        except Exception as e:
            logger.error(f"=== CHATBOT ERROR ===")
            logger.error(f"Error processing message: {e}")
            logger.error(f"Session ID: {session_id}")
            logger.error(f"User Message: {message}")
            logger.error(f"Context: {context}")
            return ChatbotResponse(
                message=f"I encountered an error while processing your request: {str(e)}. Please try again or rephrase your request.",
                confidence=0.1
            )

    async def process_message_streaming(self, message: str, session_id: str, context: Dict[str, Any] = None):
        """Process a user message using the AI agent with streaming response"""
        try:
            logger.info(f"=== CHATBOT STREAMING MESSAGE PROCESSING ===")
            logger.info(f"Session ID: {session_id}")
            logger.info(f"User Message: {message}")
            logger.info(f"Context: {context}")
            
            if not self.ai_agent:
                logger.warning("AI Agent not initialized - returning error response")
                yield {
                    'type': 'error',
                    'content': "Chatbot not initialized. Please generate MCP tools first.",
                    'session_id': session_id
                }
                return
            
            # Process message through AI agent with streaming
            logger.info("Forwarding message to AI Agent for streaming...")
            async for chunk in self.ai_agent.process_message_streaming(message, context):
                # Add session_id to each chunk for tracking
                chunk['session_id'] = session_id
                yield chunk
            
        except Exception as e:
            logger.error(f"=== CHATBOT STREAMING ERROR ===")
            logger.error(f"Error processing streaming message: {e}")
            logger.error(f"Session ID: {session_id}")
            logger.error(f"User Message: {message}")
            logger.error(f"Context: {context}")
            yield {
                'type': 'error',
                'content': f"I encountered an error while processing your request: {str(e)}. Please try again or rephrase your request.",
                'session_id': session_id,
                'error': str(e)
            }
    
    async def close(self):
        """Close the chatbot session"""
        if self.ai_agent:
            await self.ai_agent.close()
