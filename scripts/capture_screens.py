import asyncio
import os
import sys
from playwright.async_api import async_playwright

# Configuration
# TARGET_URL = "https://lfsd-frontend-326887569107.us-central1.run.app" # REPLACE THIS with actual URL
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
        
        # 0. Login (We need to login to see meaningful Chat/Profile)
        try:
             print("Navigating to Login...")
             # Assuming direct access to /dashboard redirects to login, or we go to /login
             await page_mobile.goto(f"{url}/login", timeout=60000)
             
             # Check if we are actually at login (if not authenticated)
             if "login" in page_mobile.url:
                 # FILL WITH DEMO CREDENTIALS - ADJUST SELECTORS AS NEEDED
                 print("Attempting login with finance@helm.com...")
                 await page_mobile.fill("input[type='email']", "finance@helm.com")
                 await page_mobile.fill("input[type='password']", "password") 
                 
                 await page_mobile.click("button[type='submit']") 
                 await page_mobile.wait_for_url("**/dashboard", timeout=20000)
        except Exception as e:
            print(f"Login attempt failed or unnecessary: {e}")

        # --- Scenario 1: Dashboard / Today ---
        try:
            print("Navigating to Dashboard (Mobile)...")
            await page_mobile.goto(f"{url}/dashboard", timeout=60000) 
            await page_mobile.wait_for_load_state("networkidle")
            await page_mobile.screenshot(path=os.path.join(OUTPUT_DIR, "dashboard_mobile.png"))
            print("Captured dashboard_mobile.png")
        except Exception as e:
            print(f"Failed to capture Dashboard: {e}")

        # --- Scenario 2: Spending Overview ---
        try:
            print("Navigating to Spending (Mobile)...")
            await page_mobile.goto(f"{url}/spending")
            await page_mobile.wait_for_load_state("networkidle")
            await page_mobile.screenshot(path=os.path.join(OUTPUT_DIR, "spending_mobile.png"))
            print("Captured spending_mobile.png")
        except Exception as e:
             print(f"Failed to capture Spending: {e}")

        # --- Scenario 3: Profile with Connections --- (REQUESTED)
        try:
            print("Navigating to Profile (Mobile)...")
            # Assuming /profile path
            await page_mobile.goto(f"{url}/profile")
            await page_mobile.wait_for_load_state("networkidle")
            await page_mobile.screenshot(path=os.path.join(OUTPUT_DIR, "profile_mobile.png"))
            print("Captured profile_mobile.png")
        except Exception as e:
             print(f"Failed to capture Profile: {e}")

        # --- Scenario 4: Chat Interaction (Booking) --- (REQUESTED)
        try:
            print("Navigating to Chat (Mobile)...")
            await page_mobile.goto(f"{url}/chat")
            await page_mobile.wait_for_load_state("networkidle")
            
            # Simulate Interaction
            # Check if there is an input box
            chat_input = page_mobile.locator("input[type='text'], textarea")
            if await chat_input.count() > 0:
                 await chat_input.fill("I need to book a ride to the airport for tomorrow morning.")
                 await page_mobile.keyboard.press("Enter")
                 # Wait for response (simple wait)
                 await page_mobile.wait_for_timeout(3000) 
            
            await page_mobile.screenshot(path=os.path.join(OUTPUT_DIR, "chat_mobile.png"))
            print("Captured chat_mobile.png")
        except Exception as e:
             print(f"Failed to capture Chat: {e}")

        # --- Scenario 5: Desktop Home (for variety) ---
        page_desktop = await desktop_context.new_page()
        try:
             print("Navigating to Home (Desktop)...")
             await page_desktop.goto(f"{url}/")
             await page_desktop.wait_for_load_state("networkidle")
             await page_desktop.screenshot(path=os.path.join(OUTPUT_DIR, "home_desktop.png"))
             print("Captured home_desktop.png")
        except Exception as e:
            print(f"Failed to capture Home Desktop: {e}")

        await browser.close()
        print("Done.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = TARGET_URL
        
    asyncio.run(capture_screenshots(url))
