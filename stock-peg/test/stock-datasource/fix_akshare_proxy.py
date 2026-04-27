"""
彻底修复 AKShare 代理问题 - 强制版本

此脚本会：
1. 完全清除所有代理相关环境变量
2. 强制禁用 requests 的代理功能
3. 测试 AKShare 连接
"""
import os
import sys

# 设置 UTF-8 编码（Windows）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 60)
print("强制禁用代理并测试 AKShare 连接")
print("=" * 60)

# 步骤1: 清除所有代理相关环境变量
proxy_vars = [
    'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
    'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy',
    'FTP_PROXY', 'ftp_proxy', 'SOCKS_PROXY', 'socks_proxy',
    'ALL_PROXY', 'all_proxy'
]

print("\n步骤1: 清除代理环境变量...")
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]
        print(f"  已清除: {var}")

# 步骤2: 设置 NO_PROXY 为 *（禁用所有代理）
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
print("\n步骤2: 设置 NO_PROXY='*'")

# 步骤3: 强制禁用 requests 的代理功能
print("\n步骤3: 禁用 requests 代理功能...")
try:
    import requests
    # 方法1: 设置 trust_env = False
    requests.sessions.Session.trust_env = False
    print("  ✓ requests.sessions.Session.trust_env = False")
    
    # 方法2: 猴子补丁 - 强制禁用代理
    original_init = requests.Session.__init__
    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.trust_env = False
        self.proxies = {}
    requests.Session.__init__ = patched_init
    print("  ✓ requests.Session 已打补丁")
    
except Exception as e:
    print(f"  ✗ 禁用 requests 代理失败: {str(e)}")

# 步骤4: 测试 AKShare 连接
print("\n步骤4: 测试 AKShare 连接...")
try:
    import akshare as ak
    import pandas as pd
    from datetime import datetime
    
    print(f"  AKShare 版本: {ak.__version__}")
    
    # 尝试获取市场数据
    print("\n  正在调用 ak.stock_zh_a_spot_em()...")
    start_time = datetime.now()
    
    df = ak.stock_zh_a_spot_em()
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"  请求耗时: {elapsed:.2f}秒")
    
    if df is not None and not df.empty:
        # 统计股票数量
        if '代码' in df.columns:
            valid_stocks = df[df['代码'].astype(str).str.fullmatch(r'\d{6}', na=False)]
            total = len(valid_stocks)
            
            print(f"\n✓ 成功获取数据!")
            print(f"  总股票数: {total}")
            
            # 统计涨跌
            if '涨跌幅' in valid_stocks.columns:
                change_pct = pd.to_numeric(valid_stocks['涨跌幅'], errors='coerce').dropna()
                up = (change_pct > 0).sum()
                down = (change_pct < 0).sum()
                flat = (change_pct == 0).sum()
                limit_up = (change_pct >= 9.9).sum()
                limit_down = (change_pct <= -9.9).sum()
                
                print(f"  上涨: {up}")
                print(f"  下跌: {down}")
                print(f"  平盘: {flat}")
                print(f"  涨停: {limit_up}")
                print(f"  跌停: {limit_down}")
                print(f"  市场宽度: {(up/total*100):.2f}%")
                print(f"  平均涨跌: {change_pct.mean():.2f}%")
                
                if total >= 4500:
                    print(f"\n✓✓✓ 数据完整！({total} >= 4500)")
                else:
                    print(f"\n⚠ 数据不完整 ({total} < 4500)")
        else:
            print("\n✗ 数据格式异常（缺少'代码'列）")
    else:
        print("\n✗ 未获取到数据")
        
except Exception as e:
    print(f"\n✗✗✗ 获取数据失败!")
    print(f"  错误类型: {type(e).__name__}")
    print(f"  错误信息: {str(e)}")
    
    # 提供详细的修复建议
    print("\n" + "=" * 60)
    print("修复建议:")
    print("=" * 60)
    print("1. 检查网络连接是否正常")
    print("2. 尝试使用 VPN 或切换网络环境")
    print("3. 检查防火墙是否阻止了 Python 访问网络")
    print("4. 尝试在浏览器中访问: https://quote.eastmoney.com/center/")
    print("5. 如果浏览器能访问但 Python 不能，可能是证书问题")
    print("\n如果以上都无法解决，考虑使用 Tushare 作为数据源")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
