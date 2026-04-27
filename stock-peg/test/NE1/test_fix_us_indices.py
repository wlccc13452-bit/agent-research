"""
测试修复方案：美股指数获取
测试目标：
1. 验证数据库查询（列名修复）
2. 验证数据获取和返回
"""
import asyncio
import sys
import os
import logging
from datetime import datetime

# Windows控制台编码设置
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, desc, text

# 创建数据库引擎
DATABASE_URL = "sqlite+aiosqlite:///d:/play-ground/股票研究/stock-peg/backend/data/stock_peg.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_us_database_query():
    """测试1: 验证数据库查询（使用正确的列名）"""
    print("\n" + "=" * 80)
    print("测试1: 美股数据库查询验证")
    print("=" * 80)
    
    async with async_session_maker() as session:
        # 测试1: 查询所有美股指数
        print("\n【步骤1】查询所有美股指数...")
        
        # ✓ 正确的查询方式（使用 us_stock_code）
        result = await session.execute(text(
            "SELECT us_stock_code, trade_date, close_price, change_pct "
            "FROM us_daily_data "
            "ORDER BY us_stock_code, trade_date DESC"
        ))
        all_data = result.fetchall()
        
        print(f"✓ 总记录数: {len(all_data)}")
        
        # 按指数分组显示最新数据
        indices_latest = {}
        for row in all_data:
            code = row[0]
            if code not in indices_latest:
                indices_latest[code] = row
        
        print("\n【步骤2】各指数最新数据:")
        for code, data in sorted(indices_latest.items()):
            print(f"  {code}:")
            print(f"    日期: {data[1]}")
            print(f"    收盘价: {data[2]}")
            print(f"    涨跌幅: {data[3]}%")
        
        # 测试2: 查询特定指数
        print("\n【步骤3】查询特定指数 (^GSPC)...")
        
        result = await session.execute(text(
            "SELECT us_stock_code, trade_date, close_price "
            "FROM us_daily_data "
            "WHERE us_stock_code = '^GSPC' "
            "ORDER BY trade_date DESC LIMIT 5"
        ))
        sp500_data = result.fetchall()
        
        if sp500_data:
            print(f"✓ 找到 {len(sp500_data)} 条记录")
            for data in sp500_data:
                print(f"  {data[1]}: {data[2]}")
        else:
            print("✗ 未找到数据")
        
        # 测试3: 检查VIX数据
        print("\n【步骤4】检查VIX数据...")
        
        result = await session.execute(text(
            "SELECT us_stock_code, trade_date, close_price "
            "FROM us_daily_data "
            "WHERE us_stock_code = '^VIX' "
            "ORDER BY trade_date DESC LIMIT 1"
        ))
        vix_data = result.fetchone()
        
        if vix_data:
            print(f"✓ VIX数据存在")
            print(f"  日期: {vix_data[1]}")
            print(f"  值: {vix_data[2]}")
        else:
            print("✗ VIX数据不存在")


async def test_us_market_service():
    """测试2: 验证美股数据服务"""
    print("\n" + "=" * 80)
    print("测试2: 美股数据服务验证")
    print("=" * 80)
    
    # 先测试数据库直接查询
    print("\n【步骤1】直接查询数据库测试...")
    
    async with async_session_maker() as session:
        result = await session.execute(text(
            "SELECT us_stock_code, trade_date, close_price, change_pct "
            "FROM us_daily_data "
            "WHERE us_stock_code = '^GSPC' "
            "ORDER BY trade_date DESC LIMIT 1"
        ))
        data = result.fetchone()
        
        if data:
            print(f"✓ 成功获取数据")
            print(f"  代码: {data[0]}")
            print(f"  日期: {data[1]}")
            print(f"  收盘价: {data[2]}")
            print(f"  涨跌幅: {data[3]}%")
        else:
            print("✗ 未获取到数据")
    
    # 测试获取所有美股指数
    print("\n【步骤2】获取所有美股指数...")
    
    async with async_session_maker() as session:
        result = await session.execute(text(
            "SELECT us_stock_code, trade_date, close_price, change_pct "
            "FROM us_daily_data "
            "WHERE us_stock_code IN ('^GSPC', '^IXIC', '^DJI', '^VIX') "
            "ORDER BY us_stock_code, trade_date DESC"
        ))
        all_data = result.fetchall()
        
        # 按指数分组，获取每个指数的最新数据
        indices_latest = {}
        for row in all_data:
            code = row[0]
            if code not in indices_latest:
                indices_latest[code] = {
                    'code': code,
                    'date': row[1],
                    'close': row[2],
                    'change_pct': row[3]
                }
        
        if indices_latest:
            print(f"✓ 成功获取 {len(indices_latest)} 个指数")
            for code, data in sorted(indices_latest.items()):
                print(f"  {code}: {data['close']} ({data['change_pct']}%)")
        else:
            print("✗ 未获取到指数数据")


async def test_data_source_fetch():
    """测试3: 验证数据源获取能力"""
    print("\n" + "=" * 80)
    print("测试3: 数据源获取能力验证")
    print("=" * 80)
    
    from backend.services.us_market_analyzer import USMarketDataService
    
    service = USMarketDataService()
    
    # 测试东方财富
    print("\n【步骤1】测试东方财富数据源...")
    
    for symbol in ['^GSPC', '^IXIC', '^DJI', '^VIX']:
        print(f"\n  测试 {symbol}:")
        try:
            data = await service._get_from_eastmoney(symbol)
            if data:
                print(f"    ✓ 成功: 收盘价={data.get('previous_close')}")
            else:
                print(f"    ✗ 失败: 无数据")
        except Exception as e:
            print(f"    ✗ 错误: {str(e)}")
    
    # 测试Alpha Vantage（如果配置了）
    print("\n【步骤2】测试Alpha Vantage数据源...")
    
    try:
        data = await service._get_from_alphavantage('^GSPC', '1mo')
        if data:
            print(f"  ✓ 成功获取数据")
        else:
            print(f"  ✗ 失败: 无数据")
    except Exception as e:
        print(f"  ✗ 错误: {str(e)}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("美股指数获取修复方案测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # 测试1: 数据库查询
        await test_us_database_query()
        
        # 测试2: 数据服务
        await test_us_market_service()
        
        # 测试3: 数据源
        await test_data_source_fetch()
        
        print("\n" + "=" * 80)
        print("✓ 所有测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
