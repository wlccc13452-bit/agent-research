"""
Check Feishu chat history in database
"""
import sqlite3
import os
from datetime import datetime

def check_chat_history():
    """Check recent Feishu chat messages in database"""
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'data', 'stock_peg.db')
    
    print("=" * 60)
    print("Checking Feishu Chat History in Database")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='feishu_chat_messages'
    """)
    
    if not cursor.fetchone():
        print("[ERROR] Table 'feishu_chat_messages' does not exist")
        conn.close()
        return
    
    # Get recent messages
    cursor.execute("""
        SELECT id, message_id, sender_type, content, send_time, chat_id
        FROM feishu_chat_messages
        ORDER BY send_time DESC
        LIMIT 10
    """)
    
    messages = cursor.fetchall()
    
    if not messages:
        print("\n[INFO] No messages found in database")
    else:
        print(f"\n[INFO] Found {len(messages)} recent messages:\n")
        for msg in messages:
            msg_id, message_id, sender_type, content, send_time, chat_id = msg
            print(f"  [{send_time}] {sender_type.upper()}: {content[:50]}...")
            print(f"    Message ID: {message_id}")
            print(f"    Chat ID: {chat_id}")
            print()
    
    conn.close()
    print("=" * 60)


if __name__ == "__main__":
    check_chat_history()
