import aiohttp
import asyncio
import json

async def discover_ollama_models(base_url: str = "http://localhost:11434"):
    """Discover and list all available Ollama models"""
    try:
        async with aiohttp.ClientSession() as session:
            # Get list of all models
            async with session.get(f"{base_url}/api/tags") as response:
                if response.status == 200:
                    models_data = await response.json()
                    models = models_data.get('models', [])
                    
                    print("🔍 Available Ollama Models:")
                    print("=" * 50)
                    
                    for i, model in enumerate(models):
                        model_name = model.get('name', 'Unknown')
                        model_size = model.get('size', 0)
                        model_modified = model.get('modified_at', 'Unknown')
                        
                        print(f"{i+1}. {model_name}")
                        print(f"   Size: {model_size:,} bytes")
                        print(f"   Modified: {model_modified}")
                        print()
                    
                    return models
                else:
                    print(f"❌ Error: {response.status}")
                    return []
                    
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        return []

async def get_first_model(base_url: str = "http://localhost:11434"):
    """Get the first available Ollama model"""
    models = await discover_ollama_models(base_url)
    
    if models:
        first_model = models[0]
        model_name = first_model.get('name', 'Unknown')
        print(f"✅ First model selected: {model_name}")
        return model_name
    else:
        print("❌ No models found")
        return None

async def get_model_info(model_name: str, base_url: str = "http://localhost:11434"):
    """Get detailed information about a specific model"""
    try:
        async with aiohttp.ClientSession() as session:
            # Get model info
            async with session.post(f"{base_url}/api/show", json={"name": model_name}) as response:
                if response.status == 200:
                    model_info = await response.json()
                    print(f"📋 Model Info for {model_name}:")
                    print("=" * 50)
                    print(f"Name: {model_info.get('name', 'Unknown')}")
                    print(f"Size: {model_info.get('size', 0):,} bytes")
                    print(f"Modified: {model_info.get('modified_at', 'Unknown')}")
                    print(f"Format: {model_info.get('format', 'Unknown')}")
                    print(f"Parameters: {model_info.get('parameter_size', 'Unknown')}")
                    print(f"Quantization: {model_info.get('quantization_level', 'Unknown')}")
                    return model_info
                else:
                    print(f"❌ Error getting model info: {response.status}")
                    return None
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Usage example
async def main():
    print("🚀 Ollama Model Discovery")
    print("=" * 50)
    
    # Discover and list all models
    models = await discover_ollama_models()
    
    if models:
        # Get the first model
        first_model = await get_first_model()
        
        if first_model:
            # Get detailed info about the first model
            await get_model_info(first_model)
            
            # You can now use this model name
            print(f"\n🎯 Ready to use model: {first_model}")
    else:
        print("❌ No Ollama models found. Make sure Ollama is running.")

# Run the discovery
if __name__ == "__main__":
    asyncio.run(main())
