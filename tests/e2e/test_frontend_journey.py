"""
Test script to simulate the Figma prototype journey through the frontend API
"""
import requests
import json
import time

BASE_URL = "http://localhost:8003"

def test_journey():
    """Test the three conversation turns from the Figma prototype"""
    
    print("=" * 60)
    print("TESTING FIGMA PROTOTYPE JOURNEY")
    print("=" * 60)
    
    # Journey turns from the Figma prototype
    turns = [
        "Hi, who are you?",
        "Can you check Uber prices from Downtown to Marina?",
        "What's the cheapest option?"
    ]
    
    conversation_id = None
    all_messages = []
    
    for i, user_message in enumerate(turns, 1):
        print(f"\n{'─' * 60}")
        print(f"Turn {i}/{len(turns)}")
        print(f"{'─' * 60}")
        print(f"\n👤 USER: {user_message}")
        
        # Add user message to history
        all_messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Prepare request
        payload = {
            "messages": all_messages
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        # Make request
        try:
            print("\n⏳ Sending request to backend...")
            response = requests.post(
                f"{BASE_URL}/history/generate",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract conversation ID
                if "history_metadata" in data and "conversation_id" in data["history_metadata"]:
                    conversation_id = data["history_metadata"]["conversation_id"]
                
                # Extract AI response
                if "choices" in data and len(data["choices"]) > 0:
                    ai_message = data["choices"][0]["messages"][0]
                    ai_content = ai_message["content"]
                    
                    print(f"\n🤖 ASSISTANT: {ai_content}")
                    
                    # Add to message history
                    all_messages.append({
                        "role": "assistant",
                        "content": ai_content
                    })
                    
                    print(f"\n✓ Turn {i} completed successfully")
                else:
                    print("\n❌ ERROR: No response in data")
                    print(f"Response data: {json.dumps(data, indent=2)}")
                    break
            else:
                print(f"\n❌ ERROR: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                break
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            break
        
        # Small delay between turns
        if i < len(turns):
            time.sleep(2)
    
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"✓ Completed {len(all_messages) // 2} conversation turns")
    print(f"✓ Total messages: {len(all_messages)}")
    if conversation_id:
        print(f"✓ Conversation ID: {conversation_id}")
    print(f"{'=' * 60}\n")

if __name__ == "__main__":
    test_journey()
