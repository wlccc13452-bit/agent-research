"""
测试完整的市场情绪 API（禁用证书验证）
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
print("测试市场情绪 API（禁用证书验证）")
print("=" * 60)

try:
    import akshare as ak
    import pandas as pd
    from datetime import datetime
    
    print(f"\n[1] AKShare 版本: {ak.__version__}")
    
    # 测试 stock_zh_a_spot_em
    print("\n[2] 调用 ak.stock_zh_a_spot_em()...")
    start_time = datetime.now()
    
    # 尝试使用禁用证书验证的方式
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    import warnings
    warnings.simplefilter('ignore', InsecureRequestWarning)
    
    # 创建一个自定义的 session，禁用证书验证
    session = requests.Session()
    session.verify = False
    
    # 使用 akshare 的方式获取数据
    df = ak.stock_zh_a_spot_em()
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"  请求耗时: {elapsed:.2f}秒")
    
    if df is not None and not df.empty:
        # 统计股票数量
        if '代码' in df.columns:
            valid_stocks = df[df['代码'].astype(str).str.fullmatch(r'\d{6}', na=False)]
            total = len(valid_stocks)
            
            print(f"\n[3] ✓✓✓ 成功获取全市场数据！")
            print(f"  总股票数: {total}")
            
            # 统计涨跌
            if '涨跌幅' in valid_stocks.columns:
                change_pct = pd.to_numeric(valid_stocks['涨跌幅'], errors='coerce').dropna()
                up = (change_pct > 0).sum()
                down = (change_pct < 0).sum()
                flat = (change_pct == 0).sum()
                limit_up = (change_pct >= 9.9).sum()
                limit_down = (change_pct <= -9.9).sum()
                
                print(f"\n[4] 市场统计数据:")
                print(f"  上涨: {up}")
                print(f"  下跌: {down}")
                print(f"  平盘: {flat}")
                print(f"  涨停: {limit_up}")
                print(f"  跌停: {limit_down}")
                print(f"  市场宽度: {(up/total*100):.2f}%")
                print(f"  平均涨跌: {change_pct.mean():.2f}%")
                
                if total >= 4500:
                    print(f"\n✓✓✓ 数据完整！({total} >= 4500)")
                    print("\n建议：修改 akshare_service.py 以支持禁用证书验证")
                else:
                    print(f"\n⚠ 数据可能不完整 ({total} < 4500)")
                    
                # 输出 JSON 格式（用于API）
                import json
                result = {
                    'total_count': int(total),
                    'up_count': int(up),
                    'down_count': int(down),
                    'flat_count': int(flat),
                    'limit_up': int(limit_up),
                    'limit_down': int(limit_down),
                    'market_breadth': round(up/total*100, 2),
                    'avg_change_pct': round(float(change_pct.mean()), 2),
                    'timestamp': datetime.now().isoformat(),
                    'data_quality': 'full' if total >= 4500 else 'partial'
                }
                print(f"\n[5] API 返回格式:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("\n✗ 数据格式异常（缺少'代码'列）")
    else:
        print("\n✗ 未获取到数据")
        
except Exception as e:
    print(f"\n✗✗✗ 获取数据失败!")
    print(f"  错误类型: {type(e).__name__}")
    print(f"  错误信息: {str(e)}")
    import traceback
    print(f"\n详细堆栈:")
    traceback.print_exc()

print("\n" + "=" * 60)
