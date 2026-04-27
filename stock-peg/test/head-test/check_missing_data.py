"""
检查服务器上缺失的 HeadBar 指数数据和自持股票财务数据
"""
import sys
import asyncio
from pathlib import Path

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import select, func
from database.session import async_session_maker
from database.models import StockKLineData, FundamentalMetrics, FinancialHistory
from services.holding_manager import HoldingManager
from config.settings import settings


# HeadBar 指数配置
CN_INDICES = {
    '000001': '上证指数',
    '399001': '深证指数',
    '399006': '创业板指',
}

US_INDICES = {
    '^GSPC': '标普500',
    '^IXIC': '纳斯达克',
    '^DJI': '道琼斯',
    '^VIX': 'VIX恐慌指数',
}


async def check_kline_data(stock_code: str, name: str, min_records: int = 10):
    """
    检查K线数据是否存在
    
    Args:
        stock_code: 股票/指数代码
        name: 名称
        min_records: 最小记录数
    
    Returns:
        dict: 检查结果
    """
    async with async_session_maker() as db:
        # 查询K线数据总数
        count_query = select(func.count()).select_from(StockKLineData).where(
            StockKLineData.stock_code == stock_code,
            StockKLineData.period == 'day'
        )
        result = await db.execute(count_query)
        count = result.scalar()
        
        # 查询最新一条数据的日期
        if count > 0:
            latest_query = select(StockKLineData).where(
                StockKLineData.stock_code == stock_code,
                StockKLineData.period == 'day'
            ).order_by(StockKLineData.trade_date.desc()).limit(1)
            latest_result = await db.execute(latest_query)
            latest_record = latest_result.scalar_one_or_none()
            latest_date = latest_record.trade_date if latest_record else None
        else:
            latest_date = None
        
        has_data = count >= min_records
        
        return {
            'code': stock_code,
            'name': name,
            'has_data': has_data,
            'count': count,
            'latest_date': latest_date,
            'status': '[OK]' if has_data else '[X]'
        }


async def check_financial_data(stock_code: str, name: str):
    """
    检查财务数据是否存在
    
    Args:
        stock_code: 股票代码
        name: 名称
    
    Returns:
        dict: 检查结果
    """
    async with async_session_maker() as db:
        # 检查 fundamental_metrics 表
        fm_count_query = select(func.count()).select_from(FundamentalMetrics).where(
            FundamentalMetrics.stock_code == stock_code
        )
        fm_result = await db.execute(fm_count_query)
        fm_count = fm_result.scalar()
        
        # 检查 financial_history 表
        fh_count_query = select(func.count()).select_from(FinancialHistory).where(
            FinancialHistory.stock_code == stock_code
        )
        fh_result = await db.execute(fh_count_query)
        fh_count = fh_result.scalar()
        
        # 查询最新数据日期
        latest_fm_date = None
        latest_fh_date = None
        
        if fm_count > 0:
            latest_fm_query = select(FundamentalMetrics).where(
                FundamentalMetrics.stock_code == stock_code
            ).order_by(FundamentalMetrics.report_date.desc()).limit(1)
            fm_latest_result = await db.execute(latest_fm_query)
            fm_latest = fm_latest_result.scalar_one_or_none()
            latest_fm_date = fm_latest.report_date if fm_latest else None
        
        if fh_count > 0:
            latest_fh_query = select(FinancialHistory).where(
                FinancialHistory.stock_code == stock_code
            ).order_by(FinancialHistory.report_date.desc()).limit(1)
            fh_latest_result = await db.execute(latest_fh_query)
            fh_latest = fh_latest_result.scalar_one_or_none()
            latest_fh_date = fh_latest.report_date if fh_latest else None
        
        has_data = fm_count > 0 or fh_count > 0
        
        return {
            'code': stock_code,
            'name': name,
            'has_data': has_data,
            'fm_count': fm_count,
            'fh_count': fh_count,
            'latest_fm_date': latest_fm_date,
            'latest_fh_date': latest_fh_date,
            'status': '[OK]' if has_data else '[X]'
        }


async def main():
    """主检查流程"""
    print("=" * 80)
    print("开始检查服务器数据完整性...")
    print("=" * 80)
    print()
    
    # ==================== 检查 HeadBar 指数数据 ====================
    print("【1】检查 HeadBar 指数K线数据")
    print("-" * 80)
    
    index_results = []
    
    # 检查A股指数
    print("\nA股指数:")
    for code, name in CN_INDICES.items():
        result = await check_kline_data(code, name)
        index_results.append(result)
        print(f"  {result['status']} {result['name']:8s} ({result['code']:6s}): {result['count']:4d} 条记录, 最新: {result['latest_date'] or '无数据'}")
    
    # 检查美股指数
    print("\n美股指数:")
    for code, name in US_INDICES.items():
        result = await check_kline_data(code, name)
        index_results.append(result)
        print(f"  {result['status']} {result['name']:10s} ({result['code']:6s}): {result['count']:4d} 条记录, 最新: {result['latest_date'] or '无数据'}")
    
    # 统计缺失数据
    missing_indices = [r for r in index_results if not r['has_data']]
    print()
    print(f"指数数据统计: {len(index_results) - len(missing_indices)}/{len(index_results)} 完整")
    if missing_indices:
        print("[!] 缺失指数数据:")
        for r in missing_indices:
            print(f"   - {r['name']} ({r['code']})")
    
    print()
    print("=" * 80)
    
    # ==================== 检查自持股票数据 ====================
    print("【2】检查自持股票数据")
    print("-" * 80)
    
    # 加载自持股票
    holding_manager = HoldingManager(settings.holdings_file_path)
    holdings = await holding_manager.load_holdings()
    
    stock_results = []
    
    if holdings and holdings.sectors:
        for sector in holdings.sectors:
            print(f"\n板块: {sector.name}")
            for stock in sector.stocks:
                # 检查K线数据
                kline_result = await check_kline_data(stock.code, stock.name)
                
                # 检查财务数据
                financial_result = await check_financial_data(stock.code, stock.name)
                
                stock_results.append({
                    'sector': sector.name,
                    'code': stock.code,
                    'name': stock.name,
                    'kline': kline_result,
                    'financial': financial_result
                })
                
                # 打印结果
                kline_status = kline_result['status']
                financial_status = financial_result['status']
                print(f"  {stock.name:10s} ({stock.code:6s}): K线[{kline_status}] {kline_result['count']:3d}条, 财务[{financial_status}] 基本面{kline_result['count']:3d}条, 历史{financial_result['fh_count']:3d}条")
    
    # 统计缺失数据
    missing_kline = [r for r in stock_results if not r['kline']['has_data']]
    missing_financial = [r for r in stock_results if not r['financial']['has_data']]
    
    print()
    print(f"股票K线数据统计: {len(stock_results) - len(missing_kline)}/{len(stock_results)} 完整")
    if missing_kline:
        print("[!] 缺失K线数据:")
        for r in missing_kline:
            print(f"   - {r['name']} ({r['code']}) - {r['sector']}")
    
    print()
    print(f"股票财务数据统计: {len(stock_results) - len(missing_financial)}/{len(stock_results)} 完整")
    if missing_financial:
        print("[!] 缺失财务数据:")
        for r in missing_financial:
            print(f"   - {r['name']} ({r['code']}) - {r['sector']}")
    
    print()
    print("=" * 80)
    
    # ==================== 总结 ====================
    print("【总结】")
    print("-" * 80)
    
    total_issues = len(missing_indices) + len(missing_kline) + len(missing_financial)
    
    if total_issues == 0:
        print("[OK] 所有数据完整！")
    else:
        print(f"[!] 发现 {total_issues} 个数据缺失问题:")
        if missing_indices:
            print(f"   - 指数K线缺失: {len(missing_indices)} 个")
        if missing_kline:
            print(f"   - 股票K线缺失: {len(missing_kline)} 只")
        if missing_financial:
            print(f"   - 股票财务缺失: {len(missing_financial)} 只")
        
        print()
        print("建议操作:")
        print("  1. 重启后端服务，触发自动数据更新")
        print("  2. 或手动调用 API 更新数据:")
        if missing_indices:
            print(f"     - 更新指数: POST /api/stocks/update/<code>/day")
        if missing_kline or missing_financial:
            print(f"     - 更新股票: POST /api/stocks/update/<code>/day")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
