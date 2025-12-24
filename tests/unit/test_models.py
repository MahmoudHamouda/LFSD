from google import genai
import os

api_key = "AIzaSyCunqpwCFxCocnE6xZlzoDQ1hoJZcRtLPQ"
client = genai.Client(api_key=api_key)

# Try different models
models_to_try = [
    'gemini-1.5-flash',
    'gemini-1.5-pro', 
    'gemini-2.0-flash-exp',
    'gemini-pro'
]

for model_name in models_to_try:
    try:
        print(f"\nTrying model: {model_name}")
        response = client.models.generate_content(
            model=model_name,
            contents='Say hello'
        )
        print(f"✅ SUCCESS with {model_name}!")
        print(f"Response: {response.text}")
        break
    except Exception as e:
        print(f"❌ Failed with {model_name}: {str(e)[:100]}")
