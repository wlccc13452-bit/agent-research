"""
修复数据库查询问题的快速脚本
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

async def check_us_indices():
    """检查美股指数数据"""
    from database.session import async_session_maker
    
    async with async_session_maker() as session:
        print("\n" + "=" * 80)
        print("美股指数数据检查")
        print("=" * 80)
        
        # 正确的查询：使用 us_stock_code 列
        result = await session.execute(text(
            "SELECT us_stock_code, trade_date, close_price, change_pct "
            "FROM us_daily_data "
            "ORDER BY us_stock_code, trade_date DESC"
        ))
        rows = result.fetchall()
        
        print(f"\n总记录数: {len(rows)}")
        print("\n各指数最新数据:")
        
        # 按指数分组显示
        indices_data = {}
        for row in rows:
            code = row[0]
            if code not in indices_data:
                indices_data[code] = row
        
        for code, data in sorted(indices_data.items()):
            print(f"\n  {code}:")
            print(f"    日期: {data[1]}")
            print(f"    收盘价: {data[2]}")
            print(f"    涨跌幅: {data[3]}%")
        
        # 检查缺失的指数
        expected_indices = ['^GSPC', '^IXIC', '^DJI', '^VIX']
        existing_indices = set(indices_data.keys())
        missing_indices = set(expected_indices) - existing_indices
        
        if missing_indices:
            print(f"\n⚠ 缺失的指数: {', '.join(missing_indices)}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(check_us_indices())
