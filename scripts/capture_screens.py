import asyncio
import os
import sys
from playwright.async_api import async_playwright

# Configuration
TARGET_URL = os.getenv("HELM_APP_URL", "https://lfsd-frontend-692544481281.us-central1.run.app") 
OUTPUT_DIR = r"c:\Users\hmahm\OneDrive\Desktop\LFSD Codebase\LFSD\helm-landing\public\screenshots"

async def capture_screenshots(url):
    print(f"Starting screenshot capture for: {url}")
    
    if "REPLACE_ME" in url:
        print("ERROR: Please set HELM_APP_URL environment variable or update the script with the actual deployed URL.")
        return

    async with async_playwright() as p:
        # Browser setup (using chromium)
        browser = await p.chromium.launch(headless=True)
        
        # Mobile View (iPhone 14 Pro ish)
        mobile_context = await browser.new_context(
            viewport={"width": 393, "height": 852},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        )
        
        # Desktop View
        desktop_context = await browser.new_context(
            viewport={"width": 1440, "height": 900}
        )
        
        # Setup output directory
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        # Main Page Context for Login
        page_mobile = await mobile_context.new_page()
        
        # 0. Login (We need to login to see meaningful screens)
        try:
             print("Navigating to Login...")
             await page_mobile.goto(f"{url}/login", timeout=60000)
             
             # Check if we are actually at login
             if "login" in page_mobile.url:
                 print("Attempting login with finance@helm.com...")
                 await page_mobile.fill("input[type='email']", "finance@helm.com")
                 await page_mobile.fill("input[type='password']", "password") 
                 
                 await page_mobile.click("button[type='submit']") 
                 await page_mobile.wait_for_url("**/dashboard", timeout=20000)
                 print("Login successful!")
        except Exception as e:
            print(f"Login attempt failed or unnecessary: {e}")

        # --- Scenario 1: Home Page with Three Gauges ---
        try:
            print("Navigating to Home/Dashboard (Mobile)...")
            await page_mobile.goto(f"{url}/dashboard", timeout=60000) 
            await page_mobile.wait_for_load_state("networkidle")
            # Wait a bit for gauges to render
            await page_mobile.wait_for_timeout(2000)
            await page_mobile.screenshot(path=os.path.join(OUTPUT_DIR, "home_gauges_mobile.png"))
            print("Captured home_gauges_mobile.png")
        except Exception as e:
            print(f"Failed to capture Home: {e}")

        # --- Scenario 2: Dashboard (Spending or another dashboard) ---
        try:
            print("Navigating to Spending Dashboard (Mobile)...")
            await page_mobile.goto(f"{url}/spending")
            await page_mobile.wait_for_load_state("networkidle")
            await page_mobile.wait_for_timeout(1000)
            await page_mobile.screenshot(path=os.path.join(OUTPUT_DIR, "dashboard_mobile.png"))
            print("Captured dashboard_mobile.png")
        except Exception as e:
             print(f"Failed to capture Dashboard: {e}")

        # --- Scenario 3: Chat with Jumeirah Hotel to Airport conversation ---
        try:
            print("Navigating to Chat (Mobile)...")
            await page_mobile.goto(f"{url}/chat")
            await page_mobile.wait_for_load_state("networkidle")
            
            # Simulate Interaction - type the message about Jumeirah to airport
            chat_input = page_mobile.locator("input[type='text'], textarea")
            if await chat_input.count() > 0:
                 await chat_input.fill("I need a ride from Jumeirah Hotel to the airport tomorrow at 8 AM")
                 await page_mobile.keyboard.press("Enter")
                 # Wait for response
                 await page_mobile.wait_for_timeout(5000) 
            
            await page_mobile.screenshot(path=os.path.join(OUTPUT_DIR, "chat_booking_mobile.png"))
            print("Captured chat_booking_mobile.png")
        except Exception as e:
             print(f"Failed to capture Chat: {e}")

        await browser.close()
        print("Done.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = TARGET_URL
        
    asyncio.run(capture_screenshots(url))
