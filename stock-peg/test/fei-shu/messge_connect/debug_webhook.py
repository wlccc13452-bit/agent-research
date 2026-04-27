import requests
import json

# 直接调用webhook并查看响应
payload = {
    "schema": "2.0",
    "header": {
        "event_id": "debug_test",
        "event_type": "im.message.receive_v1",
        "create_time": "1000000",
        "token": "test",
        "app_id": "cli_test",
        "tenant_key": "test"
    },
    "event": {
        "sender": {"sender_id": {"user_id": "debug_user"}, "sender_type": "user"},
        "message": {
            "message_id": "debug_msg_123",
            "chat_id": "debug_chat",
            "message_type": "text",
            "content": json.dumps({"text": "Debug message"}),
            "create_time": "1000000",
        }
    }
}

print("Sending webhook...")
resp = requests.post("http://localhost:8000/api/feishu/webhook", json=payload, timeout=10)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")

# 检查消息是否保存
print("\nChecking recent messages...")
resp = requests.get("http://localhost:8000/api/feishu-chat/recent?limit=3")
msgs = resp.json()
print(f"Found {len(msgs)} messages")
for m in msgs:
    print(f"  - {m.get('message_id')}: {m.get('content', '')[:30]}")
