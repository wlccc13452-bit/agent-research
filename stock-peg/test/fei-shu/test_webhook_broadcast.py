"""
Test Feishu webhook broadcast via real HTTP request
"""
import requests
import json
import time

def test_webhook_broadcast():
    """Test if webhook triggers WebSocket broadcast"""
    print("=" * 60)
    print("Testing Feishu Webhook -> WebSocket Broadcast")
    print("=" * 60)
    
    # Check WebSocket status first
    print("\n[Step 1] Checking WebSocket status...")
    response = requests.get("http://localhost:8000/api/feishu/websocket-status")
    status = response.json()
    print(f"   Active connections: {status['active_connections']}")
    print(f"   Stock subscriptions: {status['stock_subscriptions']}")
    
    if status['active_connections'] == 0:
        print("   [WARNING] No WebSocket connections! Frontend may not be connected.")
        return
    
    # Simulate a Feishu webhook event (message receive)
    print("\n[Step 2] Simulating Feishu webhook event...")
    webhook_payload = {
        "schema_version": "2.0",
        "header": {
            "event_id": "test_event_001",
            "event_type": "im.message.receive_v1",
            "create_time": str(int(time.time() * 1000)),
            "token": "test_token",
            "app_id": "test_app_id",
            "tenant_key": "test_tenant"
        },
        "event": {
            "sender": {
                "sender_id": {
                    "user_id": "test_user_001",
                    "open_id": "ou_test_user_001"
                },
                "sender_type": "user",
                "tenant_key": "test_tenant"
            },
            "message": {
                "message_id": "test_msg_" + str(int(time.time())),
                "root_id": "",
                "parent_id": "",
                "create_time": str(int(time.time() * 1000)),
                "chat_id": "oc_test_chat_001",
                "message_type": "text",
                "content": json.dumps({"text": "查询 平安银行"}),
                "mentions": []
            }
        }
    }
    
    print(f"   Sending webhook with command: '查询 平安银行'")
    print(f"   Chat ID: oc_test_chat_001")
    
    try:
        # Note: This will fail signature verification in production
        # But we can check backend logs to see if broadcast was attempted
        response = requests.post(
            "http://localhost:8000/api/feishu/webhook",
            json=webhook_payload,
            headers={
                "Content-Type": "application/json",
                "X-Lark-Request-Timestamp": str(int(time.time())),
                "X-Lark-Request-Nonce": "test_nonce",
                "X-Lark-Signature": "test_signature"  # Will fail verification
            }
        )
        
        print(f"\n[Step 3] Webhook response: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 401:
            print("\n   [EXPECTED] Signature verification failed (security feature)")
            print("   Check backend logs for broadcast attempt...")
        elif response.status_code == 200:
            print("\n   [SUCCESS] Webhook accepted")
            print("   Check frontend console for WebSocket message...")
        
    except Exception as e:
        print(f"\n[ERROR] Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Check backend logs for '[WEBSOCKET]' messages")
    print("2. Check frontend console for 'feishu-chat-message' messages")
    print("3. If no messages, WebSocket broadcast may not be working")
    print("=" * 60)


if __name__ == "__main__":
    test_webhook_broadcast()
