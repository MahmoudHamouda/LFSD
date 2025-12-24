import google.generativeai as genai
import asyncio
import os

# Use the key that we know works
api_key = "AIzaSyBTeVnxIK98KHnToQRNWw_HJgsfDHh0pJI"
genai.configure(api_key=api_key)

async def test_async():
    model_name = "models/gemini-1.5-flash"
    print(f"Testing async with model: {model_name}")
    
    model = genai.GenerativeModel(model_name)
    
    try:
        print("Testing SYNC...")
        response_sync = model.generate_content("Hello")
        print(f"✅ SYNC Success! Response: {response_sync.text}")
    except Exception as e:
        print(f"❌ SYNC Failed: {e}")

    try:
        print("Testing ASYNC...")
        response = await model.generate_content_async("Hello")
        print(f"✅ ASYNC Success! Response: {response.text}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_async())
