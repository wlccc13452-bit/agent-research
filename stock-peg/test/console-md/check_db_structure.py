"""
检查数据库表结构
"""
import sys
import asyncio
from pathlib import Path
from sqlalchemy import text

# Windows控制台编码设置
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加backend到路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

async def check_table_structure():
    """检查数据库表结构"""
    from database.session import async_session_maker
    
    async with async_session_maker() as session:
        # 获取所有表
        tables_result = await session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ))
        tables = [row[0] for row in tables_result]
        
        print("\n" + "=" * 80)
        print("数据库表结构检查")
        print("=" * 80)
        
        for table in tables:
            print(f"\n【表名】: {table}")
            print("-" * 80)
            
            # 获取表结构
            pragma_result = await session.execute(text(f"PRAGMA table_info({table})"))
            columns = pragma_result.fetchall()
            
            print(f"{'序号':<6} {'列名':<20} {'类型':<15} {'非空':<8} {'默认值':<15} {'主键':<8}")
            print("-" * 80)
            for col in columns:
                cid, name, dtype, notnull, default, pk = col
                print(f"{cid:<6} {name:<20} {dtype:<15} {notnull:<8} {str(default):<15} {pk:<8}")
            
            # 获取记录数
            count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = count_result.scalar()
            print(f"\n记录数: {count}")
            
            # 如果是美股数据表，显示样例数据
            if 'us_' in table.lower() and count > 0:
                print("\n样例数据（前3条）:")
                sample_result = await session.execute(text(f"SELECT * FROM {table} LIMIT 3"))
                rows = sample_result.fetchall()
                if rows:
                    # 获取列名
                    cols = sample_result.keys()
                    print(f"  列名: {', '.join(cols)}")
                    for i, row in enumerate(rows, 1):
                        print(f"  第{i}条: {dict(zip(cols, row))}")

if __name__ == "__main__":
    asyncio.run(check_table_structure())
