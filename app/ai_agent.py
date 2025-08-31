import json
import logging
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from langchain_ollama import OllamaLLM
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from .models import MCPTool, ChatbotResponse

logger = logging.getLogger(__name__)

class MCPToolWrapper(BaseTool):
    """Wrapper for MCP tools to be used with LangChain agents"""
    name: str
    description: str
    mcp_tool: MCPTool
    
    def __init__(self, mcp_tool: MCPTool):
        super().__init__(
            name=mcp_tool.name,
            description=mcp_tool.description,
            mcp_tool=mcp_tool
        )
    
    def _run(self, **kwargs) -> str:
        """Synchronous execution of MCP tool"""
        # This will be handled by the async version
        return "Tool executed successfully"
    
    async def _arun(self, **kwargs) -> str:
        """Asynchronous execution of MCP tool"""
        try:
            # Execute the MCP tool
            result = await self._execute_mcp_tool(kwargs)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error executing MCP tool {self.name}: {e}")
            return f"Error executing tool: {str(e)}"
    
    async def _execute_mcp_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual MCP tool with HTTP request"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'AI-Agent-MCP/1.0'
            }
            
            # Prepare request based on HTTP method
            method = self.mcp_tool.method.value if hasattr(self.mcp_tool.method, 'value') else str(self.mcp_tool.method)
            
            async with aiohttp.ClientSession() as session:
                if method in ['POST', 'PUT', 'PATCH']:
                    async with session.request(
                        method=method,
                        url=self.mcp_tool.endpoint_url,
                        headers=headers,
                        json=parameters,
                        timeout=30
                    ) as response:
                        return await self._process_response(response)
                else:
                    async with session.request(
                        method=method,
                        url=self.mcp_tool.endpoint_url,
                        headers=headers,
                        params=parameters,
                        timeout=30
                    ) as response:
                        return await self._process_response(response)
                        
        except Exception as e:
            logger.error(f"Error executing MCP tool {self.name}: {e}")
            return {"error": str(e), "success": False}
    
    async def _process_response(self, response) -> Dict[str, Any]:
        """Process the HTTP response"""
        result = {
            'status_code': response.status,
            'success': 200 <= response.status < 300,
            'url': str(response.url)
        }
        
        try:
            result['data'] = await response.json()
        except:
            result['data'] = await response.text()
        
        return result

class AIAgent:
    """AI Agent powered by Ollama with conversational MCP tool execution"""
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434", model_name: str = "llama3.1:latest"):
        self.ollama_base_url = ollama_base_url
        self.model_name = model_name
        self.llm = None
        self.agent_executor = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.mcp_tools: List[MCPTool] = []
        self.user_context: Dict[str, Any] = {}
        
    async def initialize(self, mcp_tools: List[MCPTool]):
        """Initialize the AI agent with MCP tools"""
        self.mcp_tools = mcp_tools
        
        # Initialize Ollama LLM
        try:
            self.llm = OllamaLLM(
                model=self.model_name,
                base_url=self.ollama_base_url,
                temperature=0.1
            )
            logger.info(f"Ollama LLM initialized successfully with model: {self.llm.model}")
            logger.info(f"Ollama Base URL: {self.ollama_base_url}")
            logger.info(f"Model Temperature: {self.llm.temperature}")
            logger.info(f"Model Name: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM: {e}")
            raise
        
        # Create LangChain tools from MCP tools
        langchain_tools = [MCPToolWrapper(tool) for tool in mcp_tools]
        
        # Create system prompt with MCP tool information
        system_prompt = self._create_system_prompt()
        
        # Create a simpler approach without function calling
        self.llm = self.llm
        self.tools = langchain_tools
        self.system_prompt = system_prompt
        
        logger.info(f"AI Agent initialized with {len(mcp_tools)} MCP tools")
        logger.info(f"=== AI AGENT CONFIGURATION ===")
        logger.info(f"LLM Model: {self.llm.model}")
        logger.info(f"LLM Model Name: {self.model_name}")
        logger.info(f"LLM Base URL: {self.ollama_base_url}")
        logger.info(f"LLM Temperature: {self.llm.temperature}")
        logger.info(f"Available Tools: {len(self.tools)}")
        logger.info(f"System Prompt Length: {len(self.system_prompt)} characters")
    
    def _create_system_prompt(self) -> str:
        """Create a comprehensive system prompt with MCP tool information"""
        tools_info = []
        
        for tool in self.mcp_tools:
            # Escape JSON content to avoid template variable conflicts
            params_json = json.dumps(tool.parameters, indent=2).replace('{', '{{').replace('}', '}}')
            tool_info = f"""
Tool: {tool.name}
Description: {tool.description}
Category: {tool.category}
Endpoint: {tool.method.value} {tool.endpoint_url}
Authentication Required: {tool.authentication_required}
Parameters: {params_json}
"""
            tools_info.append(tool_info)
        
        tools_str = "\n".join(tools_info)
        
        # Escape JSON content in user context
        context_json = json.dumps(self.user_context, indent=2).replace('{', '{{').replace('}', '}}')
        
        return f"""You are a helpful AI assistant that can interact with websites through MCP tools. Your job is to understand user requests and select the most appropriate tool to help them.

EXECUTION RULES:
1. Analyze the user's request to understand their intent
2. Select the most relevant MCP tool from the available options
3. Extract required parameters from user input
4. Execute the tool and provide a conversational response

Available MCP Tools:
{tools_str}

RESPONSE FORMAT:
When a tool is needed:
"I'll help you with that! Based on your request, I'm using the [tool_name] tool. This tool [brief explanation of what it does]. Let me execute it with the parameters: [params]. 

Result: [result]"

When no tool matches:
"I understand you're asking about [summarize request], but I don't have a suitable tool available to help with that specific request. Could you try rephrasing or let me know if there's something else I can help you with?"

Current user context: {context_json}

Be conversational, helpful, and explain your reasoning for tool selection."""
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> ChatbotResponse:
        """Process a user message using the AI agent"""
        try:
            # Update context
            if context:
                self.user_context.update(context)
                logger.info(f"Updated user context: {self.user_context}")
            
            # Create a simple prompt with the message and available tools
            tools_description = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
            
            prompt = f"""{self.system_prompt}

USER REQUEST: {message}

Please analyze this request and provide a conversational response. If you need to use a tool, explain why you chose it and what it does. If no tool is suitable, explain why and suggest alternatives."""
            
            # Log the prompt being sent to LLM
            logger.info(f"=== LLM REQUEST ===")
            logger.info(f"User Message: {message}")
            logger.info(f"Available Tools: {len(self.tools)} tools")
            logger.info(f"User Context: {self.user_context}")
            logger.info(f"Prompt Length: {len(prompt)} characters")
            logger.debug(f"Full Prompt:\n{prompt}")
            
            # Get response from LLM
            logger.info("Sending request to Ollama LLM...")
            start_time = asyncio.get_event_loop().time()
            
            response = await self.llm.ainvoke(prompt)
            
            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            
            # Log the LLM response
            logger.info(f"=== LLM RESPONSE ===")
            logger.info(f"Response Time: {response_time:.2f} seconds")
            logger.info(f"Response Length: {len(response)} characters")
            logger.info(f"Model Used: {self.llm.model}")
            logger.info(f"Temperature: {self.llm.temperature}")
            logger.info(f"Full Response:\n{response}")
            
            # Log any tool usage detected in response
            tools_mentioned = []
            for tool in self.tools:
                if tool.name.lower() in response.lower():
                    tools_mentioned.append(tool.name)
            
            if tools_mentioned:
                logger.info(f"Tools mentioned in response: {tools_mentioned}")
            else:
                logger.info("No specific tools mentioned in response")
            
            # For now, return a simple response
            # In a full implementation, you would parse the response and execute tools
            return ChatbotResponse(
                message=response,
                actions=[],
                tools_used=tools_mentioned,
                confidence=0.8,
                metadata={
                    'llm_response': response,
                    'response_time': response_time,
                    'model': self.llm.model,
                    'temperature': self.llm.temperature,
                    'prompt_length': len(prompt),
                    'response_length': len(response),
                    'tools_available': len(self.tools),
                    'tools_mentioned': tools_mentioned
                }
            )
            
        except Exception as e:
            logger.error(f"=== LLM ERROR ===")
            logger.error(f"Error in AI agent processing: {e}")
            logger.error(f"User message that caused error: {message}")
            logger.error(f"Current context: {self.user_context}")
            logger.error(f"Available tools: {len(self.tools)}")
            return ChatbotResponse(
                message=f"I encountered an error while processing your request: {str(e)}. Please try again.",
                confidence=0.1
            )
    
    async def _handle_authentication(self, response_text: str):
        """Handle authentication tokens from responses"""
        try:
            # Look for authentication tokens in the response
            if 'token' in response_text.lower() or 'auth' in response_text.lower():
                # Extract token using regex or JSON parsing
                import re
                token_match = re.search(r'token["\']?\s*:\s*["\']([^"\']+)["\']', response_text)
                if token_match:
                    self.user_context['auth_token'] = token_match.group(1)
                    logger.info("Authentication token extracted and stored")
        except Exception as e:
            logger.debug(f"Error handling authentication: {e}")
    
    async def close(self):
        """Clean up resources"""
        if self.agent_executor:
            # Clean up any resources
            pass
