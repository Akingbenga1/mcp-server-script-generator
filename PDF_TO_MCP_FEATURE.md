# PDF-to-MCP Generation Feature

## Overview

This feature allows you to upload PDF files containing API documentation and automatically generate 3 files needed to create a complete MCP (Model Context Protocol) server:

1. **`mcp_server.py`** - Complete FastMCP server with API endpoints
2. **`requirements.txt`** - All Python dependencies 
3. **`Dockerfile`** - Ready-to-deploy container configuration

## How to Use

### Web Interface (Recommended)

1. **Start the server:**
   ```bash
   python3 main.py
   ```

2. **Open your browser to:**
   ```
   http://localhost:8001
   ```

3. **Find the "Generate MCP Server from PDF" section** (green section on the page)

4. **Upload your PDF:**
   - Select a PDF file containing API documentation
   - Optionally set a production API base URL
   - Choose extractor type (PyPDF2 or PDFPlumber)
   - Choose parser type (OpenAPI/Swagger or Markdown)

5. **Click "Generate & Download MCP Server Files"**

6. **Download the zip file** containing all 3 files

### API Endpoint

You can also use the REST API directly:

```bash
curl -X POST "http://localhost:8001/generate-mcp-from-pdf" \
  -F "file=@your_api_documentation.pdf" \
  -F "extractor_type=pypdf" \
  -F "parser_type=openapi" \
  -F "production_base_url=https://api.example.com/v1" \
  -o generated_mcp_server.zip
```

## Supported PDF Formats

The feature works best with PDFs that contain:

- **API endpoint definitions** (GET, POST, PUT, DELETE, PATCH)
- **URL paths** (e.g., `/users`, `/users/{id}`)
- **HTTP methods** clearly specified
- **Parameter descriptions**
- **Request/response examples**

### Example API Documentation Format

```
GET /users
Description: Get all users
Parameters: None
Response: JSON array of user objects

POST /users  
Description: Create a new user
Parameters:
- name (string, required): User's full name
- email (string, required): User's email address
Request Body: {"name": "John", "email": "john@example.com"}
```

## Generated Files

### 1. mcp_server.py
- Complete FastMCP server implementation
- Individual tools for each API endpoint
- Generic HTTP method tools (GET, POST, PUT, DELETE)
- Comprehensive error handling
- Type-safe parameter handling
- Production-ready configuration

### 2. requirements.txt
- FastMCP framework
- HTTP client (aiohttp)
- JSON handling libraries
- Type checking support
- Environment variable management
- Data validation (Pydantic)

### 3. Dockerfile
- Python 3.11 slim base image
- System dependencies (gcc)
- Python package installation
- Proper working directory setup
- Port exposure (8000)
- Environment variables
- Ready-to-run configuration

## Configuration Options

### Extractor Types
- **PyPDF2**: Faster extraction, good for simple PDFs
- **PDFPlumber**: More accurate extraction, better for complex layouts

### Parser Types
- **OpenAPI/Swagger**: Best for formal API documentation
- **Markdown**: Good for documentation in markdown format

### Production Base URL
- Optional parameter to set the actual API base URL
- If not provided, uses `https://api.example.com` as placeholder
- Example: `https://api.mycompany.com/v1`

## Running the Generated MCP Server

After downloading and extracting the zip file:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python mcp_server.py
```

Or using Docker:

```bash
# Build the image
docker build -t my-mcp-server .

# Run the container
docker run -p 8000:8000 my-mcp-server
```

## Troubleshooting

### No API Endpoints Found
- Ensure your PDF contains clear API endpoint definitions
- Try different extractor/parser combinations
- Check that HTTP methods (GET, POST, etc.) are clearly specified

### Poor Extraction Quality
- Use PDFPlumber extractor for complex layouts
- Ensure PDF text is selectable (not just images)
- Consider converting images to text-based PDF first

### Server Errors
- Check that all dependencies are installed
- Ensure Python 3.11+ is being used
- Verify that the generated code is syntactically correct

## Technical Details

- **Framework**: FastMCP (latest version)
- **Python Version**: 3.11+
- **PDF Processing**: PyPDF2 + PDFPlumber
- **Parameter Detection**: Automatic source detection (path, query, body, header)
- **Error Handling**: Comprehensive with status codes and messages
- **Authentication**: Header-based (configurable)

## Examples

The repository includes a test script demonstrating the functionality:

```bash
python3 test_pdf_feature_demo.py
```

This script shows how the feature works with sample API endpoints and generates all three files programmatically.