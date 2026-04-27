import asyncio
import sys
import os
import json
from datetime import datetime

# 将 backend 目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from services.fundamental_analyzer import FundamentalAnalyzer

async def debug_stock(stock_code):
    print(f"\n{'='*20} Debugging Stock: {stock_code} {'='*20}")
    analyzer = FundamentalAnalyzer()
    
    # 1. 测试 analyze_valuation
    print(f"--- Calling analyze_valuation('{stock_code}') ---")
    valuation = await analyzer.analyze_valuation(stock_code)
    print(f"Valuation Result: {json.dumps(valuation, indent=2, default=str)}")
    
    # 2. 测试 analyze_financial_health
    print(f"\n--- Calling analyze_financial_health('{stock_code}') ---")
    health = await analyzer.analyze_financial_health(stock_code)
    print(f"Financial Health Result: {json.dumps(health, indent=2, default=str)}")
    
    # 3. 测试 analyze_fundamental (综合分析)
    print(f"\n--- Calling analyze_fundamental('{stock_code}') ---")
    fundamental = await analyzer.analyze_fundamental(stock_code)
    if fundamental:
        print(f"Fundamental Analysis Result: {json.dumps(fundamental, indent=2, default=str)}")
        print(f"Fundamental Analysis Summary:")
        print(f"  PE (TTM): {fundamental.get('valuation', {}).get('pe_ttm')}")
        print(f"  PB: {fundamental.get('valuation', {}).get('pb')}")
        print(f"  PS (TTM): {fundamental.get('valuation', {}).get('ps_ttm')}")
        print(f"  PEG: {fundamental.get('valuation', {}).get('peg')}")
        # ROE 可能在 growth 中
        roe = fundamental.get('growth', {}).get('roe') or fundamental.get('financial_health', {}).get('roe')
        print(f"  ROE: {roe}")
        print(f"  Debt Ratio: {fundamental.get('financial_health', {}).get('debt_ratio')}")
    else:
        print("Fundamental analysis failed.")

async def debug_akshare_sina(stock_code):
    from services.akshare_service import akshare_service
    print(f"\n--- Debugging Akshare Sina for {stock_code} ---")
    
    # 1. 资产负债表
    balance = await akshare_service.get_financial_report_sina(stock_code, '资产负债表')
    if balance and 'data' in balance and not balance['data'].empty:
        print(f"Balance Sheet Columns: {balance['data'].columns.tolist()}")
        print(f"First row: {balance['data'].iloc[0].to_dict()}")
    else:
        print("Balance sheet not found.")
        
    # 2. 利润表
    income = await akshare_service.get_financial_report_sina(stock_code, '利润表')
    if income and 'data' in income and not income['data'].empty:
        print(f"Income Statement Columns: {income['data'].columns.tolist()}")
        print(f"Recent Profits: {income['data']['净利润'].head(5).tolist()}")
        print(f"Recent Revenues: {income['data']['营业总收入'].head(5).tolist()}")
    else:
        print("Income statement not found.")

async def main():
    test_stocks = ['600519']
    for stock in test_stocks:
        await debug_akshare_sina(stock)
        await debug_stock(stock)

if __name__ == "__main__":
    asyncio.run(main())
