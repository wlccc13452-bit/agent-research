"""
测试 AKShare 的其他实时行情接口

目标：找到一个可以工作的接口来获取全市场涨跌数据
"""
import os
import sys

# 设置 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 禁用证书验证警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 清除代理环境变量
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(var, None)
os.environ['NO_PROXY'] = '*'

print("=" * 60)
print("测试 AKShare 实时行情接口")
print("=" * 60)

import akshare as ak
import pandas as pd
from datetime import datetime

# 测试不同的接口
test_functions = [
    # 1. stock_zh_a_spot_em - 东方财富全市场行情
    {
        'name': 'stock_zh_a_spot_em',
        'function': ak.stock_zh_a_spot_em,
        'description': '东方财富全市场实时行情'
    },
    # 2. stock_zh_a_spot - 腾讯财经全市场行情
    {
        'name': 'stock_zh_a_spot',
        'function': lambda: ak.stock_zh_a_spot(),
        'description': '腾讯财经全市场实时行情'
    },
    # 3. stock_zh_a_hist_min_em - 东方财富分钟行情（获取单只股票测试）
    {
        'name': 'stock_zh_a_hist_min_em (single)',
        'function': lambda: ak.stock_zh_a_hist_min_em(symbol="000001", period="1", adjust=""),
        'description': '东方财富分钟行情（单只股票测试）'
    },
]

results = []

for test in test_functions:
    print(f"\n[测试] {test['description']}")
    print(f"  函数: {test['name']}")
    
    try:
        start_time = datetime.now()
        df = test['function']()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if df is not None and not df.empty:
            print(f"  ✓ 成功！耗时: {elapsed:.2f}秒")
            print(f"  数据形状: {df.shape}")
            print(f"  列名: {list(df.columns)[:5]}...")
            
            # 统计股票数量
            if '代码' in df.columns:
                total = len(df)
                print(f"  股票数量: {total}")
                
                # 检查是否有涨跌幅数据
                if '涨跌幅' in df.columns:
                    change_pct = pd.to_numeric(df['涨跌幅'], errors='coerce').dropna()
                    up = (change_pct > 0).sum()
                    down = (change_pct < 0).sum()
                    print(f"  上涨: {up}, 下跌: {down}")
                    
                    if total >= 4500:
                        print(f"  ✓✓✓ 数据完整！")
                        results.append({
                            'name': test['name'],
                            'status': 'success',
                            'total': total,
                            'up': up,
                            'down': down
                        })
        else:
            print(f"  ✗ 未获取到数据")
            
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"  ✗ 失败: {type(e).__name__}: {str(e)[:100]}")
        results.append({
            'name': test['name'],
            'status': 'failed',
            'error': str(e)[:100]
        })
    
    # 短暂延迟，避免请求过快
    import time
    time.sleep(1)

print("\n" + "=" * 60)
print("测试结果汇总")
print("=" * 60)

successful = [r for r in results if r.get('status') == 'success']
if successful:
    print(f"\n✓ 成功的接口: {len(successful)}")
    for r in successful:
        print(f"  - {r['name']}: {r.get('total', 'N/A')} 只股票")
else:
    print(f"\n✗ 所有接口均失败")

print("\n建议：")
if not successful:
    print("1. 检查网络连接")
    print("2. 等待一段时间后重试（可能被限流）")
    print("3. 使用 Tushare 作为替代数据源")
    print("4. 考虑使用本地缓存的股票列表 + 单只股票查询")
else:
    print(f"✓ 可以使用 '{successful[0]['name']}' 接口")
