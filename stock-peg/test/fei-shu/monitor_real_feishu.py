"""
Real-time Feishu message monitor
Run this and send message from Feishu mobile app to test
"""
import asyncio
import websockets
import json
from datetime import datetime

async def monitor():
    """Monitor WebSocket for real Feishu messages"""
    uri = "ws://localhost:8000/ws"

    print("=" * 70)
    print("FEISHU REAL-TIME MESSAGE MONITOR")
    print("=" * 70)
    print("\n📱 Send a message from Feishu mobile app now!")
    print("    Example: '查询 平安银行' or '行情 000001'\n")
    print("⏱️  Listening for messages (Press Ctrl+C to stop)...\n")

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

                        msg_data = data.get("data", {})
                        sender_type = msg_data.get("sender_type", "unknown")
                        content = msg_data.get("content", "")

                        print(f"\n{'='*70}")
                        print(f"[{timestamp}] 📨 MESSAGE #{message_count}")
                        print(f"{'='*70}")
                        print(f"  👤 Sender: {sender_type.upper()}")
                        print(f"  💬 Content: {content}")
                        print(f"  📍 Chat ID: {msg_data.get('chat_id', 'N/A')}")

                        if sender_type == "user":
                            print(f"\n  ✅ User message received!")
                            print(f"  ⏳ Waiting for bot response...")
                        elif sender_type == "bot":
                            print(f"\n  ✅ Bot response received!")
                            print(f"  🎯 Frontend should auto-update now!")

                        print(f"{'='*70}\n")

                    elif msg_type != "pong":
                        # Show other messages (not pong)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 {msg_type}")

                except Exception as e:
                    print(f"[ERROR] {e}")
                    continue

    except KeyboardInterrupt:
        print(f"\n\n{'='*70}")
        print(f"Monitor stopped by user")
        print(f"Total messages received: {message_count}")
        print(f"{'='*70}")
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
