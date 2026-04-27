"""
快速验证脚本 - 测试数据库连接和数据读取
使用Server端相同的服务和流程
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# 添加backend路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database.session import async_session_maker
from database.models import (
    StockRealtimeQuote, 
    StockKLineData, 
    DailyReport,
    FundamentalMetrics
)
from services.quote_data_service import QuoteDataService
from sqlalchemy import select, func


async def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("测试1: 数据库连接")
    print("=" * 60)
    
    try:
        async with async_session_maker() as db:
            # 测试连接
            result = await db.execute(select(1))
            print("[OK] 数据库连接成功")
            return True
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return False


async def test_stock_list():
    """测试股票列表"""
    print("\n" + "=" * 60)
    print("测试2: 股票列表")
    print("=" * 60)
    
    try:
        async with async_session_maker() as db:
            # 统计各表数据
            quote_count = await db.execute(select(func.count(StockRealtimeQuote.stock_code)))
            kline_count = await db.execute(select(func.count(StockKLineData.id)))
            report_count = await db.execute(select(func.count(DailyReport.id)))
            
            print(f"实时行情表: {quote_count.scalar()} 条记录")
            print(f"K线数据表: {kline_count.scalar()} 条记录")
            print(f"每日报告表: {report_count.scalar()} 条记录")
            
            # 获取前5个股票代码
            result = await db.execute(
                select(StockRealtimeQuote.stock_code, StockRealtimeQuote.stock_name)
                .limit(5)
            )
            
            print("\n前5个股票:")
            for row in result:
                print(f"  {row.stock_code} - {row.stock_name or '未知'}")
            
            return True
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        return False


async def test_quote_service(stock_code: str):
    """测试行情服务（使用server端服务）"""
    print("\n" + "=" * 60)
    print(f"测试3: 行情服务 - {stock_code}")
    print("=" * 60)
    
    try:
        async with async_session_maker() as db:
            # 使用server端的QuoteDataService
            quote_service = QuoteDataService()
            quote = await quote_service.get_quote_from_db(db, stock_code)
            
            if quote:
                print(f"[OK] 成功获取行情数据")
                print(f"  代码: {quote.code}")
                print(f"  名称: {quote.name}")
                print(f"  价格: {quote.price}")
                print(f"  涨跌: {quote.change} ({quote.change_pct}%)")
                print(f"  成交量: {quote.volume}")
                print(f"  时间戳: {quote.timestamp}")
                return True
            else:
                print(f"[WARN] 未找到该股票的行情数据")
                return False
    except Exception as e:
        print(f"[ERROR] 获取行情失败: {e}")
        return False


async def test_kline_data(stock_code: str):
    """测试K线数据"""
    print("\n" + "=" * 60)
    print(f"测试4: K线数据 - {stock_code}")
    print("=" * 60)
    
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(StockKLineData)
                .where(StockKLineData.stock_code == stock_code)
                .where(StockKLineData.period == 'day')
                .order_by(StockKLineData.trade_date.desc())
                .limit(5)
            )
            rows = result.scalars().all()
            
            if rows:
                print(f"[OK] 找到 {len(rows)} 条K线数据")
                print("\n最近5天K线:")
                for row in rows:
                    print(f"  {row.trade_date}: 开{row.open:.2f} 高{row.high:.2f} "
                          f"低{row.low:.2f} 收{row.close:.2f}")
                return True
            else:
                print(f"[WARN] 未找到该股票的K线数据")
                return False
    except Exception as e:
        print(f"[ERROR] 查询K线失败: {e}")
        return False


async def test_daily_report(stock_code: str):
    """测试每日报告"""
    print("\n" + "=" * 60)
    print(f"测试5: 每日报告 - {stock_code}")
    print("=" * 60)
    
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(DailyReport)
                .where(DailyReport.stock_code == stock_code)
                .order_by(DailyReport.report_date.desc())
                .limit(1)
            )
            report = result.scalar_one_or_none()
            
            if report:
                print(f"[OK] 找到最新报告: {report.report_date}")
                print(f"  收盘价: {report.close_price}")
                print(f"  涨跌幅: {report.change_pct}%")
                if report.overall_score:
                    print(f"  综合评分: {report.overall_score}")
                if report.action:
                    print(f"  操作建议: {report.action}")
                return True
            else:
                print(f"[WARN] 未找到该股票的报告数据")
                return False
    except Exception as e:
        print(f"[ERROR] 查询报告失败: {e}")
        return False


async def main():
    """主测试流程"""
    print("\n" + "股票数据读取测试（Server端服务）" + "\n")
    print(f"数据库路径: {Path(__file__).parent.parent.parent / 'backend' / 'data' / 'stock_peg.db'}")
    print()
    
    # 测试1: 数据库连接
    if not await test_database_connection():
        print("\n[ERROR] 测试终止：数据库连接失败")
        return
    
    # 测试2: 股票列表
    if not await test_stock_list():
        print("\n[WARN] 测试继续：无法获取股票列表")
    
    # 测试3-5: 使用示例股票代码
    test_stocks = ["600219", "000001", "601318"]  # 南山铝业、平安银行、中国平安
    
    for stock_code in test_stocks:
        print(f"\n尝试测试股票: {stock_code}")
        await test_quote_service(stock_code)
        await test_kline_data(stock_code)
        await test_daily_report(stock_code)
        
        # 只测试第一个有效的股票
        break
    
    print("\n" + "=" * 60)
    print("[OK] 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
