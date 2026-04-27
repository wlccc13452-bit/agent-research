"""
Monitor Feishu messages in real-time
Run this script and send messages from Feishu app to test
"""
import asyncio
import websockets
import json
from datetime import datetime

async def monitor_feishu_messages():
    """Monitor WebSocket for Feishu messages"""
    uri = "ws://localhost:8000/ws"
    
    print("=" * 70)
    print("FEISHU MESSAGE MONITOR")
    print("=" * 70)
    print("\nListening for Feishu messages...")
    print("Send a message from Feishu app to test the integration.\n")
    print("Press Ctrl+C to stop.\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            message_count = 0
            
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "feishu-chat-message":
                        message_count += 1
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        print(f"\n[{timestamp}] Message #{message_count}")
                        print("=" * 70)
                        
                        msg_data = data.get("data", {})
                        print(f"  Sender:   {msg_data.get('sender_type', 'unknown')}")
                        print(f"  Sender ID: {msg_data.get('sender_id', 'N/A')}")
                        print(f"  Chat ID:  {msg_data.get('chat_id', 'N/A')}")
                        print(f"  Content:  {msg_data.get('content', 'N/A')}")
                        print(f"  Time:     {msg_data.get('send_time', 'N/A')}")
                        print("=" * 70)
                        
                    elif msg_type != "pong":
                        # Log other message types (not pong)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg_type}")
                        
                except Exception as e:
                    print(f"[ERROR] {e}")
                    continue
                    
    except KeyboardInterrupt:
        print("\n\nMonitor stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(monitor_feishu_messages())
