"""
Complete diagnostic for Feishu Bot WebSocket broadcast
"""
import asyncio
import websockets
import json
import requests
import time
from datetime import datetime

class BroadcastDiagnostic:
    def __init__(self):
        self.results = {}
        
    def log(self, category, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{status}] [{category}] {message}")
        
    async def run_all_tests(self):
        """Run all diagnostic tests"""
        print("=" * 70)
        print("FEISHU BOT WEBSOCKET BROADCAST DIAGNOSTIC")
        print("=" * 70)
        
        # Test 1: Check backend is running
        print("\n[TEST 1] Backend Health Check")
        try:
            response = requests.get("http://localhost:8000/api/feishu/test", timeout=2)
            if response.status_code == 200:
                self.log("BACKEND", "Backend is running", "PASS")
                self.results["backend_running"] = True
            else:
                self.log("BACKEND", f"Backend returned {response.status_code}", "FAIL")
                self.results["backend_running"] = False
                return
        except Exception as e:
            self.log("BACKEND", f"Cannot connect to backend: {e}", "FAIL")
            self.results["backend_running"] = False
            return
        
        # Test 2: Check WebSocket connections
        print("\n[TEST 2] WebSocket Connection Status")
        try:
            response = requests.get("http://localhost:8000/api/feishu/websocket-status")
            status = response.json()
            self.log("WEBSOCKET", f"Active connections: {status['active_connections']}", "INFO")
            self.log("WEBSOCKET", f"Stock subscriptions: {status['stock_subscriptions']}", "INFO")
            self.results["ws_connections"] = status['active_connections']
        except Exception as e:
            self.log("WEBSOCKET", f"Failed to get status: {e}", "FAIL")
            return
        
        # Test 3: Test manual broadcast
        print("\n[TEST 3] Manual Broadcast Test")
        try:
            # Start WebSocket listener
            ws_task = asyncio.create_task(self.listen_for_broadcast())
            await asyncio.sleep(1)  # Wait for WebSocket to connect
            
            # Trigger broadcast
            response = requests.post("http://localhost:8000/api/feishu/test-broadcast")
            result = response.json()
            self.log("BROADCAST", f"Manual broadcast result: {result['message']}", "INFO")
            
            # Wait for message
            await asyncio.wait_for(ws_task, timeout=5)
            
            if self.results.get("received_manual_broadcast"):
                self.log("BROADCAST", "Manual broadcast SUCCESS", "PASS")
            else:
                self.log("BROADCAST", "Manual broadcast FAILED - no message received", "FAIL")
                
        except asyncio.TimeoutError:
            self.log("BROADCAST", "Manual broadcast FAILED - timeout", "FAIL")
        except Exception as e:
            self.log("BROADCAST", f"Manual broadcast error: {e}", "FAIL")
        
        # Test 4: Test webhook broadcast
        print("\n[TEST 4] Webhook Broadcast Test")
        try:
            # Start WebSocket listener
            ws_task = asyncio.create_task(self.listen_for_webhook_broadcast())
            await asyncio.sleep(1)
            
            # Send webhook
            webhook_payload = {
                "schema_version": "2.0",
                "header": {
                    "event_id": f"diag_{int(time.time())}",
                    "event_type": "im.message.receive_v1",
                    "create_time": str(int(time.time() * 1000)),
                    "token": "diag",
                    "app_id": "diag",
                    "tenant_key": "diag"
                },
                "event": {
                    "sender": {
                        "sender_id": {"user_id": "diag_user", "open_id": "ou_diag"},
                        "sender_type": "user",
                        "tenant_key": "diag"
                    },
                    "message": {
                        "message_id": f"diag_msg_{int(time.time())}",
                        "create_time": str(int(time.time() * 1000)),
                        "chat_id": "oc_diag_chat",
                        "message_type": "text",
                        "content": json.dumps({"text": "查询 000001"})
                    }
                }
            }
            
            response = requests.post(
                "http://localhost:8000/api/feishu/webhook",
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            )
            self.log("WEBHOOK", f"Webhook response: {response.status_code}", "INFO")
            
            # Wait for message
            await asyncio.wait_for(ws_task, timeout=10)
            
            if self.results.get("received_webhook_broadcast"):
                self.log("WEBHOOK", "Webhook broadcast SUCCESS", "PASS")
            else:
                self.log("WEBHOOK", "Webhook broadcast FAILED - no message received", "FAIL")
                
        except asyncio.TimeoutError:
            self.log("WEBHOOK", "Webhook broadcast FAILED - timeout", "FAIL")
        except Exception as e:
            self.log("WEBHOOK", f"Webhook broadcast error: {e}", "FAIL")
        
        # Summary
        print("\n" + "=" * 70)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 70)
        print(f"Backend running: {'PASS' if self.results.get('backend_running') else 'FAIL'}")
        print(f"WebSocket connections: {self.results.get('ws_connections', 0)}")
        print(f"Manual broadcast: {'PASS' if self.results.get('received_manual_broadcast') else 'FAIL'}")
        print(f"Webhook broadcast: {'PASS' if self.results.get('received_webhook_broadcast') else 'FAIL'}")
        print("=" * 70)
        
        if not self.results.get("received_webhook_broadcast"):
            print("\nPOSSIBLE ISSUES:")
            print("1. process_message_event() is not being called")
            print("2. background_tasks.add_task() has issues with async functions")
            print("3. Exception is thrown before broadcast is called")
            print("4. Backend code needs to be restarted to pick up changes")
            print("\nRECOMMENDED ACTIONS:")
            print("1. Check backend console logs for [PROCESS] messages")
            print("2. Restart backend service to reload code changes")
            print("3. Add more logging to process_message_event()")
        
    async def listen_for_broadcast(self):
        """Listen for manual broadcast"""
        try:
            async with websockets.connect("ws://localhost:8000/ws") as websocket:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    if data.get("type") == "feishu-chat-message":
                        self.results["received_manual_broadcast"] = True
                        return
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            self.log("WS_LISTENER", f"Error: {e}", "ERROR")
    
    async def listen_for_webhook_broadcast(self):
        """Listen for webhook broadcast"""
        try:
            async with websockets.connect("ws://localhost:8000/ws") as websocket:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "feishu-chat-message":
                        self.log("WS_LISTENER", f"Received webhook broadcast!", "SUCCESS")
                        self.results["received_webhook_broadcast"] = True
                        return
                    elif msg_type != "pong":
                        self.log("WS_LISTENER", f"Received: {msg_type}", "INFO")
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            self.log("WS_LISTENER", f"Error: {e}", "ERROR")


if __name__ == "__main__":
    diagnostic = BroadcastDiagnostic()
    asyncio.run(diagnostic.run_all_tests())
