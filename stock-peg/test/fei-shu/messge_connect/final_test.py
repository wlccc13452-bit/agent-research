"""
Final verification test
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
test_msg_id = None

async def test():
    global ws_received, test_msg_id
    
    print("\n" + "="*60)
    print("Final Verification Test")
    print("="*60)
    
    # 1. Start WebSocket listener
    async def ws_listener():
        async with websockets.connect(WS_URL) as ws:
            print("[WS] Connected, waiting for messages...")
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1)
                    data = json.loads(msg)
                    msg_type = data.get('type', '')
                    print(f"[WS] Received: {msg_type}")
                    if 'feishu' in msg_type.lower():
                        ws_received.append(data)
                        print(f"[WS] >>> Feishu message content: {str(data.get('data', {}).get('content', ''))[:50]}")
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"[WS] Error: {e}")
                    break
    
    ws_task = asyncio.create_task(ws_listener())
    await asyncio.sleep(2)
    
    # 2. Send webhook
    test_msg_id = f"final_{int(time.time())}"
    payload = {
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
            "sender": {"sender_id": {"user_id": "final_user"}, "sender_type": "user"},
            "message": {
                "message_id": test_msg_id,
                "chat_id": "final_chat",
                "message_type": "text",
                "content": json.dumps({"text": f"Final Test {datetime.now().strftime('%H:%M:%S')}"}),
                "create_time": str(int(time.time() * 1000)),
            }
        }
    }
    
    print(f"\n[Webhook] Sending message ID: {test_msg_id}")
    resp = requests.post(f"{BASE_URL}/api/feishu/webhook", json=payload)
    print(f"[Webhook] Status: {resp.status_code}")
    
    # 3. Wait for processing
    print("\n[Processing] Waiting 5 seconds for broadcast...")
    await asyncio.sleep(5)
    
    # 4. Cancel WebSocket
    ws_task.cancel()
    try:
        await ws_task
    except:
        pass
    
    # 5. Verify database
    print("\n[API] Checking database...")
    resp = requests.get(f"{BASE_URL}/api/feishu-chat/recent?limit=5")
    msgs = resp.json()
    db_found = any(m.get('message_id') == test_msg_id for m in msgs)
    print(f"[API] Message in database: {db_found}")
    
    # Summary
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    print(f"  WebSocket broadcast: {len(ws_received)} messages received")
    print(f"  Database save: {'SUCCESS' if db_found else 'FAILED'}")
    
    if ws_received:
        print(f"\n  WebSocket message types: {[m.get('type') for m in ws_received]}")
    
    all_ok = len(ws_received) > 0 and db_found
    
    print("\n" + "-"*60)
    if all_ok:
        print("  [SUCCESS] Backend flow is working correctly!")
        print("\n  If frontend doesn't show messages, the issue is:")
        print("  1. Frontend WebSocket not connected (check green dot)")
        print("  2. Event listener not set up correctly")
        print("  3. React Query not refreshing")
        print("\n  To debug frontend:")
        print("  - Open browser console (F12)")
        print("  - Run: window.addEventListener('feishu-chat-message-received', e => console.log('MSG:', e.detail))")
        print("  - Send message from Feishu mobile app")
    else:
        print("  [FAILED] Issues detected:")
        if not ws_received:
            print("  - WebSocket broadcast not working")
        if not db_found:
            print("  - Database save not working")
    print("="*60 + "\n")
    
    return all_ok

if __name__ == "__main__":
    asyncio.run(test())
