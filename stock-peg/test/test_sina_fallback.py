
import asyncio
import logging
import sys
import os

# 添加 backend 目录到 path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from services.akshare_service import akshare_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sina_fallback(stock_code):
    print(f"\n--- Testing Sina Finance fallback for {stock_code} ---")
    
    reports = ['资产负债表', '利润表', '现金流量表']
    for report_type in reports:
        print(f"Fetching {report_type}...")
        try:
            result = await akshare_service.get_financial_report_sina(stock_code, report_type)
            if result and result.get('data') is not None:
                df = result['data']
                print(f"SUCCESS: Found {len(df)} records for {report_type}")
                # print(df.head(2))
            else:
                print(f"FAILED: No data found for {report_type}")
        except Exception as e:
            print(f"ERROR: Failed to fetch {report_type}: {str(e)}")

async def main():
    # 测试几个不同市场的股票
    test_stocks = ['600519', '000858', '300750'] # 贵州茅台, 五粮液, 宁德时代
    for stock in test_stocks:
        await test_sina_fallback(stock)

if __name__ == "__main__":
    asyncio.run(main())
