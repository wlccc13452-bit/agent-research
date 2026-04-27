"""
检查和修复数据库表结构
"""
import sys
import sqlite3
from pathlib import Path

# 数据库路径
db_path = Path(__file__).parent.parent.parent / "backend" / "data" / "stock_peg.db"

print("=" * 60)
print("检查数据库表结构")
print("=" * 60)
print(f"\n数据库路径: {db_path}")
print(f"数据库存在: {db_path.exists()}\n")

if not db_path.exists():
    print("[ERROR] 数据库文件不存在！")
    sys.exit(1)

# 连接数据库
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 检查 daily_reports 表结构
print("\n--- daily_reports 表结构 ---")
cursor.execute("PRAGMA table_info(daily_reports)")
columns = cursor.fetchall()

print(f"当前字段数: {len(columns)}\n")
print("字段列表:")
for col in columns:
    print(f"  {col[1]:30s} {col[2]:15s} {'NOT NULL' if col[3] else 'NULL'}")

# 检查是否有新字段
column_names = [col[1] for col in columns]
new_columns = [
    ('smart_analysis', 'TEXT'),
    ('smart_analysis_formatted', 'TEXT'),
    ('pmr_data', 'TEXT'),
    ('llm_model', 'VARCHAR(50)'),
    ('llm_provider', 'VARCHAR(50)')
]

print("\n\n--- 检查新字段 ---")
missing_columns = []
for col_name, col_type in new_columns:
    if col_name in column_names:
        print(f"  [OK] {col_name} - 已存在")
    else:
        print(f"  [MISSING] {col_name} - 缺失")
        missing_columns.append((col_name, col_type))

# 如果有缺失字段，提示修复
if missing_columns:
    print("\n\n" + "=" * 60)
    print("发现缺失字段，是否添加？")
    print("=" * 60)
    
    for col_name, col_type in missing_columns:
        print(f"  - {col_name} ({col_type})")
    
    choice = input("\n是否添加这些字段？(y/n): ").strip().lower()
    
    if choice == 'y':
        print("\n开始添加字段...")
        for col_name, col_type in missing_columns:
            try:
                sql = f"ALTER TABLE daily_reports ADD COLUMN {col_name} {col_type}"
                cursor.execute(sql)
                print(f"  [OK] 已添加 {col_name}")
            except Exception as e:
                print(f"  [ERROR] 添加 {col_name} 失败: {e}")
        
        conn.commit()
        print("\n[OK] 数据库表结构更新完成！")
    else:
        print("\n已取消更新。")
else:
    print("\n\n[OK] 所有字段都已存在，无需更新。")

conn.close()
