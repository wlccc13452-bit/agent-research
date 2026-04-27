"""
测试网络连接和证书

检查：
1. 基本网络连接
2. DNS 解析
3. HTTPS 连接
4. 证书验证
"""
import os
import sys
import ssl
import socket
import urllib.request
from urllib.error import URLError, HTTPError

# 设置 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 60)
print("网络连接诊断")
print("=" * 60)

# 1. 测试基本网络连接
print("\n[测试1] 基本网络连接...")
try:
    socket.create_connection(("www.baidu.com", 80), timeout=5)
    print("  ✓ 可以连接到 baidu.com:80")
except Exception as e:
    print(f"  ✗ 连接失败: {str(e)}")

# 2. 测试 DNS 解析
print("\n[测试2] DNS 解析...")
try:
    ip = socket.gethostbyname("82.push2.eastmoney.com")
    print(f"  ✓ eastmoney.com 解析成功: {ip}")
except Exception as e:
    print(f"  ✗ DNS 解析失败: {str(e)}")

# 3. 测试 HTTPS 连接（不验证证书）
print("\n[测试3] HTTPS 连接（不验证证书）...")
try:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    with urllib.request.urlopen("https://www.baidu.com", timeout=10, context=context) as response:
        print(f"  ✓ HTTPS 连接成功 (状态码: {response.status})")
except Exception as e:
    print(f"  ✗ HTTPS 连接失败: {str(e)}")

# 4. 测试东方财富 API（不验证证书）
print("\n[测试4] 东方财富 API 连接（不验证证书）...")
test_url = "https://quote.eastmoney.com/"
try:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    with urllib.request.urlopen(test_url, timeout=10, context=context) as response:
        print(f"  ✓ 连接成功 (状态码: {response.status})")
        print(f"  URL: {test_url}")
except Exception as e:
    print(f"  ✗ 连接失败: {str(e)}")

# 5. 测试 requests 库（不验证证书）
print("\n[测试5] requests 库测试（不验证证书）...")
try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    import warnings
    warnings.simplefilter('ignore', InsecureRequestWarning)
    
    response = requests.get(
        "https://quote.eastmoney.com/",
        timeout=10,
        verify=False,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    print(f"  ✓ requests 连接成功 (状态码: {response.status_code})")
except Exception as e:
    print(f"  ✗ requests 连接失败: {str(e)}")

# 6. 测试 AKShare（不验证证书）
print("\n[测试6] AKShare 测试（不验证证书）...")
try:
    import akshare as ak
    
    # 临时禁用证书验证
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 获取少量数据测试
    print("  正在获取股票列表...")
    df = ak.stock_info_a_code_name()
    
    if df is not None and not df.empty:
        print(f"  ✓ AKShare 连接成功！")
        print(f"  获取到 {len(df)} 只股票")
    else:
        print("  ✗ 未获取到数据")
        
except Exception as e:
    print(f"  ✗ AKShare 失败: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)

print("\n如果测试6失败，说明问题可能是：")
print("1. 东方财富 API 限流（请求过于频繁）")
print("2. IP 被临时封禁")
print("3. 网络环境限制（防火墙/企业网络）")
print("\n解决方案：")
print("- 等待一段时间后重试")
print("- 使用其他数据源（Tushare）")
print("- 联系网络管理员检查防火墙设置")
