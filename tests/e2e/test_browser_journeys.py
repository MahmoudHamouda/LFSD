import asyncio
import os
import sys
from playwright.async_api import async_playwright
from loguru import logger

# Output directory for screenshots
SCREENSHOT_DIR = r"C:\Users\hmahm\.gemini\antigravity\brain\392bf087-902d-4f6e-94c7-00458be598a0"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CREDENTIALS = [
    {"email": "finance@helm.com", "password": "P@ssword", "chat_prompt": "Can I afford to spend $500 on a watch?", "name": "finance"},
    {"email": "time@helm.com", "password": "P@ssword", "chat_prompt": "How much focus time did I have last week?", "name": "time"},
    {"email": "health@helm.com", "password": "P@ssword", "chat_prompt": "How much is an Uber to the Dubai Marina?", "name": "health"}
]

async def test_persona(browser, persona):
    email = persona["email"]
    password = persona["password"]
    name = persona["name"]
    prompt = persona["chat_prompt"]
    
    logger.info(f"Starting test for persona: {email}")
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    page = await context.new_page()
    
    try:
        # 1. Open Landing Page / Login
        logger.info("Navigating to https://app.helmory.com/")
        await page.goto("https://app.helmory.com/", timeout=60000)
        await page.wait_for_load_state("networkidle")
        
        # Click Log In
        login_btn = page.locator("button:has-text('Log In'), a:has-text('Log In'), button:has-text('Sign In')")
        if await login_btn.count() > 0:
            logger.info("Clicking Log In button...")
            await login_btn.first.click()
            await page.wait_for_load_state("networkidle")
        
        # 2. Wait for Auth0 Login Form
        logger.info("Waiting for login inputs...")
        username_selector = "input[type='email'], input[name='username'], input[name='email'], input[placeholder*='email']"
        password_selector = "input[type='password'], input[name='password']"
        
        await page.wait_for_selector(username_selector, timeout=30000)
        await page.wait_for_selector(password_selector, timeout=30000)
        
        logger.info("Filling credentials...")
        await page.fill(username_selector, email)
        await page.fill(password_selector, password)
        
        # Find Continue or Log In button
        submit_btn = page.locator("button[type='submit'], button:has-text('Continue'), button:has-text('Log In')")
        await submit_btn.first.click()
        logger.info("Login submitted. Waiting 10 seconds for redirect and dashboard load...")
        await asyncio.sleep(10)
        
        # 3. Capture Dashboard
        dash_screenshot = os.path.join(SCREENSHOT_DIR, f"{name}_dashboard.png")
        await page.screenshot(path=dash_screenshot)
        logger.info(f"Captured dashboard screenshot: {dash_screenshot}")
        
        # 4. Navigate to Profile
        logger.info("Navigating to Profile...")
        await page.goto("https://app.helmory.com/profile", timeout=30000)
        await asyncio.sleep(5)
        profile_screenshot = os.path.join(SCREENSHOT_DIR, f"{name}_profile_page.png")
        await page.screenshot(path=profile_screenshot)
        logger.info(f"Captured profile page screenshot: {profile_screenshot}")
        
        # 5. Navigate to Chat & Test AI responses
        logger.info("Navigating to Chat...")
        await page.goto("https://app.helmory.com/chat", timeout=30000)
        await asyncio.sleep(5)
        
        # Find the chat input textarea/input
        chat_input = page.locator("textarea, input[placeholder*='type'], input[placeholder*='ask'], [contenteditable='true']").first
        await chat_input.fill(prompt)
        await asyncio.sleep(1)
        await chat_input.press("Enter")
        logger.info(f"Sent prompt: '{prompt}'. Waiting 15 seconds for AI response...")
        await asyncio.sleep(15)
        
        # Capture Chat response
        chat_screenshot = os.path.join(SCREENSHOT_DIR, f"{name}_chat_response.png")
        await page.screenshot(path=chat_screenshot)
        logger.info(f"Captured chat response screenshot: {chat_screenshot}")
        
        # Extract response text to log
        # Let's grab all text on the chat page to see if response is present
        page_text = await page.evaluate("() => document.body.innerText")
        logger.info(f"AI Page Text Sample: {page_text[:500]}...")
        
    except Exception as e:
        logger.error(f"Error testing persona {email}: {e}")
        err_screenshot = os.path.join(SCREENSHOT_DIR, f"{name}_error.png")
        await page.screenshot(path=err_screenshot)
        logger.error(f"Captured error screenshot: {err_screenshot}")
    finally:
        await context.close()

async def main():
    logger.info("Starting Playwright E2E UI/UX Test Suite...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for persona in CREDENTIALS:
            await test_persona(browser, persona)
        await browser.close()
    logger.info("Playwright E2E UI/UX Test Suite Complete!")

if __name__ == "__main__":
    asyncio.run(main())
