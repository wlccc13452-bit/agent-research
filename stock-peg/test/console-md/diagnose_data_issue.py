"""
诊断脚本：检查财务数据和指数获取问题
运行方式：使用项目虚拟环境执行
d:/play-ground/股票研究/stock-peg/backend/.venv/Scripts/python.exe diagnose_data_issue.py
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Windows控制台编码设置
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加backend到路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def diagnose():
    """主诊断函数"""
    print("=" * 80)
    print("数据获取问题诊断开始")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. 检查配置
    print("\n【1. 配置检查】")
    await check_config()
    
    # 2. 检查数据库连接
    print("\n【2. 数据库连接检查】")
    await check_database()
    
    # 3. 检查财务数据获取
    print("\n【3. 财务数据获取检查】")
    await check_financial_data()
    
    # 4. 检查A股指数获取（headbar上的指数）
    print("\n【4. A股指数获取检查】")
    await check_a_stock_indices()
    
    # 5. 检查美股指数获取
    print("\n【5. 美股指数获取检查】")
    await check_us_market_indices()
    
    # 6. 检查数据源可用性
    print("\n【6. 数据源可用性检查】")
    await check_data_sources()
    
    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)


async def check_config():
    """检查配置"""
    try:
        from config.settings import settings
        
        print(f"✓ Tushare Token: {'已配置' if settings.tushare_token else '未配置'}")
        print(f"✓ Alpha Vantage Key: {'已配置' if settings.alphavantage_api_key else '未配置'}")
        print(f"✓ Finnhub Key: {'已配置' if settings.finnhub_api_key else '未配置'}")
        print(f"✓ 美股数据源: {settings.us_stock_data_source}")
        print(f"✓ 数据库路径: {settings.database_url}")
        
        # 检查数据库文件是否存在
        db_path = backend_path / "data" / "stock_peg.db"
        if db_path.exists():
            print(f"✓ 数据库文件存在: {db_path}")
            print(f"  文件大小: {db_path.stat().st_size / 1024 / 1024:.2f} MB")
        else:
            print(f"✗ 数据库文件不存在: {db_path}")
            
    except Exception as e:
        print(f"✗ 配置检查失败: {str(e)}")


async def check_database():
    """检查数据库连接"""
    try:
        from database.session import async_session_maker
        from sqlalchemy import text
        
        async with async_session_maker() as session:
            # 测试连接
            result = await session.execute(text("SELECT 1"))
            print("✓ 数据库连接成功")
            
            # 检查表是否存在
            tables = await session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            table_list = [row[0] for row in tables]
            print(f"✓ 数据库表数量: {len(table_list)}")
            print(f"  主要表: {', '.join(table_list[:10])}")
            
            # 检查财务数据表
            if 'fundamental_metrics' in table_list:
                count_result = await session.execute(text(
                    "SELECT COUNT(*) FROM fundamental_metrics"
                ))
                count = count_result.scalar()
                print(f"✓ 财务数据记录数: {count}")
            
            # 检查美股数据表
            if 'us_daily_data' in table_list:
                count_result = await session.execute(text(
                    "SELECT COUNT(*) FROM us_daily_data"
                ))
                count = count_result.scalar()
                print(f"✓ 美股数据记录数: {count}")
                
                # 检查有哪些美股指数
                indices_result = await session.execute(text(
                    "SELECT DISTINCT symbol FROM us_daily_data"
                ))
                symbols = [row[0] for row in indices_result]
                print(f"  已存储的美股代码: {', '.join(symbols)}")
                
    except Exception as e:
        print(f"✗ 数据库检查失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def check_financial_data():
    """检查财务数据获取"""
    test_stocks = ['600519', '000001', '601318']  # 茅台、平安、平安银行
    
    for stock_code in test_stocks:
        print(f"\n--- 测试股票: {stock_code} ---")
        
        # 1. 尝试从数据库获取
        try:
            from services.fundamental_analyzer import FundamentalAnalyzer
            analyzer = FundamentalAnalyzer()
            
            # 从数据库获取
            metrics = await analyzer.get_metrics_from_db(stock_code)
            if metrics:
                print(f"✓ 数据库有数据: PE={metrics.valuation.get('pe_ttm') if metrics.valuation else 'N/A'}")
            else:
                print(f"✗ 数据库无数据")
            
            # 尝试获取年报数据
            report = await analyzer.get_annual_report_from_db(stock_code)
            if report:
                print(f"✓ 年报数据: 营收={report.get('revenue')}, 净利润={report.get('net_profit')}")
            else:
                print(f"✗ 无年报数据")
                
        except Exception as e:
            print(f"✗ 财务数据获取失败: {str(e)}")
        
        # 2. 尝试从Tushare获取（如果配置了）
        try:
            import tushare as ts
            from config.settings import settings
            
            if settings.tushare_token:
                pro = ts.pro_api(settings.tushare_token)
                
                # 尝试获取财务指标
                print(f"  尝试Tushare获取财务指标...")
                df = pro.daily_basic(ts_code=f"{stock_code}.SH", fields='pe_ttm,pb,roe')
                if not df.empty:
                    print(f"✓ Tushare返回数据: {df.iloc[0].to_dict()}")
                else:
                    print(f"✗ Tushare无数据")
            else:
                print(f"  跳过Tushare测试（未配置Token）")
                
        except Exception as e:
            print(f"✗ Tushare获取失败: {str(e)}")
        
        # 3. 尝试从Akshare获取
        try:
            from services.akshare_service import akshare_service
            
            if akshare_service.available:
                print(f"  尝试Akshare获取财务指标...")
                
                # 获取财务指标
                indicators = await akshare_service.get_financial_indicator(stock_code)
                if indicators:
                    print(f"✓ Akshare返回数据: {indicators}")
                else:
                    print(f"✗ Akshare无数据")
            else:
                print(f"  跳过Akshare测试（不可用）")
                
        except Exception as e:
            print(f"✗ Akshare获取失败: {str(e)}")
        
        # 只测试一只股票
        break


async def check_a_stock_indices():
    """检查A股指数获取（headbar上的指数）"""
    # headbar上的指数：上证指数、深证成指、上证50、创业板指、中证500
    test_indices = [
        ('000001.SH', '上证指数'),
        ('399001.SZ', '深证成指'),
        ('000016.SH', '上证50'),
        ('399006.SZ', '创业板指'),
        ('000905.SH', '中证500'),
    ]
    
    print("\n问题分析:")
    print("从日志看到：腾讯API连续失败触发熔断，Akshare找不到股票")
    print("原因：指数代码格式问题，Akshare需要不带后缀的代码\n")
    
    for code, name in test_indices:
        print(f"\n--- 测试指数: {name} ({code}) ---")
        
        # 1. 从数据库检查
        try:
            from database.session import async_session_maker
            from sqlalchemy import text
            
            async with async_session_maker() as session:
                # 提取纯代码
                pure_code = code.split('.')[0]
                
                # 检查stock_daily表
                result = await session.execute(text(
                    f"SELECT COUNT(*) FROM stock_daily WHERE code = '{pure_code}'"
                ))
                count = result.scalar()
                print(f"✓ 数据库记录数: {count}")
                
        except Exception as e:
            print(f"✗ 数据库检查失败: {str(e)}")
        
        # 2. 尝试Akshare获取（需要纯代码）
        try:
            from services.akshare_service import akshare_service
            
            if akshare_service.available:
                pure_code = code.split('.')[0]
                print(f"  尝试Akshare获取 (纯代码: {pure_code})...")
                
                # Akshare的指数代码格式：sh000001
                market = code.split('.')[1].lower()
                ak_code = f"{market}{pure_code}"
                
                # 获取实时行情
                import akshare as ak
                df = ak.stock_zh_index_spot_em()
                
                # 查找对应指数
                index_data = df[df['代码'] == pure_code]
                if not index_data.empty:
                    row = index_data.iloc[0]
                    print(f"✓ Akshare返回: 最新价={row['最新价']}, 涨跌幅={row['涨跌幅']}")
                else:
                    print(f"✗ Akshare未找到指数")
                    
        except Exception as e:
            print(f"✗ Akshare获取失败: {str(e)}")


async def check_us_market_indices():
    """检查美股指数获取"""
    us_indices = [
        ('^GSPC', '标普500'),
        ('^IXIC', '纳斯达克'),
        ('^DJI', '道琼斯'),
        ('^VIX', 'VIX恐慌指数'),
    ]
    
    print("\n问题分析:")
    print("从日志看到：VIX指数所有数据源都失败，东方财富返回数据格式问题")
    print("可能原因：API key配置问题、数据源限流、证书问题\n")
    
    for symbol, name in us_indices:
        print(f"\n--- 测试美股指数: {name} ({symbol}) ---")
        
        # 1. 从数据库检查
        try:
            from database.session import async_session_maker
            from sqlalchemy import text
            
            async with async_session_maker() as session:
                result = await session.execute(text(
                    f"SELECT COUNT(*) FROM us_daily_data WHERE symbol = '{symbol}'"
                ))
                count = result.scalar()
                
                if count > 0:
                    # 获取最新数据
                    latest = await session.execute(text(
                        f"SELECT * FROM us_daily_data WHERE symbol = '{symbol}' "
                        f"ORDER BY trade_date DESC LIMIT 1"
                    ))
                    row = latest.fetchone()
                    if row:
                        print(f"✓ 数据库有数据: 最新价={row.close_price}, 涨跌幅={row.change_pct}")
                else:
                    print(f"✗ 数据库无数据")
                    
        except Exception as e:
            print(f"✗ 数据库检查失败: {str(e)}")
        
        # 2. 尝试东方财富获取
        if symbol in ['^GSPC', '^IXIC', '^DJI', '^VIX']:
            try:
                from services.us_market_analyzer import USMarketDataService
                us_service = USMarketDataService()
                
                print(f"  尝试东方财富获取...")
                data = await us_service._get_from_eastmoney(symbol)
                if data:
                    print(f"✓ 东方财富返回: {data}")
                else:
                    print(f"✗ 东方财富无数据")
                    
            except Exception as e:
                print(f"✗ 东方财富获取失败: {str(e)}")
        
        # 3. 尝试Yahoo Finance获取
        try:
            from services.us_market_analyzer import USMarketDataService
            us_service = USMarketDataService()
            
            print(f"  尝试Yahoo Finance获取...")
            data = await us_service._get_from_yfinance(symbol, "1mo")
            if data:
                print(f"✓ Yahoo返回: {data}")
            else:
                print(f"✗ Yahoo无数据")
                
        except Exception as e:
            print(f"✗ Yahoo获取失败: {str(e)}")


async def check_data_sources():
    """检查数据源可用性"""
    print("\n--- 检查各数据源状态 ---")
    
    # 1. Tushare
    try:
        import tushare as ts
        from config.settings import settings
        
        if settings.tushare_token:
            pro = ts.pro_api(settings.tushare_token)
            # 测试接口
            df = pro.trade_calendar(exchange='SSE', start_date='20260101', end_date='20260110')
            print(f"✓ Tushare: 可用（返回{len(df)}条数据）")
        else:
            print(f"✗ Tushare: 未配置Token")
            
    except Exception as e:
        print(f"✗ Tushare: 不可用 - {str(e)}")
    
    # 2. Akshare
    try:
        from services.akshare_service import akshare_service
        
        if akshare_service.available:
            import akshare as ak
            # 测试接口
            df = ak.stock_zh_a_spot_em()
            print(f"✓ Akshare: 可用（返回{len(df)}条A股数据）")
        else:
            print(f"✗ Akshare: 不可用")
            
    except Exception as e:
        print(f"✗ Akshare: 不可用 - {str(e)}")
    
    # 3. 东方财富（美股）
    try:
        import httpx
        client = httpx.AsyncClient(timeout=10.0)
        
        url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
        params = {
            "fltt": 2,
            "invt": 2,
            "fields": "f2,f3,f12,f14",
            "secids": "100.SPX"
        }
        
        response = await client.get(url, params=params)
        data = response.json()
        
        if data and 'data' in data:
            print(f"✓ 东方财富(美股): 可用")
        else:
            print(f"✗ 东方财富(美股): 返回数据异常")
            
    except Exception as e:
        print(f"✗ 东方财富(美股): 不可用 - {str(e)}")
    
    # 4. Alpha Vantage
    try:
        from config.settings import settings
        
        if settings.alphavantage_api_key:
            import httpx
            client = httpx.AsyncClient(timeout=10.0)
            
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": "IBM",
                "apikey": settings.alphavantage_api_key
            }
            
            response = await client.get(url, params=params)
            data = response.json()
            
            if 'Global Quote' in data:
                print(f"✓ Alpha Vantage: 可用")
            elif 'Note' in data:
                print(f"⚠ Alpha Vantage: API调用频率限制")
            else:
                print(f"✗ Alpha Vantage: 返回数据异常")
        else:
            print(f"✗ Alpha Vantage: 未配置API Key")
            
    except Exception as e:
        print(f"✗ Alpha Vantage: 不可用 - {str(e)}")
    
    # 5. Finnhub
    try:
        from config.settings import settings
        
        if settings.finnhub_api_key:
            import httpx
            client = httpx.AsyncClient(timeout=10.0)
            
            url = "https://finnhub.io/api/v1/quote"
            params = {
                "symbol": "AAPL",
                "token": settings.finnhub_api_key
            }
            
            response = await client.get(url, params=params)
            data = response.json()
            
            if 'c' in data and data['c'] > 0:
                print(f"✓ Finnhub: 可用")
            else:
                print(f"✗ Finnhub: 返回数据异常")
        else:
            print(f"✗ Finnhub: 未配置API Key")
            
    except Exception as e:
        print(f"✗ Finnhub: 不可用 - {str(e)}")


if __name__ == "__main__":
    asyncio.run(diagnose())
