# -*- coding: utf-8 -*-
"""
Complete Feishu Message Flow Test Suite
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

results = {}
received_messages = []


def print_header(text):
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)


def print_result(test_name, passed, message=""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"  {status} {test_name}")
    if message:
        print(f"         {message}")
    results[test_name] = passed


async def run_tests():
    global received_messages
    
    print_header("Feishu Message Flow - Complete Test Suite")
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Backend Health
    print_header("Test 1: Backend Health")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=3)
        print_result("backend_health", resp.status_code == 200, f"Status: {resp.status_code}")
    except Exception as e:
        print_result("backend_health", False, str(e))
        print("\n[ABORT] Backend not running.")
        return
    
    # Test 2: Long Connection Service
    print_header("Test 2: Long Connection Service")
    try:
        from services.feishu_long_connection_service import feishu_long_connection_service
        
        enabled = feishu_long_connection_service.enabled
        running = feishu_long_connection_service._running
        loop_set = feishu_long_connection_service._loop is not None
        
        print(f"  Enabled: {enabled}")
        print(f"  Running: {running}")
        print(f"  Loop set: {loop_set}")
        
        passed = enabled and running and loop_set
        msg = "OK - Service running" if passed else "FAIL - Service NOT running"
        print_result("long_conn_service", passed, msg)
    except Exception as e:
        print_result("long_conn_service", False, str(e))
    
    # Test 3: WebSocket Connection
    print_header("Test 3: WebSocket Connection")
    
    async def ws_listener():
        async with websockets.connect(WS_URL) as ws:
            print("  WebSocket connected")
            await ws.send(json.dumps({"action": "ping"}))
            
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1)
                    data = json.loads(msg)
                    if data.get('type') in ['feishu-chat-message', 'feishu_chat_message']:
                        received_messages.append(data)
                        print(f"\n  [WS] Received feishu-chat-message!")
                    elif data.get('type') == 'pong':
                        print_result("websocket_connection", True, "Ping/pong works")
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break
    
    ws_task = asyncio.create_task(ws_listener())
    await asyncio.sleep(2)
    
    # Test 4: Direct Broadcast
    print_header("Test 4: Direct Broadcast")
    try:
        resp = requests.post(f"{BASE_URL}/api/feishu/test-broadcast", timeout=5)
        data = resp.json()
        connections = data.get('active_connections', 0)
        print(f"  Sent to {connections} connections")
        await asyncio.sleep(2)
        
        passed = len(received_messages) > 0
        msg = f"Received {len(received_messages)} messages" if passed else "No messages received"
        print_result("direct_broadcast", passed, msg)
    except Exception as e:
        print_result("direct_broadcast", False, str(e))
    
    # Test 5: Webhook Simulation
    print_header("Test 5: Webhook Simulation")
    
    test_msg_id = f"test_{int(time.time())}"
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
            "sender": {"sender_id": {"user_id": "test"}, "sender_type": "user"},
            "message": {
                "message_id": test_msg_id,
                "chat_id": "test_chat",
                "message_type": "text",
                "content": json.dumps({"text": f"Test {datetime.now().strftime('%H:%M:%S')}"}),
                "create_time": str(int(time.time() * 1000)),
            }
        }
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/api/feishu/webhook", json=webhook_payload, timeout=5)
        print(f"  Response: {resp.status_code}")
        await asyncio.sleep(3)
        
        passed = len(received_messages) > 0
        msg = f"Total messages: {len(received_messages)}" if passed else "No broadcast received"
        print_result("webhook_broadcast", passed, msg)
    except Exception as e:
        print_result("webhook_broadcast", False, str(e))
    
    # Cancel WebSocket task
    ws_task.cancel()
    try:
        await ws_task
    except asyncio.CancelledError:
        pass
    
    # Test 6: Database Save
    print_header("Test 6: Database Save")
    try:
        from database.session import get_db_sync
        from database.models import FeishuChatMessage
        
        db = get_db_sync()
        msg = db.query(FeishuChatMessage).filter(
            FeishuChatMessage.message_id == test_msg_id
        ).first()
        db.close()
        
        print_result("database_save", msg is not None, msg.content[:50] if msg else "Not found")
    except Exception as e:
        print_result("database_save", False, str(e))
    
    # Test 7: API Endpoint
    print_header("Test 7: API Endpoint")
    try:
        resp = requests.get(f"{BASE_URL}/api/feishu-chat/recent?limit=5", timeout=5)
        messages = resp.json()
        print_result("api_endpoint", resp.status_code == 200, f"Returned {len(messages)} messages")
    except Exception as e:
        print_result("api_endpoint", False, str(e))
    
    # Summary
    print_header("Summary")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for test, passed in results.items():
        status = "[OK]" if passed else "[X]"
        print(f"  {status} {test}")
    
    print(f"\n  Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n  SUCCESS! All tests passed.")
    else:
        print("\n  Some tests failed. Check errors above.")
    
    print("="*60 + "\n")
    
    return passed_count == total_count


if __name__ == "__main__":
    asyncio.run(run_tests())
