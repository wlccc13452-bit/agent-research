"""测试美股指数更新流程"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession
from database.session import async_session_maker
from database.operations import get_us_daily_data
from services.us_market_analyzer import USMarketDataService
from services.background_updater import background_updater
from datasource import get_datasource, DataSourceType


async def test_us_indices_data_sources():
    """测试各数据源是否可以获取美股指数"""
    print("\n=== 测试美股指数数据源 ===\n")
    
    us_indices = ['^GSPC', '^IXIC', '^DJI', '^VIX', '^N225', '^KS11']
    us_ds = get_datasource().get_source(DataSourceType.YFINANCE)
    
    for symbol in us_indices:
        print(f"测试 {symbol}:")
        
        # 测试 K 线数据
        try:
            kline = await us_ds.get_index_kline(symbol, period='day', count=5)
            if kline:
                print(f"  ✅ K线数据获取成功，最新: {kline[-1]['date']} 收盘价: {kline[-1]['close']}")
            else:
                print(f"  ❌ K线数据获取失败")
        except Exception as e:
            print(f"  ❌ K线数据异常: {str(e)[:100]}")
        
        # 测试实时报价
        try:
            quote = await us_ds.get_us_quote(symbol)
            if quote:
                print(f"  ✅ 实时报价获取成功，当前价: {quote.get('current')}, 涨跌幅: {quote.get('change_pct')}%")
            else:
                print(f"  ❌ 实时报价获取失败")
        except Exception as e:
            print(f"  ❌ 实时报价异常: {str(e)[:100]}")
        
        print()


async def test_database_us_indices():
    """测试数据库中的美股指数数据"""
    print("\n=== 检查数据库中的美股指数 ===\n")
    
    us_indices = ['^GSPC', '^IXIC', '^DJI', '^VIX', '^N225', '^KS11']
    
    async with async_session_maker() as db:
        for symbol in us_indices:
            data = await get_us_daily_data(db, symbol, limit=1)
            if data:
                latest = data[0]
                print(f"✅ {symbol}: 最新数据 {latest['trade_date']}, 收盘价: {latest['close']}")
            else:
                print(f"❌ {symbol}: 数据库无数据")


async def test_us_index_update_task():
    """测试美股指数更新任务"""
    print("\n=== 测试美股指数更新任务 ===\n")
    
    symbol = '^GSPC'
    print(f"提交 {symbol} 更新任务...")
    result = await background_updater.submit_us_index_update_task(symbol)
    print(f"提交结果: {result}")
    
    # 等待任务完成
    task_id = result.get('task_id')
    if task_id:
        print(f"等待任务 {task_id} 完成...")
        for i in range(30):  # 最多等待30秒
            await asyncio.sleep(1)
            status = background_updater.get_task_status(task_id)
            if status:
                print(f"  [{i+1}s] 状态: {status.get('status')}")
                if status.get('status') in ['completed', 'failed']:
                    break
        
        final_status = background_updater.get_task_status(task_id)
        print(f"\n最终状态: {final_status}")


async def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("美股指数更新测试")
    print("="*60)
    
    # 1. 测试数据源
    await test_us_indices_data_sources()
    
    # 2. 检查数据库
    await test_database_us_indices()
    
    # 3. 测试更新任务（可选）
    # await test_us_index_update_task()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
