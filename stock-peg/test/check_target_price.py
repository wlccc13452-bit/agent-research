#!/usr/bin/env python3
"""检查数据库中有基准价的股票"""
import sqlite3

conn = sqlite3.connect('backend/data/stock_peg.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT stock_code, stock_name, target_price, change_up_pct, change_down_pct 
    FROM daily_watchlist 
    WHERE target_price IS NOT NULL 
    LIMIT 10
''')

rows = cursor.fetchall()

print("Stocks with target_price:")
for row in rows:
    print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}% | {row[4]}%")

conn.close()
