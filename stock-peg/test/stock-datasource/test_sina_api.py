"""
测试新浪财经API - 通常更稳定

新浪财经的行情数据API通常比腾讯和东方财富更稳定
"""
import requests
import json
import sys
import os
from datetime import datetime

# 设置 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 60)
print("测试新浪财经API")
print("=" * 60)

# 新浪财经实时行情API
sina_api_url = "http://hq.sinajs.cn/list=sh600000,sz000001"

try:
    print("\n[1] 测试新浪财经API...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://finance.sina.com.cn/'
    }
    
    response = requests.get(sina_api_url, headers=headers, timeout=10)
    print(f"  状态码: {response.status_code}")
    print(f"  响应长度: {len(response.text)}")
    
    if response.status_code == 200:
        # 解析数据
        data = response.text.split(';')
        stocks = []
        
        for item in data:
            if not item.strip():
                continue
            
            fields = item.split(',')
            if len(fields) >= 32:
                code = fields[0]
                name = fields[1]
                price = float(fields[3]) if fields[3] else 0
                change_pct = float(fields[32]) if len(fields) > 32 and fields[32] else 0
                
                stocks.append({
                    'code': code,
                    'name': name,
                    'price': price,
                    'change_pct': change_pct
                })
        
        print(f"  ✓ 解析成功: {len(stocks)} 只股票")
        for stock in stocks[:3]:
            print(f"    - {stock['code']} {stock['name']}: {stock['price']} ({stock['change_pct']}%)")
            
except Exception as e:
    print(f"  ✗ 失败: {str(e)}")

# 测试全量股票列表（使用其他API）
print("\n[2] 测试获取完整股票列表...")

# 尝试使用东方财富的行情中心页面数据
try:
    import urllib.request
    import ssl
    
    # 创建一个不验证证书的上下文
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    # 东方财富行情中心URL
    em_url = "https://quote.eastmoney.com/center/gridlist.html"
    
    req = urllib.request.Request(em_url)
    response = urllib.request.urlopen(req, timeout=10, context=context)
    
    print(f"  状态码: {response.status}")
    print(f"  响应长度: {len(response.read())}")
    print(f"  ✓ 可以访问东方财富网站")
    
except Exception as e:
    print(f"  ✗ 失败: {str(e)}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)

print("\n建议:")
print("1. 如果所有API都失败，可能是网络环境限制（防火墙/企业网络）")
print("2. 考虑在交易时间测试（9:30-15:00）")
print("3. 使用VPN或切换网络环境")
print("4. 配置Tushare作为主要数据源")
