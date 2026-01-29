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

        # --- Scenario 1: Dashboard / Today ---
        page_mobile = await mobile_context.new_page()
        try:
            print("Navigating to Dashboard (Mobile)...")
            await page_mobile.goto(f"{url}/dashboard", timeout=60000) 
            # Add login logic here if redirected to login
            # await page_mobile.fill("input[type='email']", "demo@helm.com")
            # await page_mobile.fill("input[type='password']", "password")
            # await page_mobile.click("button[type='submit']")
            # await page_mobile.wait_for_url("**/dashboard")
            
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

        # --- Scenario 3: Desktop Home (for variety) ---
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
