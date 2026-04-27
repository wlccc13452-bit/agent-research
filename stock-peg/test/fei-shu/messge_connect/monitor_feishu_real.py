"""Monitor real Feishu messages in real-time"""
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

backend_dir = Path(__file__).resolve().parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from database.session import get_db_sync
from database.models import FeishuChatMessage

print("\n" + "=" * 60)
print("Real Feishu Message Monitor")
print("=" * 60)
print("\nInstructions:")
print("1. Send a message in Feishu mobile app NOW")
print("2. Watch this monitor for new messages")
print("\nMonitoring... (Press Ctrl+C to stop)")
print("=" * 60 + "\n")

db = get_db_sync()
last_count = 0
last_time = datetime.now() - timedelta(minutes=5)

try:
    while True:
        # Check for new messages in last 10 seconds
        recent_time = datetime.now() - timedelta(seconds=10)
        new_messages = db.query(FeishuChatMessage).filter(
            FeishuChatMessage.send_time >= recent_time
        ).order_by(FeishuChatMessage.send_time.desc()).all()
        
        if new_messages:
            for msg in new_messages:
                if msg.send_time > last_time:
                    print(f"\n[NEW MESSAGE] {datetime.now().strftime('%H:%M:%S')}")
                    print(f"  Type: {msg.sender_type}")
                    print(f"  Content: {msg.content[:50]}")
                    print(f"  Chat ID: {msg.chat_id}")
                    print(f"  Message ID: {msg.message_id}")
                    print(f"  Time: {msg.send_time}")
                    last_time = msg.send_time
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped.")
finally:
    db.close()
