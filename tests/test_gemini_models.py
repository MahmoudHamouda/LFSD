import google.generativeai as genai
from core.config import get_settings
import os

def test_gemini():
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY
    print(f"Testing Gemini with key: {api_key[:5]}...")
    
    genai.configure(api_key=api_key)
    
    print("\nListing available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

if __name__ == "__main__":
    test_gemini()
