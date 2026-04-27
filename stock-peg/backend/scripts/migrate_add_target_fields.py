"""数据库迁移脚本：为 DailyWatchlist 表添加目标价相关字段"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database.session import async_session_maker


async def migrate():
    """执行数据库迁移"""
    async with async_session_maker() as session:
        try:
            # 检查字段是否已存在
            check_sql = text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('daily_watchlist') 
                WHERE name IN ('change_up_pct', 'change_down_pct')
            """)
            result = await session.execute(check_sql)
            row = result.fetchone()
            
            if row and row.count >= 2:
                print("[OK] 字段已存在，无需迁移")
                return
            
            # 添加新字段
            try:
                alter_sql = text("""
                    ALTER TABLE daily_watchlist 
                    ADD COLUMN change_up_pct DECIMAL(10, 4)
                """)
                await session.execute(alter_sql)
                print("[OK] 已添加 change_up_pct 字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("[OK] change_up_pct 字段已存在")
                else:
                    raise
            
            try:
                alter_sql = text("""
                    ALTER TABLE daily_watchlist 
                    ADD COLUMN change_down_pct DECIMAL(10, 4)
                """)
                await session.execute(alter_sql)
                print("[OK] 已添加 change_down_pct 字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("[OK] change_down_pct 字段已存在")
                else:
                    raise
            
            await session.commit()
            print("[OK] 数据库迁移完成")
            
        except Exception as e:
            print(f"[ERROR] 迁移失败: {str(e)}")
            await session.rollback()
            raise


if __name__ == "__main__":
    print("开始数据库迁移...")
    asyncio.run(migrate())
