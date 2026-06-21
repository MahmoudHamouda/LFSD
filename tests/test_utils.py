import os
import sys
import threading

# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from core.authentication import create_access_token

_TOKEN_CACHE = {}

def get_auth0_token(email, password="P@ssword"):
    if email in _TOKEN_CACHE:
        return _TOKEN_CACHE[email]
        
    def _fetch():
        from playwright.sync_api import sync_playwright
        base_url = get_test_base_url()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            try:
                page.goto(base_url, timeout=60000)
                page.wait_for_load_state("networkidle")
                
                login_btn = page.locator("button:has-text('Log In'), a:has-text('Log In'), button:has-text('Sign In')")
                if login_btn.count() > 0:
                    login_btn.first.click()
                    page.wait_for_load_state("networkidle")
                
                username_selector = "input[type='email'], input[name='username'], input[name='email'], input[placeholder*='email']"
                password_selector = "input[type='password'], input[name='password']"
                
                page.wait_for_selector(username_selector, timeout=30000)
                page.wait_for_selector(password_selector, timeout=30000)
                
                page.fill(username_selector, email)
                page.fill(password_selector, password)
                
                submit_btn = page.locator("button[type='submit'], button:has-text('Continue'), button:has-text('Log In')")
                submit_btn.first.click()
                
                token = None
                for _ in range(20):
                    page.wait_for_timeout(1000)
                    token = page.evaluate("() => localStorage.getItem('token')")
                    if token:
                        _TOKEN_CACHE[email] = token
                        return token
                return None
            except Exception as e:
                print(f"Playwright Auth0 login failed for {email}: {e}")
                return None
            finally:
                browser.close()

    # Run the fetch function in a separate thread to prevent asyncio event loop clashes
    result = []
    def target():
        res = _fetch()
        result.append(res)
        
    t = threading.Thread(target=target)
    t.start()
    t.join()
    return result[0] if result else None

def get_auth_headers(email="health@helm.com"):
    base_url = get_test_base_url()
    if base_url.startswith("https://") or "helmory.com" in base_url:
        token = get_auth0_token(email)
        if token:
            return {"Authorization": f"Bearer {token}"}
            
    # Local fallback
    token = create_access_token({"sub": email})
    return {"Authorization": f"Bearer {token}"}

def get_test_base_url():
    return os.getenv("TEST_BASE_URL", "https://app.helmory.com")



