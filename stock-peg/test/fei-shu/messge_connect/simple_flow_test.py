"""
Simple flow test - API only, no database imports
"""
import json
import time
import asyncio
import requests
import websockets
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

received = []

async def test():
    print("\n" + "="*60)
    print("Simple Flow Test")
    print("="*60)
    
    # 1. WebSocket listener
    async def ws_listener():
        async with websockets.connect(WS_URL) as ws:
            print("[WS] Connected")
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1)
                    data = json.loads(msg)
                    if 'feishu' in data.get('type', ''):
                        received.append(data)
                        print(f"[WS] >>> Received: {data.get('type')}")
                except asyncio.TimeoutError:
                    continue
                except:
                    break
    
    ws_task = asyncio.create_task(ws_listener())
    await asyncio.sleep(2)
    
    # 2. Send webhook
    test_id = f"simple_{int(time.time())}"
    payload = {
        "schema": "2.0",
        "header": {
            "event_id": test_id,
            "event_type": "im.message.receive_v1",
            "create_time": str(int(time.time() * 1000)),
            "token": "test",
            "app_id": "cli_test",
            "tenant_key": "test"
        },
        "event": {
            "sender": {"sender_id": {"user_id": "user"}, "sender_type": "user"},
            "message": {
                "message_id": test_id,
                "chat_id": "chat",
                "message_type": "text",
                "content": json.dumps({"text": f"Test {datetime.now().strftime('%H:%M:%S')}"}),
                "create_time": str(int(time.time() * 1000)),
            }
        }
    }
    
    print(f"\n[Webhook] Sending...")
    resp = requests.post(f"{BASE_URL}/api/feishu/webhook", json=payload)
    print(f"[Webhook] Status: {resp.status_code}")
    
    await asyncio.sleep(3)
    
    ws_task.cancel()
    
    # 3. Check API
    resp = requests.get(f"{BASE_URL}/api/feishu-chat/recent?limit=5")
    msgs = resp.json()
    found = any(m.get('message_id') == test_id for m in msgs)
    
    print(f"\n[API] Found in recent: {found}")
    
    # Summary
    print("\n" + "="*60)
    print(f"WebSocket: {len(received)} messages")
    print(f"Database: {'SAVED' if found else 'NOT FOUND'}")
    
    if len(received) > 0 and found:
        print("\n[OK] Backend flow works correctly!")
        print("If frontend doesn't update, issue is in frontend.")
    else:
        print("\n[FAIL] Backend has issues")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test())
