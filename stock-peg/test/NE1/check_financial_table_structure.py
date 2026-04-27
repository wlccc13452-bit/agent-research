"""
检查财务数据表结构
"""
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Windows控制台编码设置
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 创建数据库引擎
DATABASE_URL = "sqlite+aiosqlite:///d:/play-ground/股票研究/stock-peg/backend/data/stock_peg.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def check_table_structure():
    """检查表结构"""
    async with async_session_maker() as session:
        # 检查 fundamental_metrics 表结构
        print("\n" + "=" * 80)
        print("fundamental_metrics 表结构")
        print("=" * 80)
        
        result = await session.execute(text("PRAGMA table_info(fundamental_metrics)"))
        columns = result.fetchall()
        
        print(f"\n{'序号':<6} {'列名':<30} {'类型':<20}")
        print("-" * 80)
        for col in columns:
            cid, name, dtype, notnull, default, pk = col
            print(f"{cid:<6} {name:<30} {dtype:<20}")
        
        # 查看一条样例数据
        print("\n样例数据:")
        result = await session.execute(text("SELECT * FROM fundamental_metrics LIMIT 1"))
        row = result.fetchone()
        
        if row:
            # 获取列名
            cols = result.keys()
            print(f"\n列名: {list(cols)}")
            print(f"\n数据: {dict(zip(cols, row))}")
        
        # 检查 financial_history 表结构
        print("\n" + "=" * 80)
        print("financial_history 表结构")
        print("=" * 80)
        
        result = await session.execute(text("PRAGMA table_info(financial_history)"))
        columns = result.fetchall()
        
        print(f"\n{'序号':<6} {'列名':<30} {'类型':<20}")
        print("-" * 80)
        for col in columns:
            cid, name, dtype, notnull, default, pk = col
            print(f"{cid:<6} {name:<30} {dtype:<20}")
        
        # 查看一条样例数据
        print("\n样例数据:")
        result = await session.execute(text("SELECT * FROM financial_history LIMIT 1"))
        row = result.fetchone()
        
        if row:
            # 获取列名
            cols = result.keys()
            print(f"\n列名: {list(cols)}")
            print(f"\n数据: {dict(zip(cols, row))}")


if __name__ == "__main__":
    asyncio.run(check_table_structure())
