import google.generativeai as genai
import os

api_key = "AIzaSyBTeVnxIK98KHnToQRNWw_HJgsfDHh0pJI"
genai.configure(api_key=api_key)

try:
    print("Listing models...")
    models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    if not models:
        print("No generative models found!")
        exit(1)
        
    print(f"Found {len(models)} models.")
    
    # Try the first 3 models
    for m in models[:3]:
        print(f"\nTrying model: {m.name}")
        try:
            model = genai.GenerativeModel(m.name)
            response = model.generate_content('Hello')
            print(f"✅ SUCCESS with {m.name}!")
            print(f"!!! USE THIS MODEL NAME: {m.name} !!!")
            print(f"Response: {response.text}")
            break
        except Exception as e:
            print(f"❌ Failed with {m.name}: {e}")

except Exception as e:
    print(f"Error: {e}")
