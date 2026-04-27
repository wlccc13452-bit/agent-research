"""
Improved test with proper WebSocket timing
"""
import json
import time
import asyncio
import requests
import websockets
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

ws_received = []

async def test():
    global ws_received
    
    print("\n" + "="*60)
    print("WebSocket Broadcast Test (Improved)")
    print("="*60)
    
    # 1. Connect WebSocket and wait for connection
    print("\n[1] Connecting WebSocket...")
    async with websockets.connect(WS_URL) as ws:
        print("[WS] Connected!")
        
        # Send ping to verify connection
        await ws.send(json.dumps({"action": "ping"}))
        
        # Start a receiver task
        async def receiver():
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1)
                    data = json.loads(msg)
                    msg_type = data.get('type', '')
                    print(f"[WS] <<< {msg_type}")
                    if 'feishu' in msg_type.lower():
                        ws_received.append(data)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"[WS] Receiver error: {e}")
                    break
        
        recv_task = asyncio.create_task(receiver())
        
        # Wait for pong to confirm connection is ready
        await asyncio.sleep(2)
        
        # 2. Test direct broadcast first
        print("\n[2] Testing direct broadcast...")
        resp = requests.post(f"{BASE_URL}/api/feishu/test-broadcast")
        print(f"    Status: {resp.json()}")
        
        # Wait for message
        await asyncio.sleep(2)
        
        # 3. Send webhook
        print("\n[3] Sending webhook...")
        test_id = f"ws_test_{int(time.time())}"
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
                "sender": {"sender_id": {"user_id": "ws_user"}, "sender_type": "user"},
                "message": {
                    "message_id": test_id,
                    "chat_id": "ws_chat",
                    "message_type": "text",
                    "content": json.dumps({"text": f"WS Test {datetime.now().strftime('%H:%M:%S')}"}),
                    "create_time": str(int(time.time() * 1000)),
                }
            }
        }
        
        resp = requests.post(f"{BASE_URL}/api/feishu/webhook", json=payload)
        print(f"    Status: {resp.status_code}")
        
        # Wait for broadcast
        print("\n[4] Waiting for broadcast (5s)...")
        await asyncio.sleep(5)
        
        # Cancel receiver
        recv_task.cancel()
        try:
            await recv_task
        except:
            pass
    
    # 5. Check database
    print("\n[5] Checking database...")
    resp = requests.get(f"{BASE_URL}/api/feishu-chat/recent?limit=5")
    msgs = resp.json()
    db_found = any(m.get('message_id') == test_id for m in msgs)
    print(f"    Message in DB: {db_found}")
    
    # Summary
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    print(f"  WebSocket messages received: {len(ws_received)}")
    for m in ws_received:
        print(f"    - {m.get('type')}: {str(m.get('data', {}).get('content', ''))[:30]}")
    print(f"  Database: {'SAVED' if db_found else 'NOT FOUND'}")
    
    if ws_received:
        print("\n  [SUCCESS] WebSocket broadcast is working!")
    else:
        print("\n  [FAIL] No WebSocket messages received")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test())
