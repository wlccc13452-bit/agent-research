#!/usr/bin/env python3
"""检查数据库中所有股票代码格式"""
import sqlite3

conn = sqlite3.connect('backend/data/stock_peg.db')
cursor = conn.cursor()

# 查询所有股票代码
cursor.execute('''
    SELECT DISTINCT stock_code, stock_name
    FROM daily_watchlist
    ORDER BY stock_code
    LIMIT 20
''')

rows = cursor.fetchall()

print("=" * 100)
print("All stock codes in daily_watchlist table:")
print("=" * 100)

if rows:
    for row in rows:
        print(f"  [{row[0]}] {row[1]}")
else:
    print("  [FAIL] No records in daily_watchlist table")

# 查询所有表名
print("\n" + "=" * 100)
print("All tables in database:")
print("=" * 100)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

# 查询daily_watchlist表的总记录数
cursor.execute("SELECT COUNT(*) FROM daily_watchlist")
count = cursor.fetchone()[0]
print(f"\nTotal records in daily_watchlist: {count}")

conn.close()
