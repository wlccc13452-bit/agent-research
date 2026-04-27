"""
Complete automated test for Feishu message flow
Tests the entire pipeline from backend startup to frontend display
"""
import sys
import json
import time
import asyncio
import requests
import websockets
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

received_messages = []


async def test_websocket_broadcast():
    """Test WebSocket broadcast functionality"""
    global received_messages
    
    print("\n" + "="*60)
    print("Feishu Message Flow - Complete Verification")
    print("="*60)
    
    # Step 1: Check backend health
    print("\n[Step 1] Checking backend health...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=3)
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print("  [FAIL] Backend not healthy")
            return False
        print("  [OK] Backend is healthy")
    except Exception as e:
        print(f"  [FAIL] Backend not responding: {e}")
        return False
    
    # Step 2: Check WebSocket connections
    print("\n[Step 2] Checking WebSocket connections...")
    try:
        resp = requests.get(f"{BASE_URL}/api/feishu/websocket-status", timeout=3)
        data = resp.json()
        connections = data.get('active_connections', 0)
        print(f"  Active connections: {connections}")
    except Exception as e:
        print(f"  [WARN] Could not check WebSocket status: {e}")
    
    # Step 3: Connect WebSocket and listen
    print("\n[Step 3] Connecting to WebSocket...")
    
    async def ws_listener():
        async with websockets.connect(WS_URL) as ws:
            print("  [OK] WebSocket connected")
            
            # Send ping to verify connection
            await ws.send(json.dumps({"action": "ping"}))
            
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1)
                    data = json.loads(msg)
                    msg_type = data.get('type', 'unknown')
                    
                    if msg_type in ['feishu-chat-message', 'feishu_chat_message']:
                        received_messages.append(data)
                        print(f"\n  [WS] ★ Received feishu-chat-message!")
                        print(f"       Sender: {data.get('data', {}).get('sender_type')}")
                        print(f"       Content: {data.get('data', {}).get('content', '')[:50]}...")
                    elif msg_type == 'pong':
                        pass  # Ignore pong
                    else:
                        print(f"  [WS] Received: {msg_type}")
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"  [WS] Error: {e}")
                    break
    
    ws_task = asyncio.create_task(ws_listener())
    
    # Wait for connection
    await asyncio.sleep(2)
    
    # Step 4: Test direct broadcast
    print("\n[Step 4] Testing direct broadcast...")
    try:
        resp = requests.post(f"{BASE_URL}/api/feishu/test-broadcast", timeout=5)
        data = resp.json()
        print(f"  Response: {data}")
        print(f"  Connections reached: {data.get('active_connections', 0)}")
    except Exception as e:
        print(f"  [FAIL] Direct broadcast failed: {e}")
    
    # Wait for message
    await asyncio.sleep(2)
    
    # Step 5: Test webhook simulation
    print("\n[Step 5] Testing webhook message simulation...")
    
    test_msg_id = f"verify_{int(time.time())}"
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
                "sender_id": {"user_id": "verify_user"},
                "sender_type": "user"
            },
            "message": {
                "message_id": test_msg_id,
                "root_id": "",
                "parent_id": "",
                "create_time": str(int(time.time() * 1000)),
                "chat_id": "verify_chat",
                "message_type": "text",
                "content": json.dumps({"text": f"Verification test {datetime.now().strftime('%H:%M:%S')}"}),
                "mentions": []
            }
        }
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/feishu/webhook",
            json=webhook_payload,
            timeout=5
        )
        print(f"  Response: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"  [FAIL] Webhook failed: {e}")
    
    # Wait for broadcast
    await asyncio.sleep(3)
    
    # Step 6: Check database
    print("\n[Step 6] Checking database...")
    try:
        from database.session import get_db_sync
        from database.models import FeishuChatMessage
        
        db = get_db_sync()
        msg = db.query(FeishuChatMessage).filter(
            FeishuChatMessage.message_id == test_msg_id
        ).first()
        
        if msg:
            print(f"  [OK] Message found in database")
            print(f"       Content: {msg.content}")
        else:
            print(f"  [FAIL] Message not found in database")
        
        db.close()
    except Exception as e:
        print(f"  [FAIL] Database check failed: {e}")
    
    # Step 7: Check API endpoint
    print("\n[Step 7] Checking API endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/api/feishu-chat/recent?limit=5", timeout=5)
        messages = resp.json()
        print(f"  [OK] API returned {len(messages)} messages")
        
        # Check if our test message is in the list
        found = any(m.get('message_id') == test_msg_id for m in messages)
        if found:
            print(f"  [OK] Test message is in recent messages")
        else:
            print(f"  [WARN] Test message not in recent messages")
    except Exception as e:
        print(f"  [FAIL] API check failed: {e}")
    
    # Cancel WebSocket task
    ws_task.cancel()
    try:
        await ws_task
    except asyncio.CancelledError:
        pass
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    print(f"\nWebSocket messages received: {len(received_messages)}")
    
    if received_messages:
        print("\n[SUCCESS] WebSocket broadcast is working!")
        print("\nIf frontend doesn't show messages, check:")
        print("  1. Browser console (F12) for errors")
        print("  2. BotChatTab component is mounted")
        print("  3. React Query is refreshing")
        print("\nTo debug frontend, paste this in browser console:")
        print("  window.addEventListener('feishu-chat-message-received', e => console.log('MSG:', e.detail))")
    else:
        print("\n[FAIL] No WebSocket messages received!")
        print("\nPossible issues:")
        print("  1. Long connection service not running")
        print("  2. Event loop not properly set")
        print("  3. WebSocket connection problem")
        print("\nCheck backend logs for '[LONG_CONN]' and '[WEBSOCKET]' messages")
    
    print("\n" + "="*60 + "\n")
    
    return len(received_messages) > 0


async def check_long_connection_service():
    """Check if long connection service is running"""
    print("\n" + "="*60)
    print("Long Connection Service Status")
    print("="*60)
    
    try:
        from services.feishu_long_connection_service import feishu_long_connection_service
        
        print(f"\n  Enabled: {feishu_long_connection_service.enabled}")
        print(f"  Running: {feishu_long_connection_service._running}")
        print(f"  Loop set: {feishu_long_connection_service._loop is not None}")
        print(f"  Thread alive: {feishu_long_connection_service._thread is not None and feishu_long_connection_service._thread.is_alive()}")
        
        if feishu_long_connection_service.enabled:
            if feishu_long_connection_service._running:
                print("\n  [OK] Long connection service is running")
            else:
                print("\n  [WARN] Long connection service is enabled but not running")
                print("  This means real Feishu messages won't be processed via long connection")
                print("  Only webhook messages will work")
        else:
            print("\n  [WARN] Long connection service is not enabled")
            print("  Check FEISHU_APP_ID and FEISHU_APP_SECRET in .env")
        
    except Exception as e:
        print(f"\n  [ERROR] Failed to check service: {e}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # Check service status
    asyncio.run(check_long_connection_service())
    
    # Run full test
    asyncio.run(test_websocket_broadcast())
