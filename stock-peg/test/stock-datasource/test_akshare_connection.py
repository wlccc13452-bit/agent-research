"""
AKShare 连接测试和修复脚本

用途：
1. 测试 AKShare API 连接状态
2. 检查网络环境
3. 提供修复建议
"""
import asyncio
import sys
import os

# 设置 UTF-8 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加 backend 目录到 Python 路径
backend_path = os.path.dirname(__file__)
sys.path.insert(0, backend_path)

async def test_akshare_connection():
    """测试 AKShare 连接"""
    print("=" * 60)
    print("AKShare 连接测试")
    print("=" * 60)
    
    # 1. 检查 AKShare 是否安装
    try:
        import akshare as ak
        print(f"[OK] AKShare 已安装，版本: {ak.__version__}")
    except ImportError:
        print("[FAIL] AKShare 未安装")
        print("\n安装方法: pip install akshare")
        return
    
    # 2. 测试市场情绪数据接口
    print("\n测试 stock_zh_a_spot_em 接口...")
    try:
        import pandas as pd
        df = ak.stock_zh_a_spot_em()
        
        if df is not None and not df.empty:
            # 统计股票数量
            if '代码' in df.columns:
                valid_stocks = df[df['代码'].astype(str).str.fullmatch(r'\d{6}', na=False)]
                total = len(valid_stocks)
                print(f"[OK] 成功获取全市场数据")
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
                    
                    if total >= 4500:
                        print("\n[OK] 数据完整（>= 4500只股票）")
                    else:
                        print(f"\n[WARN] 数据可能不完整（< 4500只股票）")
            else:
                print("[FAIL] 返回数据格式异常")
        else:
            print("[FAIL] 未获取到数据")
            
    except Exception as e:
        print(f"[FAIL] 获取数据失败: {str(e)}")
        print("\n可能的原因：")
        print("  1. 网络连接问题")
        print("  2. AKShare API 服务器暂时不可用")
        print("  3. 被限流（请求过于频繁）")
        print("\n建议：")
        print("  1. 检查网络连接")
        print("  2. 稍后重试")
        print("  3. 考虑使用代理（如果有网络限制）")
        print("  4. 升级 AKShare: pip install --upgrade akshare")

if __name__ == "__main__":
    asyncio.run(test_akshare_connection())
