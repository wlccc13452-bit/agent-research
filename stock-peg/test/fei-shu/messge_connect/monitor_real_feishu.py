"""
Test real Feishu message handling
This test monitors database and WebSocket for real Feishu messages
"""
import sys
import json
import time
import asyncio
import websockets
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

WS_URL = "ws://localhost:8000/ws"

received_messages = []
last_db_count = 0


def check_database_messages():
    """Check database for new messages"""
    from database.session import get_db_sync
    from database.models import FeishuChatMessage
    
    db = get_db_sync()
    messages = db.query(FeishuChatMessage).order_by(
        FeishuChatMessage.send_time.desc()
    ).limit(5).all()
    db.close()
    return messages


async def websocket_monitor():
    """Monitor WebSocket for messages"""
    global received_messages
    
    print("\n[WS] Connecting to WebSocket...")
    async with websockets.connect(WS_URL) as ws:
        print("[WS] Connected! Waiting for messages...\n")
        
        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=1)
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                
                if msg_type in ['feishu-chat-message', 'feishu_chat_message']:
                    msg_data = data.get('data', {})
                    print(f"\n[WS] ★ FEISHU MESSAGE RECEIVED ★")
                    print(f"  Type: {msg_type}")
                    print(f"  Sender: {msg_data.get('sender_type')}")
                    print(f"  Content: {msg_data.get('content', '')[:60]}...")
                    print(f"  Time: {msg_data.get('send_time')}")
                    received_messages.append(data)
                elif msg_type not in ['pong', 'subscription']:
                    print(f"[WS] Received: {msg_type}")
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[WS] Error: {e}")
                break


async def database_monitor():
    """Monitor database for new messages"""
    global last_db_count
    
    from database.session import get_db_sync
    from database.models import FeishuChatMessage
    
    db = get_db_sync()
    
    # Get initial count
    initial_count = db.query(FeishuChatMessage).count()
    last_db_count = initial_count
    print(f"[DB] Initial message count: {initial_count}")
    
    last_check_time = datetime.now()
    
    while True:
        await asyncio.sleep(2)
        
        # Check for new messages in last 10 seconds
        recent_time = datetime.now() - timedelta(seconds=10)
        new_messages = db.query(FeishuChatMessage).filter(
            FeishuChatMessage.send_time >= recent_time
        ).order_by(FeishuChatMessage.send_time.desc()).all()
        
        for msg in new_messages:
            if msg.send_time > last_check_time:
                print(f"\n[DB] ★ NEW MESSAGE IN DATABASE ★")
                print(f"  ID: {msg.message_id}")
                print(f"  Sender: {msg.sender_type}")
                print(f"  Content: {msg.content[:60]}...")
                print(f"  Time: {msg.send_time}")
                last_check_time = msg.send_time
        
        current_count = db.query(FeishuChatMessage).count()
        if current_count != last_db_count:
            print(f"[DB] Message count changed: {last_db_count} -> {current_count}")
            last_db_count = current_count


async def run_test():
    """Run the real Feishu message test"""
    print("\n" + "="*60)
    print("Real Feishu Message Monitor")
    print("="*60)
    print("\nInstructions:")
    print("1. Send a message from your Feishu mobile app NOW")
    print("2. Watch for messages below")
    print("3. Press Ctrl+C to stop\n")
    print("="*60)
    
    # Run both monitors
    ws_task = asyncio.create_task(websocket_monitor())
    db_task = asyncio.create_task(database_monitor())
    
    try:
        await asyncio.gather(ws_task, db_task)
    except KeyboardInterrupt:
        print("\n\nStopping monitors...")
        ws_task.cancel()
        db_task.cancel()
        
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"WebSocket messages received: {len(received_messages)}")
    print(f"Database final count: {last_db_count}")
    
    if received_messages:
        print("\n[OK] WebSocket is receiving Feishu messages!")
        print("If frontend doesn't show them, the issue is in the frontend.")
    else:
        print("\n[WARN] No WebSocket messages received.")
        print("The issue is in the backend broadcast or connection.")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_test())
