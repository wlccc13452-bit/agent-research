#!/usr/bin/env python3
"""获取测试用的 chat_id"""
import sqlite3
import os
import sys
from pathlib import Path

# 添加 backend 目录到路径
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

db_path = backend_dir / "data" / "stock_peg.db"

if not db_path.exists():
    print("❌ 数据库文件不存在")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取最近的聊天记录
cursor.execute('''
    SELECT DISTINCT chat_id, sender_name, created_at 
    FROM feishu_chat_messages 
    WHERE chat_id IS NOT NULL 
    ORDER BY created_at DESC 
    LIMIT 5
''')
rows = cursor.fetchall()

print("="*60)
print("最近的聊天记录：")
print("="*60)

if rows:
    for row in rows:
        print(f"chat_id: {row[0]}")
        print(f"  sender_name: {row[1]}")
        print(f"  created_at: {row[2]}")
        print()
    
    # 返回第一个 chat_id 供测试使用
    print(f"✅ 推荐测试 chat_id: {rows[0][0]}")
else:
    print("❌ 没有找到聊天记录")

conn.close()
