# -*- coding: utf-8 -*-
"""Check long connection service status via API"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("Long Connection Service Status Check")
print("="*60)

# Check WebSocket status
print("\n1. WebSocket Status:")
try:
    resp = requests.get(f"{BASE_URL}/api/feishu/websocket-status", timeout=3)
    print(f"   {resp.json()}")
except Exception as e:
    print(f"   Error: {e}")

# Test direct broadcast
print("\n2. Direct Broadcast Test:")
try:
    resp = requests.post(f"{BASE_URL}/api/feishu/test-broadcast", timeout=5)
    data = resp.json()
    print(f"   Status: {data.get('status')}")
    print(f"   Active connections: {data.get('active_connections')}")
except Exception as e:
    print(f"   Error: {e}")

# Simulate webhook and check if broadcast works
print("\n3. Webhook + Database Test:")
import time
test_msg_id = f"check_{int(time.time())}"
webhook_payload = {
    "schema": "2.0",
    "header": {
        "event_id": test_msg_id,
        "event_type": "im.message.receive_v1",
        "create_time": str(int(time.time() * 1000)),
        "token": "test",
        "app_id": "cli_test",
        "tenant_key": "test"
    },
    "event": {
        "sender": {"sender_id": {"user_id": "check_user"}, "sender_type": "user"},
        "message": {
            "message_id": test_msg_id,
            "chat_id": "check_chat",
            "message_type": "text",
            "content": json.dumps({"text": "Check message"}),
            "create_time": str(int(time.time() * 1000)),
        }
    }
}

try:
    resp = requests.post(f"{BASE_URL}/api/feishu/webhook", json=webhook_payload, timeout=5)
    print(f"   Webhook response: {resp.status_code}")
    
    # Check database
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
    db.close()
    
    if msg:
        print(f"   [OK] Message saved to database: {msg.content}")
    else:
        print(f"   [FAIL] Message not in database")
        
except Exception as e:
    print(f"   Error: {e}")

# Check recent messages API
print("\n4. Recent Messages API:")
try:
    resp = requests.get(f"{BASE_URL}/api/feishu-chat/recent?limit=3", timeout=5)
    messages = resp.json()
    print(f"   Found {len(messages)} messages")
    for m in messages[:3]:
        print(f"   - [{m.get('sender_type')}] {m.get('content', '')[:40]}...")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*60)
print("Diagnosis:")
print("="*60)

print("""
If webhook test passes but real Feishu messages don't show:

1. Long connection service may not be running
   - Check backend logs for "飞书长连接服务" messages
   - Service should show "已启动并正在运行"

2. If service shows "启动失败":
   - Check FEISHU_APP_ID and FEISHU_APP_SECRET in .env
   - Check if lark_oapi SDK is installed: pip install lark-oapi

3. If service shows "已启动" but frontend doesn't update:
   - Check browser console for WebSocket errors
   - Verify frontend is connected (green dot in BotChatTab)
""")
print("="*60 + "\n")
