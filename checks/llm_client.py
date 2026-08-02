import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "model": "gemini-2.0-flash",
    },
    # Ollama fallback (requires local setup)
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key_env": "OLLAMA_API_KEY", # Usually not needed for local ollama, but good for uniformity
        "model": "llama3",
    }
}

def get_client(provider: str = "groq") -> tuple[OpenAI, str]:
    cfg = PROVIDERS[provider]
    
    api_key = os.environ.get(cfg["api_key_env"], "dummy-key-for-local")
    
    client = OpenAI(base_url=cfg["base_url"], api_key=api_key)
    return client, cfg["model"]
