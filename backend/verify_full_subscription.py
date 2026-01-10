import requests
import sys
import os
import time
import json

# Base URL for the backend
BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8003")
print(f"Targeting: {BASE_URL}")

def verify_all_tracking():
    print("--- COMPREHENSIVE SUBSCRIPTION TRACKING VERIFICATION ---")
    
    # 1. Setup - Create a test user or use an existing one
    # For this script, we'll assume we can use a test user ID
    user_id = "verify-user-123"
    
    print(f"User ID: {user_id}")
    
    # helper for entitlements
    def get_entitlements():
        try:
            r = requests.get(
                f"{BASE_URL}/api/growth/entitlements", 
                headers={"X-Test-User-Id": user_id}
            )
            if r.status_code == 200:
                return r.json()
            else:
                print(f"Error fetching entitlements: {r.status_code} - {r.text}")
                return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    # Step 0: Ensure user exists in DB
    def ensure_user():
        # Using a simple register or debug endpoint if available, 
        # but since we have DB access in our environment, we could just check.
        # For now, if get_entitlements returns 401/404, we'll know.
        pass

    # 2. Initial State
    initial = get_entitlements()
    if not initial:
        print("❌ FAILED: Could not fetch initial entitlements.")
        return
    
    print("\nInitial Usage:")
    print(json.dumps(initial.get('usage', {}), indent=2))
    
    # 3. Test Goal Tracking
    print("\nTesting Goal Tracking...")
    # Directly use internal routes if they exist, or just check the impact of db entries
    # For verification, we'll check if the counts increment correctly.
    # We'll assume the system is running and we can interact with it.
    
    # 4. Test AI Chat (Calls and Tokens)
    print("\nTesting AI Chat Tracking...")
    # Using the chat_service/routes.py endpoint
    try:
        headers = {"X-Test-User-Id": user_id}
        # Start a session
        # Start a session
        start_r = requests.post(f"{BASE_URL}/api/chat/start", json={"user_id": user_id, "mode": "advisory"}, headers=headers)
        if start_r.status_code == 201:
            session_id = start_r.json().get("session_id")
            print(f"Started chat session: {session_id}")
            
            # Send a message
            msg_r = requests.post(f"{BASE_URL}/api/chat/{session_id}/message", json={
                "user_id": user_id,
                "message": "Explain subscription tracking to me."
            }, headers=headers)
            if msg_r.status_code == 200:
                print("Sent chat message.")
                # The response should contain usage
                usage = msg_r.json().get("usage", {})
                print(f"Message Usage returned: {usage}")
            else:
                print(f"Failed to send message: {msg_r.status_code} - {msg_r.text}")
        else:
            print(f"Failed to start chat: {start_r.status_code} - {start_r.text}")
    except Exception as e:
        print(f"Chat test error: {e}")

    # 5. Verify Incremented Usage
    time.sleep(1) # wait for db commit/events
    after = get_entitlements()
    if not after:
        print("❌ FAILED: Could not fetch entitlements after actions.")
        return
    
    print("\nUsage After Chat:")
    print(json.dumps(after.get('usage', {}), indent=2))
    
    # Compare AI calls and tokens
    initial_calls = initial['usage'].get('ai_chat_calls', 0)
    after_calls = after['usage'].get('ai_chat_calls', 0)
    
    initial_tokens = initial['usage'].get('total_tokens_month', 0)
    after_tokens = after['usage'].get('total_tokens_month', 0)
    
    print("\nVerification Results:")
    if after_calls > initial_calls:
        print(f"✅ AI Chat Calls incremented: {initial_calls} -> {after_calls}")
    else:
        print(f"❌ AI Chat Calls DID NOT increment.")
        
    if after_tokens > initial_tokens:
        print(f"✅ AI Tokens incremented: {initial_tokens} -> {after_tokens}")
    else:
        print(f"❌ AI Tokens DID NOT increment.")

    # 6. Test Smart Recommendations (Mocking for now as it's harder to trigger via simple API)
    # 7. Test Executions (Audit Log)
    
    print("\nFull Usage Payload:")
    print(json.dumps(after, indent=2))

if __name__ == "__main__":
    import json
    verify_all_tracking()
