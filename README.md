# 🌐 Website MCP Chatbot Prototype

A powerful FastAPI application that analyzes websites, discovers their APIs, and creates intelligent chatbots with Model Context Protocol (MCP) tools. This prototype demonstrates how to automatically convert website functionality into conversational AI capabilities.

## 🚀 Features

- **🔍 Website Analysis**: Automatically crawl and analyze website structure
- **🔗 API Discovery**: Find and document API endpoints from websites
- **🔗 GitHub Repository Analysis**: Analyze public GitHub repositories for API endpoints and documentation
- **🛠️ MCP Tool Generation**: Convert discovered APIs into MCP tools
- **🤖 AI-Powered Chatbot**: Advanced chatbot powered by Ollama with Mistral 7B model
- **🧠 LangChain Agent Framework**: Intelligent tool selection and parameter extraction
- **💬 Natural Language Processing**: Understand complex user requests
- **🔐 Authentication Support**: Handle login, registration, and session management
- **📅 Appointment Booking**: Support for booking and managing appointments
- **👤 Profile Management**: User profile operations
- **🔍 Content Search**: Search functionality across website content
- **📚 Multi-Language Support**: Extract API endpoints from Python, JavaScript, Java, Go, and more

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Modern web browser
- Internet connection for website analysis

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd website-mcp-prototype
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- Ollama (for AI-powered chatbot)

### 1. Setup Ollama (Required for AI Chatbot)
```bash
# Run the Ollama setup script
python setup_ollama.py
```

This script will:
- Install Ollama if not already installed
- Download the Mistral 7B model
- Test the connection
- Create configuration files

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the server
```bash
python run.py
```

### 4. Open your browser and navigate to:
```
http://localhost:8001
```

### 5. Test the application
```bash
python test_app.py
```

## 📖 Usage Guide

### Web Interface

1. **Analyze a Website or GitHub Repository**:
   - Enter a website URL or GitHub repository URL in the input field
   - Click "Analyze Website" for regular websites
   - Click "Analyze GitHub Repo" for GitHub repositories
   - Wait for the analysis to complete

2. **Generate MCP Tools**:
   - After analysis, click "Generate MCP Tools"
   - View the discovered API endpoints and generated tools

3. **Chat with the Website/Repository**:
   - Use the AI-powered chat interface to interact with the website or repository
   - The chatbot uses Ollama with Mistral 7B for intelligent understanding
   - Try natural language commands like:
     - "I want to login with my email john@example.com and password secret123"
     - "Can you book me an appointment for a consultation on January 15th at 2:30 PM?"
     - "Show me my profile information"
     - "Search for available services"
     - "What API endpoints are available?"
     - "Help me register a new account"

### 🤖 AI-Powered Chatbot Features

The chatbot now uses advanced AI capabilities:

- **🧠 Intelligent Understanding**: Uses Mistral 7B model to understand complex requests
- **🛠️ Smart Tool Selection**: Automatically selects the best MCP tool for each request
- **📝 Parameter Extraction**: Intelligently extracts parameters from natural language
- **💬 Conversational Memory**: Remembers context from previous messages
- **🔐 Authentication Awareness**: Automatically handles authentication tokens
- **🔄 Error Recovery**: Provides helpful suggestions when tools fail
- **📊 Response Formatting**: Formats API responses in a user-friendly way

### API Endpoints

#### Health Check
```bash
GET /health
```

#### Analyze Website
```bash
POST /analyze-website
Content-Type: application/x-www-form-urlencoded

url=https://example.com
```

#### Analyze GitHub Repository
```bash
POST /analyze-github
Content-Type: application/x-www-form-urlencoded

repo_url=https://github.com/owner/repository
```

#### Generate MCP Tools
```bash
POST /generate-mcp-tools
Content-Type: application/json

{
  "session_id": "your-session-id"
}
```

#### Get Session Information
```bash
GET /session/{session_id}
```

#### Get API Endpoints
```bash
GET /api-endpoints/{session_id}
```

#### Test API Endpoint
```bash
POST /test-endpoint
Content-Type: application/x-www-form-urlencoded

session_id=your-session-id
endpoint_url=https://api.example.com/endpoint
method=POST
headers={"Content-Type": "application/json"}
body={"key": "value"}
```

#### WebSocket Chat
```bash
WS /chat/{session_id}
```

## 🧪 Testing

### Automated Test Suite

Run the comprehensive test suite:

```bash
# Test with default URL (httpbin.org)
python test_app.py

# Test with custom URL
python test_app.py https://api.github.com
```

### Manual Testing

1. **Start the server**:
   ```bash
   python main.py
   ```

2. **Test with curl**:
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Analyze website
   curl -X POST http://localhost:8000/analyze-website \
     -F "url=https://httpbin.org"
   
   # Analyze GitHub repository
   curl -X POST http://localhost:8000/analyze-github \
     -F "repo_url=https://github.com/octocat/Hello-World"
   ```

3. **Test WebSocket chat** (using wscat or similar):
   ```bash
   # Install wscat
   npm install -g wscat
   
   # Connect to chat
   wscat -c ws://localhost:8000/chat/your-session-id
   ```

## 🏗️ Architecture

### Core Components

1. **Website Analyzer** (`app/website_analyzer.py`):
   - Crawls websites and extracts structure
   - Identifies forms, links, and resources
   - Parses HTML content
   - Intelligent link discovery for API-related pages

2. **GitHub Analyzer** (`app/github_analyzer.py`):
   - Analyzes public GitHub repositories
   - Extracts API endpoints from code files
   - Finds OpenAPI/Swagger specifications
   - Supports multiple programming languages

3. **API Discoverer** (`app/api_discoverer.py`):
   - Finds OpenAPI/Swagger documentation
   - Discovers API endpoints from forms and JavaScript
   - Extracts authentication information

4. **MCP Server** (`app/mcp_server.py`):
   - Generates MCP tools from discovered APIs
   - Categorizes tools by functionality
   - Creates tool schemas

5. **Chatbot** (`app/chatbot.py`):
   - Processes natural language requests
   - Executes MCP tools
   - Manages user context and authentication

6. **Database** (`app/database.py`):
   - Manages user sessions
   - Stores analysis results
   - Persists chat history

### Data Models

- **WebsiteAnalysis**: Website structure and metadata
- **APIDiscovery**: Discovered API endpoints and schemas
- **MCPTool**: Generated MCP tool definitions
- **UserSession**: User session and context
- **ChatMessage**: Chat conversation history

## 🔧 Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Database configuration
DATA_DIR=data

# Logging
LOG_LEVEL=INFO
```

### Customization

1. **Add new tool categories** in `app/mcp_server.py`
2. **Extend API discovery patterns** in `app/api_discoverer.py`
3. **Customize chatbot responses** in `app/chatbot.py`
4. **Modify website analysis** in `app/website_analyzer.py`

## 📦 Package Compatibility

All packages in `requirements.txt` have been verified for compatibility:

| Package | Version | Status |
|---------|---------|--------|
| fastapi | 0.104.1 | ✅ Compatible |
| uvicorn | 0.24.0 | ✅ Compatible |
| requests | 2.31.0 | ✅ Compatible |
| beautifulsoup4 | 4.12.2 | ✅ Compatible |
| selenium | 4.15.2 | ✅ Compatible |
| webdriver-manager | 4.0.1 | ✅ Compatible |
| openai | 1.3.7 | ✅ Compatible |
| python-multipart | 0.0.6 | ✅ Compatible |
| jinja2 | 3.1.2 | ✅ Compatible |
| aiofiles | 23.2.1 | ✅ Compatible |
| python-jose[cryptography] | 3.3.0 | ✅ Compatible |
| passlib[bcrypt] | 1.7.4 | ✅ Compatible |
| pydantic | 2.5.0 | ✅ Compatible |
| httpx | 0.25.2 | ✅ Compatible |
| websockets | 12.0 | ✅ Compatible |
| PyYAML | 6.0.1 | ✅ Compatible |
| python-dotenv | 1.0.0 | ✅ Compatible |

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Find and kill process using port 8000
   lsof -ti:8000 | xargs kill -9
   ```

2. **Import errors**:
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

3. **WebSocket connection issues**:
   - Check if the server is running
   - Verify the session ID is valid
   - Check browser console for errors

4. **Website analysis fails**:
   - Verify the URL is accessible
   - Check if the website blocks automated requests
   - Try with a different website

### Debug Mode

Enable debug mode for detailed logging:

```bash
export LOG_LEVEL=DEBUG
python main.py
```

### Debugging API Discovery

If no API endpoints are being discovered, use the debug script:

```bash
# Debug API discovery for a specific website
python debug_api_discovery.py https://example.com

# Check the detailed logs
tail -f logs/app.log
```

The debug script will show:
- Website analysis results
- Form discovery details
- JavaScript file analysis
- OpenAPI/Swagger search results
- Common API path testing
- Detailed logging of the discovery process

### Log Files

The application creates several log files:

- `logs/app.log` - Main application log with DEBUG level
- `logs/error.log` - Error-level messages only
- Console output - INFO level messages

To view real-time logs:
```bash
# View all logs
tail -f logs/app.log

# View only errors
tail -f logs/error.log

# Search for API discovery logs
grep "API" logs/app.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Beautiful Soup for HTML parsing
- MCP (Model Context Protocol) for the tool specification
- All contributors and testers

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation

---

**Happy coding! 🚀**
