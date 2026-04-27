"""End-to-end WebSocket broadcast test"""
import asyncio
import json
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

print("\n" + "=" * 60)
print("End-to-End WebSocket Broadcast Test")
print("=" * 60)

# Step 1: Check WebSocket connections
print("\n1. Checking WebSocket connections...")
resp = requests.post(f"{BASE_URL}/api/feishu/test-broadcast", timeout=3)
data = resp.json()
print(f"   Active connections: {data['active_connections']}")

if data['active_connections'] == 0:
    print("\n   [ERROR] No WebSocket connections!")
    print("   Please ensure frontend is running (http://localhost:5173)")
    exit(1)

# Step 2: Simulate a Feishu webhook message
print("\n2. Simulating Feishu webhook message...")

# Create a test message with unique ID
test_msg_id = f"test_msg_{int(time.time())}"
test_chat_id = "test_chat_e2e"
test_content = f"E2E Test Message {datetime.now().strftime('%H:%M:%S')}"

webhook_payload = {
    "schema": "2.0",
    "header": {
        "event_id": test_msg_id,
        "event_type": "im.message.receive_v1",
        "create_time": str(int(time.time() * 1000)),
        "token": "test_token",
        "app_id": "cli_test",
        "tenant_key": "test_tenant"
    },
    "event": {
        "sender": {
            "sender_id": {
                "user_id": "test_user_123"
            },
            "sender_type": "user"
        },
        "message": {
            "message_id": test_msg_id,
            "root_id": "",
            "parent_id": "",
            "create_time": str(int(time.time() * 1000)),
            "chat_id": test_chat_id,
            "message_type": "text",
            "content": json.dumps({"text": test_content}),
            "mentions": []
        }
    }
}

print(f"   Message ID: {test_msg_id}")
print(f"   Content: {test_content}")

try:
    resp = requests.post(
        f"{BASE_URL}/api/feishu/webhook",
        json=webhook_payload,
        timeout=5
    )
    
    print(f"   Response status: {resp.status_code}")
    
    if resp.status_code == 200:
        print(f"   [OK] Webhook accepted the message")
    else:
        print(f"   [FAIL] Webhook returned error: {resp.text}")
        
except Exception as e:
    print(f"   [FAIL] Request failed: {e}")
    exit(1)

# Step 3: Check if message was saved to database
print("\n3. Checking if message was saved...")
time.sleep(1)  # Wait for async processing

try:
    import sys
    from pathlib import Path
    backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
    sys.path.insert(0, str(backend_dir))
    
    from database.session import get_db_sync
    from database.models import FeishuChatMessage
    
    db = get_db_sync()
    msg = db.query(FeishuChatMessage).filter(
        FeishuChatMessage.message_id == test_msg_id
    ).first()
    
    if msg:
        print(f"   [OK] Message saved to database")
        print(f"   Content: {msg.content}")
    else:
        print(f"   [FAIL] Message not found in database")
    
    db.close()
    
except Exception as e:
    print(f"   [FAIL] Database check failed: {e}")

# Step 4: Check if broadcast was sent
print("\n4. Checking broadcast...")
print("   Check frontend browser console (F12) for:")
print("   - 'Feishu chat message received: ...'")
print("   - '[BotChatTab] Feishu message received: ...'")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
print("\nIf frontend console shows the messages above,")
print("then WebSocket broadcast is working correctly.")
print("\nIf not, check:")
print("1. Backend logs for '[WEBSOCKET]' messages")
print("2. Frontend WebSocket connection status")
print("=" * 60 + "\n")
