import requests
import json
from PIL import Image, ImageDraw, ImageFont
import io

BASE_URL = "http://127.0.0.1:8018/api"
USER_ID = "default_user"

def test_google_auth_url():
    print("Testing Google Auth URL...")
    try:
        response = requests.get(f"{BASE_URL}/time/users/{USER_ID}/calendar/google/connect")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Response:", response.json())
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"FAILED: {e}")

def create_dummy_calendar_image():
    # Create an image with some text that looks like a calendar event
    img = Image.new('RGB', (500, 300), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    # Just basic text, Tesseract needs clean text
    # Assuming default font is available or fallback
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        
    text = """
    Meeting with Team
    Start: 2025-10-25T10:00:00
    End: 2025-10-25T11:00:00
    Category: Work
    """
    d.text((10,10), text, fill=(0,0,0), font=font)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_ocr_upload():
    print("\nTesting OCR Upload...")
    try:
        img_data = create_dummy_calendar_image()
        files = {'file': ('calendar.png', img_data, 'image/png')}
        
        response = requests.post(
            f"{BASE_URL}/time/users/{USER_ID}/calendar/upload",
            files=files
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Response:", response.json())
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_google_auth_url()
    # Uncomment to test OCR if Tesseract is confirmed installed
    test_ocr_upload()
