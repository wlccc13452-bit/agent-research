#!/usr/bin/env python3
"""检查数据库中南山铝业的基准价数据"""
import sqlite3

conn = sqlite3.connect('backend/data/stock_peg.db')
cursor = conn.cursor()

# 查询所有包含"南山铝业"或"600219"的记录
cursor.execute('''
    SELECT id, stock_code, stock_name, target_price, change_up_pct, change_down_pct, stop_loss_price, notes, created_at, updated_at
    FROM daily_watchlist 
    WHERE stock_name LIKE '%南山铝业%' OR stock_code LIKE '%600219%'
    ORDER BY created_at DESC
''')

rows = cursor.fetchall()

print("=" * 100)
print("查询条件: stock_name LIKE '%南山铝业%' OR stock_code LIKE '%600219%'")
print("=" * 100)

if rows:
    for row in rows:
        print(f"\n[Record ID: {row[0]}]")
        print(f"  Stock code: {row[1]}")
        print(f"  Stock name: {row[2]}")
        print(f"  Target price: {row[3]}")
        print(f"  Change up pct: {row[4]}%")
        print(f"  Change down pct: {row[5]}%")
        print(f"  Stop loss price: {row[6]}")
        print(f"  Notes: {row[7]}")
        print(f"  Created at: {row[8]}")
        print(f"  Updated at: {row[9]}")
else:
    print("\n[FAIL] No records found")

# 查询所有有基准价的记录
print("\n" + "=" * 100)
print("所有有基准价的记录（前10条）:")
print("=" * 100)
cursor.execute('''
    SELECT stock_code, stock_name, target_price, change_up_pct, change_down_pct
    FROM daily_watchlist 
    WHERE target_price IS NOT NULL
    LIMIT 10
''')

all_rows = cursor.fetchall()
if all_rows:
    for row in all_rows:
        print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}% | {row[4]}%")
else:
    print("  [FAIL] No records with target_price")

conn.close()
