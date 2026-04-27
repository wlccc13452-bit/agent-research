"""
Quick verification of the fix
"""
import requests
import json

def verify_fix():
    """Quick test to verify the fix works"""
    print("=" * 60)
    print("VERIFICATION TEST")
    print("=" * 60)
    
    # Test 1: Backend responding?
    print("\n[1] Testing backend...")
    try:
        response = requests.get("http://localhost:8000/api/feishu/test", timeout=5)
        print(f"    Backend: {response.json()['status']}")
    except Exception as e:
        print(f"    Backend: ERROR - {e}")
        return
    
    # Test 2: WebSocket status
    print("\n[2] Checking WebSocket...")
    try:
        response = requests.get("http://localhost:8000/api/feishu/websocket-status", timeout=5)
        status = response.json()
        print(f"    Active connections: {status['active_connections']}")
    except Exception as e:
        print(f"    WebSocket: ERROR - {e}")
        return
    
    # Test 3: Webhook with fixed timestamp
    print("\n[3] Testing webhook with fixed timestamp...")
    webhook_payload = {
        "schema_version": "2.0",
        "header": {
            "event_id": "fix_test",
            "event_type": "im.message.receive_v1",
            "create_time": "1234567890000",  # String timestamp (fixed)
            "token": "test",
            "app_id": "test",
            "tenant_key": "test"
        },
        "event": {
            "sender": {
                "sender_id": {"user_id": "test_user", "open_id": "ou_test"},
                "sender_type": "user",
                "tenant_key": "test"
            },
            "message": {
                "message_id": "test_msg",
                "create_time": "1234567890000",  # String timestamp
                "chat_id": "oc_test",
                "message_type": "text",
                "content": json.dumps({"text": "查询 000001"})
            }
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/feishu/webhook",
            json=webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"    Webhook: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            print("\n[PASS] Webhook accepted!")
            print("\nNEXT STEPS:")
            print("1. Check frontend console for 'feishu-chat-message'")
            print("2. Check backend logs for '[WEBSOCKET] Broadcasting' messages")
            print("3. Send a real message from Feishu app to verify end-to-end")
        else:
            print(f"\n[FAIL] Webhook rejected: {response.text}")
            
    except Exception as e:
        print(f"    Webhook: ERROR - {e}")
    
    print("=" * 60)


if __name__ == "__main__":
    verify_fix()
