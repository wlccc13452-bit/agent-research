"""
Complete flow test - verifies entire pipeline from webhook to frontend
"""
import sys
import json
import time
import asyncio
import requests
import websockets
from datetime import datetime
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Change to backend directory for proper imports
import os
os.chdir(backend_dir)

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

received = []

async def test_complete_flow():
    print("\n" + "="*60)
    print("Complete Flow Test - Webhook -> WebSocket -> Database")
    print("="*60)
    
    # Start WebSocket listener
    async def ws_listener():
        async with websockets.connect(WS_URL) as ws:
            print("[WS] Connected")
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1)
                    data = json.loads(msg)
                    msg_type = data.get('type', '')
                    if 'feishu' in msg_type:
                        received.append(data)
                        print(f"\n[WS] Received: {msg_type}")
                        print(f"     Content: {data.get('data', {}).get('content', '')[:50]}")
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break
    
    ws_task = asyncio.create_task(ws_listener())
    await asyncio.sleep(2)
    
    # Send webhook message
    test_id = f"flow_test_{int(time.time())}"
    test_content = f"Flow Test {datetime.now().strftime('%H:%M:%S')}"
    
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
            "sender": {"sender_id": {"user_id": "flow_user"}, "sender_type": "user"},
            "message": {
                "message_id": test_id,
                "chat_id": "flow_chat",
                "message_type": "text",
                "content": json.dumps({"text": test_content}),
                "create_time": str(int(time.time() * 1000)),
            }
        }
    }
    
    print(f"\n[Webhook] Sending test message...")
    resp = requests.post(f"{BASE_URL}/api/feishu/webhook", json=payload, timeout=5)
    print(f"[Webhook] Response: {resp.status_code}")
    
    # Wait for broadcast
    await asyncio.sleep(3)
    
    # Cancel WebSocket
    ws_task.cancel()
    try:
        await ws_task
    except asyncio.CancelledError:
        pass
    
    # Check database via API
    print("\n[Database/API] Checking...")
    resp = requests.get(f"{BASE_URL}/api/feishu-chat/recent?limit=10")
    api_messages = resp.json()
    
    msg_found = any(m.get('message_id') == test_id for m in api_messages)
    
    # Summary
    print("\n" + "="*60)
    print("Results:")
    print("="*60)
    
    print(f"  WebSocket received: {len(received)} messages")
    print(f"  Database saved: {'YES' if msg_found else 'NO'}")
    print(f"  API returns message: {'YES' if msg_found else 'NO'}")
    
    all_ok = len(received) > 0 and msg_found
    
    if all_ok:
        print("\n[SUCCESS] Complete flow is working!")
        print("\nIf frontend doesn't show messages:")
        print("  1. Open browser console (F12)")
        print("  2. Paste the content of: frontend_debug_console.js")
        print("  3. Send a message from Feishu app")
        print("  4. Check if '[WS消息]' appears in console")
    else:
        print("\n[FAIL] Flow has issues:")
        if len(received) == 0:
            print("  - WebSocket broadcast not working")
        if not msg_found:
            print("  - Database save not working")
    
    print("="*60 + "\n")
    
    return all_ok


if __name__ == "__main__":
    asyncio.run(test_complete_flow())
