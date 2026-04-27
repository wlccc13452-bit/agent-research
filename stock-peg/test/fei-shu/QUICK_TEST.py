"""
Quick verification test - Run after backend is started
"""
import asyncio
import websockets
import json
import requests
from datetime import datetime

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8000/api/feishu/test", timeout=2)
        return response.status_code == 200
    except:
        return False

async def test_broadcast():
    """Test WebSocket broadcast"""
    if not check_backend():
        print("[ERROR] Backend is not running!")
        print("\nPlease start backend first:")
        print("  cd d:\\play-ground\\股票研究\\stock-peg\\backend")
        print("  .venv\\Scripts\\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return

    print("=" * 70)
    print("WEBSOCKET BROADCAST VERIFICATION")
    print("=" * 70)

    uri = "ws://localhost:8000/ws"
    received = []

    try:
        async with websockets.connect(uri) as websocket:
            print("\n[OK] WebSocket connected")

            # Check WebSocket status
            response = requests.get("http://localhost:8000/api/feishu/websocket-status")
            print(f"[OK] Active connections: {response.json()['active_connections']}\n")

            # Send test webhook
            webhook_payload = {
                "schema_version": "2.0",
                "header": {
                    "event_id": "quick_test",
                    "event_type": "im.message.receive_v1",
                    "create_time": str(int(datetime.now().timestamp() * 1000)),
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
                        "message_id": "test_msg_quick",
                        "create_time": str(int(datetime.now().timestamp() * 1000)),
                        "chat_id": "oc_quick_test",
                        "message_type": "text",
                        "content": json.dumps({"text": "查询 000001"})
                    }
                }
            }

            print("[TEST] Sending webhook...")
            response = requests.post(
                "http://localhost:8000/api/feishu/webhook",
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"[TEST] Webhook response: {response.status_code}\n")

            # Listen for messages
            print("[LISTEN] Waiting for broadcast (5 seconds)...")
            for i in range(10):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "feishu-chat-message":
                        received.append(data)
                        print(f"\n[SUCCESS] Broadcast received!")
                        print(f"  Sender: {data['data']['sender_type']}")
                        print(f"  Content: {data['data']['content']}")
                        print(f"  Chat ID: {data['data']['chat_id']}\n")
                    elif msg_type != "pong":
                        print(f"  [{i}] {msg_type}")

                except asyncio.TimeoutError:
                    continue

    except Exception as e:
        print(f"\n[ERROR] {e}")

    print("=" * 70)
    if received:
        print("[PASS] Fix verified! WebSocket broadcast is working.")
        print("\nNext: Test from Feishu mobile app")
    else:
        print("[FAIL] No broadcast received")
        print("\nPossible issues:")
        print("  1. Backend code not reloaded - restart backend")
        print("  2. Exception in process_message_event - check logs")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_broadcast())
