#!/usr/bin/env python3
"""
Startup script for the Website MCP Chatbot application
"""

import sys
import os
import subprocess
import importlib.util

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'aiohttp': 'aiohttp',
        'beautifulsoup4': 'bs4',
        'requests': 'requests',
        'jinja2': 'jinja2',
        'pydantic': 'pydantic',
        'PyYAML': 'yaml',
        'ollama': 'ollama',
        'langchain': 'langchain',
        'langchain_community': 'langchain_community',
        'langchain_core': 'langchain_core',
        'langchain_ollama': 'langchain_ollama',
        'typing_extensions': 'typing_extensions'
    }
    
    missing_packages = []
    
    for package, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} - MISSING")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    print("\nAll dependencies are installed!")
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Website MCP Chatbot...")
    print("=" * 50)
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    print("\nStarting FastAPI server...")
    print("Access the application at: http://localhost:8001")
    print("API documentation at: http://localhost:8001/docs")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8080",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
