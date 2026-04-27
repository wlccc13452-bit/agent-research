"""
检查服务器上缺失的 HeadBar 指数数据和自持股票财务数据
版本2：从server数据库获取股票代码映射（StockRealtimeQuote表）
"""
import sys
import asyncio
from pathlib import Path

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import select, func
from database.session import async_session_maker
from database.models import StockKLineData, FundamentalMetrics, FinancialHistory, StockRealtimeQuote
from config.settings import settings


# HeadBar 指数配置（固定配置，不需要从数据库获取）
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


async def load_stock_code_map_from_server() -> dict:
    """
    从server数据库加载股票代码映射（stock_name -> stock_code）
    
    数据来源：StockRealtimeQuote 表
    - server通过外部API（如腾讯、Akshare等）获取股票实时行情时
    - 会将股票代码和名称保存到这个表中
    - 这就是server本地保存的股票代号来源
    """
    stock_map = {}
    
    async with async_session_maker() as db:
        # 从 StockRealtimeQuote 表查询所有股票代码和名称
        query = select(
            StockRealtimeQuote.stock_code, 
            StockRealtimeQuote.stock_name
        ).where(
            StockRealtimeQuote.stock_name.isnot(None)
        )
        result = await db.execute(query)
        rows = result.all()
        
        for row in rows:
            code, name = row
            if name and code:
                # 建立名称到代码的映射
                stock_map[name] = code
        
        print(f"[i] 从server数据库加载了 {len(stock_map)} 个股票代码映射")
        
        # 显示部分映射示例
        if len(stock_map) > 0:
            print("[i] 映射示例:")
            for i, (name, code) in enumerate(list(stock_map.items())[:5]):
                print(f"    {name} -> {code}")
            if len(stock_map) > 5:
                print(f"    ... 还有 {len(stock_map) - 5} 个")
        
        # 如果数据库中没有数据，显示警告
        if len(stock_map) == 0:
            print("[!] 警告：server数据库中没有股票代码映射数据")
            print("[!] 原因可能是：")
            print("    1. 后端服务从未运行过")
            print("    2. 从未调用过获取股票实时行情的API")
            print("    3. StockRealtimeQuote 表为空")
            print("[!] 建议：先启动后端服务，让它自动获取并保存股票数据")
    
    return stock_map


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
        latest_date = None
        if count > 0:
            latest_query = select(StockKLineData).where(
                StockKLineData.stock_code == stock_code,
                StockKLineData.period == 'day'
            ).order_by(StockKLineData.trade_date.desc()).limit(1)
            latest_result = await db.execute(latest_query)
            latest_record = latest_result.scalar_one_or_none()
            latest_date = latest_record.trade_date if latest_record else None
        
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
    
    # ==================== 从server数据库加载股票代码映射 ====================
    print("【0】从server数据库加载股票代码映射")
    print("-" * 80)
    
    stock_code_map = await load_stock_code_map_from_server()
    
    print()
    print("=" * 80)
    
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
    
    # 从自持股票文件读取
    holdings_file = Path(settings.holdings_file_path)
    if not holdings_file.exists():
        print(f"[!] 自持股票文件不存在: {holdings_file}")
        return
    
    # 解析自持股票文件
    with open(holdings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sectors = []
    current_sector = None
    stock_results = []
    missing_code_stocks = []  # 无法获取代码的股票
    
    for line in content.split('\n'):
        line = line.rstrip()
        if line.startswith('## '):
            # 板块标题
            sector_name = line[3:].strip()
            current_sector = {'name': sector_name, 'stocks': []}
            sectors.append(current_sector)
        elif line.strip() and not line.startswith('#') and current_sector:
            # 股票名称
            stock_name = line.strip()
            
            # 从server数据库的映射表获取股票代码
            stock_code = stock_code_map.get(stock_name)
            
            # 如果找不到，跳过
            if not stock_code:
                missing_code_stocks.append({
                    'name': stock_name,
                    'sector': current_sector['name']
                })
                continue
            
            # 检查K线数据
            kline_result = await check_kline_data(stock_code, stock_name)
            
            # 检查财务数据
            financial_result = await check_financial_data(stock_code, stock_name)
            
            stock_results.append({
                'sector': current_sector['name'],
                'code': stock_code,
                'name': stock_name,
                'kline': kline_result,
                'financial': financial_result
            })
            
            current_sector['stocks'].append({
                'name': stock_name,
                'code': stock_code
            })
    
    # 打印无法获取代码的股票
    if missing_code_stocks:
        print("\n[!] 无法从server数据库获取代码的股票:")
        for stock in missing_code_stocks:
            print(f"   - {stock['name']} ({stock['sector']})")
        print("[!] 建议：")
        print("    1. 启动后端服务，让它自动获取这些股票的实时行情")
        print("    2. 或手动调用 API: GET /api/stocks/quote/<股票名称>")
        print()
    
    # 打印结果
    for sector in sectors:
        print(f"\n板块: {sector['name']}")
        for stock in sector['stocks']:
            # 找到对应的结果
            r = next((x for x in stock_results if x['code'] == stock['code']), None)
            if r:
                kline_status = r['kline']['status']
                financial_status = r['financial']['status']
                print(f"  {r['name']:10s} ({r['code']:6s}): K线[{kline_status}] {r['kline']['count']:3d}条, 财务[{financial_status}] 基本面{r['financial']['fm_count']:3d}条, 历史{r['financial']['fh_count']:3d}条")
    
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
    
    total_issues = len(missing_indices) + len(missing_kline) + len(missing_financial) + len(missing_code_stocks)
    
    if total_issues == 0:
        print("[OK] 所有数据完整！")
    else:
        print(f"[!] 发现 {total_issues} 个问题:")
        if missing_code_stocks:
            print(f"   - 无法获取代码: {len(missing_code_stocks)} 只")
        if missing_indices:
            print(f"   - 指数K线缺失: {len(missing_indices)} 个")
        if missing_kline:
            print(f"   - 股票K线缺失: {len(missing_kline)} 只")
        if missing_financial:
            print(f"   - 股票财务缺失: {len(missing_financial)} 只")
        
        print()
        print("建议操作:")
        if missing_code_stocks:
            print("  0. 【重要】先启动后端服务，让它自动获取股票代码映射")
        print("  1. 重启后端服务，触发自动数据更新")
        print("  2. 或手动调用 API 更新数据:")
        if missing_indices:
            print(f"     - 更新指数: POST /api/stocks/update/<code>/day")
        if missing_kline or missing_financial:
            print(f"     - 更新股票: POST /api/stocks/update/<code>/day")
    
    print("=" * 80)
    
    # 返回结果供其他程序使用
    return {
        'missing_indices': missing_indices,
        'missing_kline': missing_kline,
        'missing_financial': missing_financial,
        'missing_code_stocks': missing_code_stocks,
        'total_issues': total_issues
    }


if __name__ == "__main__":
    asyncio.run(main())
