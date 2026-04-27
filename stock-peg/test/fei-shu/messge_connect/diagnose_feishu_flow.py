"""
Diagnostic tool for Feishu message flow
Tests the complete flow from webhook to frontend display
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

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_ok(text):
    print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} {text}")

def print_fail(text):
    print(f"{Colors.FAIL}[FAIL]{Colors.ENDC} {text}")

def print_info(text):
    print(f"{Colors.OKCYAN}[INFO]{Colors.ENDC} {text}")

def print_warn(text):
    print(f"{Colors.WARNING}[WARN]{Colors.ENDC} {text}")


def test_backend_health():
    """Test if backend is running"""
    print_header("Step 1: Backend Health Check")
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=3)
        if resp.status_code == 200:
            print_ok(f"Backend is running: {resp.json()}")
            return True
        else:
            print_fail(f"Backend returned {resp.status_code}")
            return False
    except Exception as e:
        print_fail(f"Backend not responding: {e}")
        return False


def test_websocket_connections():
    """Test WebSocket connection count"""
    print_header("Step 2: WebSocket Connection Check")
    try:
        resp = requests.get(f"{BASE_URL}/api/feishu/websocket-status", timeout=3)
        data = resp.json()
        connections = data.get('active_connections', 0)
        if connections > 0:
            print_ok(f"Active WebSocket connections: {connections}")
            return True, connections
        else:
            print_fail("No WebSocket connections!")
            print_info("Make sure frontend is running (http://localhost:5173)")
            return False, 0
    except Exception as e:
        print_fail(f"Failed to check WebSocket status: {e}")
        return False, 0


def test_database_messages():
    """Check recent messages in database"""
    print_header("Step 3: Database Message Check")
    try:
        from database.session import get_db_sync
        from database.models import FeishuChatMessage
        from datetime import datetime, timedelta
        
        db = get_db_sync()
        
        # Get recent messages
        recent_time = datetime.now() - timedelta(minutes=30)
        messages = db.query(FeishuChatMessage).filter(
            FeishuChatMessage.send_time >= recent_time
        ).order_by(FeishuChatMessage.send_time.desc()).limit(10).all()
        
        if messages:
            print_ok(f"Found {len(messages)} recent messages (last 30 min)")
            for msg in messages[:5]:
                print(f"  - [{msg.send_time.strftime('%H:%M:%S')}] {msg.sender_type}: {msg.content[:40]}...")
            return True, len(messages)
        else:
            print_warn("No recent messages in database")
            return True, 0
        
        db.close()
    except Exception as e:
        print_fail(f"Failed to check database: {e}")
        return False, 0


async def test_websocket_receive():
    """Test receiving WebSocket messages"""
    print_header("Step 4: WebSocket Message Reception Test")
    
    received_messages = []
    
    async def on_message(ws, message):
        try:
            data = json.loads(message)
            received_messages.append(data)
            print_info(f"Received: type={data.get('type')}")
        except:
            pass
    
    try:
        print_info("Connecting to WebSocket...")
        async with websockets.connect(WS_URL) as ws:
            print_ok("WebSocket connected")
            
            # Trigger a test broadcast
            print_info("Triggering test broadcast...")
            resp = requests.post(f"{BASE_URL}/api/feishu/test-broadcast", timeout=5)
            print_info(f"Broadcast response: {resp.json()}")
            
            # Wait for messages
            print_info("Waiting for messages (5 seconds)...")
            start = time.time()
            while time.time() - start < 5:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=1)
                    data = json.loads(message)
                    received_messages.append(data)
                    print_ok(f"Received message: type={data.get('type')}")
                except asyncio.TimeoutError:
                    continue
            
            if any(m.get('type') in ['feishu-chat-message', 'feishu_chat_message'] for m in received_messages):
                print_ok("Successfully received feishu-chat-message!")
                return True
            else:
                print_warn(f"No feishu-chat-message received. Got: {[m.get('type') for m in received_messages]}")
                return False
                
    except Exception as e:
        print_fail(f"WebSocket test failed: {e}")
        return False


def test_simulated_webhook():
    """Simulate a complete webhook flow"""
    print_header("Step 5: Simulated Webhook Test")
    
    test_msg_id = f"diag_{int(time.time())}"
    test_content = f"Diagnostic test {datetime.now().strftime('%H:%M:%S')}"
    
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
                "sender_id": {"user_id": "diag_user"},
                "sender_type": "user"
            },
            "message": {
                "message_id": test_msg_id,
                "root_id": "",
                "parent_id": "",
                "create_time": str(int(time.time() * 1000)),
                "chat_id": "diag_chat",
                "message_type": "text",
                "content": json.dumps({"text": test_content}),
                "mentions": []
            }
        }
    }
    
    print_info(f"Sending webhook with message_id: {test_msg_id}")
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/feishu/webhook",
            json=webhook_payload,
            timeout=5
        )
        
        if resp.status_code == 200:
            print_ok(f"Webhook accepted: {resp.json()}")
            
            # Wait and check database
            time.sleep(1)
            from database.session import get_db_sync
            from database.models import FeishuChatMessage
            
            db = get_db_sync()
            msg = db.query(FeishuChatMessage).filter(
                FeishuChatMessage.message_id == test_msg_id
            ).first()
            
            if msg:
                print_ok(f"Message saved to database: {msg.content}")
                db.close()
                return True, test_msg_id
            else:
                print_fail("Message NOT found in database")
                db.close()
                return False, None
        else:
            print_fail(f"Webhook failed: {resp.status_code} - {resp.text}")
            return False, None
            
    except Exception as e:
        print_fail(f"Webhook test failed: {e}")
        return False, None


def test_api_recent_messages():
    """Test the API endpoint for recent messages"""
    print_header("Step 6: API Recent Messages Test")
    
    try:
        resp = requests.get(f"{BASE_URL}/api/feishu-chat/recent?limit=5", timeout=5)
        
        if resp.status_code == 200:
            messages = resp.json()
            if messages:
                print_ok(f"API returned {len(messages)} messages")
                for msg in messages[:3]:
                    print(f"  - [{msg.get('sender_type')}] {msg.get('content', '')[:40]}...")
                return True
            else:
                print_warn("API returned empty array")
                return True
        else:
            print_fail(f"API failed: {resp.status_code}")
            return False
            
    except Exception as e:
        print_fail(f"API test failed: {e}")
        return False


def run_diagnosis():
    """Run all diagnostic tests"""
    print_header("Feishu Message Flow Diagnostic Tool")
    print_info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test 1: Backend health
    results['backend'] = test_backend_health()
    
    # Test 2: WebSocket connections
    ws_ok, ws_count = test_websocket_connections()
    results['websocket'] = ws_ok
    
    # Test 3: Database messages
    db_ok, msg_count = test_database_messages()
    results['database'] = db_ok
    
    # Test 4: WebSocket reception
    results['ws_receive'] = asyncio.run(test_websocket_receive())
    
    # Test 5: Simulated webhook
    wh_ok, msg_id = test_simulated_webhook()
    results['webhook'] = wh_ok
    
    # Test 6: API recent messages
    results['api'] = test_api_recent_messages()
    
    # Summary
    print_header("Diagnostic Summary")
    
    for test, passed in results.items():
        status = f"{Colors.OKGREEN}PASS{Colors.ENDC}" if passed else f"{Colors.FAIL}FAIL{Colors.ENDC}"
        print(f"  {test:15s}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print_ok("All tests passed!")
        print_info("If frontend still doesn't show messages, check:")
        print("  1. Browser console (F12) for errors")
        print("  2. BotChatTab component is mounted")
        print("  3. React Query is fetching data")
    else:
        print_fail("Some tests failed. Check the issues above.")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    run_diagnosis()
