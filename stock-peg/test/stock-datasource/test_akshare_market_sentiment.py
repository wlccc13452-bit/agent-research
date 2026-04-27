"""测试AKShare市场情绪数据源"""
import asyncio
import sys
from datetime import datetime
import pandas as pd

# 添加backend到路径
sys.path.insert(0, 'd:\\2026projects\\stocks-research\\stock-peg\\backend')

try:
    import akshare as ak
    print(f"[OK] AKShare 版本: {ak.__version__}")
except ImportError:
    print("[FAIL] AKShare 未安装")
    sys.exit(1)

async def test_dongfang_caifu():
    """测试东方财富数据源"""
    print("\n" + "=" * 60)
    print("[1] 测试东方财富数据源 (stock_zh_a_spot_em)")
    print("=" * 60)
    
    try:
        print("正在获取数据...")
        df = ak.stock_zh_a_spot_em()
        
        if df.empty:
            print("[WARN] 返回空数据")
            return None
        
        print(f"[OK] 成功获取数据: {len(df)} 行")
        print(f"列名: {list(df.columns)}")
        
        # 检查是否有涨跌幅列
        if '涨跌幅' in df.columns:
            print("\n[OK] 包含涨跌幅数据")
            
            # 过滤有效股票代码
            df_filtered = df[df['代码'].astype(str).str.fullmatch(r'\d{6}', na=False)]
            print(f"有效股票数: {len(df_filtered)}")
            
            # 提取涨跌幅
            change_pct = pd.to_numeric(df_filtered['涨跌幅'], errors='coerce')
            valid_change_pct = change_pct.dropna()
            
            if not valid_change_pct.empty:
                total_count = len(valid_change_pct)
                up_count = int((valid_change_pct > 0).sum())
                down_count = int((valid_change_pct < 0).sum())
                flat_count = int((valid_change_pct == 0).sum())
                limit_up = int((valid_change_pct >= 9.9).sum())
                limit_down = int((valid_change_pct <= -9.9).sum())
                market_breadth = (up_count / total_count * 100) if total_count > 0 else 0
                avg_change_pct = valid_change_pct.mean()
                
                print(f"\n市场情绪统计:")
                print(f"  总股票数: {total_count}")
                print(f"  上涨家数: {up_count}")
                print(f"  下跌家数: {down_count}")
                print(f"  平盘家数: {flat_count}")
                print(f"  涨停家数: {limit_up}")
                print(f"  跌停家数: {limit_down}")
                print(f"  市场宽度: {market_breadth:.2f}%")
                print(f"  平均涨跌幅: {avg_change_pct:.2f}%")
                
                return {
                    'total_count': total_count,
                    'up_count': up_count,
                    'down_count': down_count,
                    'limit_up': limit_up,
                    'limit_down': limit_down,
                    'market_breadth': round(market_breadth, 2),
                    'data_quality': 'full' if total_count >= 5000 else 'partial',
                    'data_source': '东方财富'
                }
            else:
                print("[WARN] 无有效涨跌幅数据")
                return None
        else:
            print(f"[WARN] 缺少涨跌幅列")
            print(f"可用列: {list(df.columns)}")
            return None
            
    except Exception as e:
        print(f"[FAIL] 东方财富接口失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def test_tencent_finance():
    """测试腾讯财经数据源"""
    print("\n" + "=" * 60)
    print("[2] 测试腾讯财经数据源 (stock_zh_a_spot)")
    print("=" * 60)
    
    try:
        print("正在获取数据...")
        df = ak.stock_zh_a_spot()
        
        if df.empty:
            print("[WARN] 返回空数据")
            return None
        
        print(f"[OK] 成功获取数据: {len(df)} 行")
        print(f"列名: {list(df.columns)}")
        
        # 检查是否有涨跌幅列
        if '涨跌幅' in df.columns:
            print("\n[OK] 包含涨跌幅数据")
            
            # 过滤有效股票代码
            df_filtered = df[df['代码'].astype(str).str.fullmatch(r'\d{6}', na=False)]
            print(f"有效股票数: {len(df_filtered)}")
            
            # 提取涨跌幅
            change_pct = pd.to_numeric(df_filtered['涨跌幅'], errors='coerce')
            valid_change_pct = change_pct.dropna()
            
            if not valid_change_pct.empty:
                total_count = len(valid_change_pct)
                up_count = int((valid_change_pct > 0).sum())
                down_count = int((valid_change_pct < 0).sum())
                flat_count = int((valid_change_pct == 0).sum())
                limit_up = int((valid_change_pct >= 9.9).sum())
                limit_down = int((valid_change_pct <= -9.9).sum())
                market_breadth = (up_count / total_count * 100) if total_count > 0 else 0
                avg_change_pct = valid_change_pct.mean()
                
                print(f"\n市场情绪统计:")
                print(f"  总股票数: {total_count}")
                print(f"  上涨家数: {up_count}")
                print(f"  下跌家数: {down_count}")
                print(f"  平盘家数: {flat_count}")
                print(f"  涨停家数: {limit_up}")
                print(f"  跌停家数: {limit_down}")
                print(f"  市场宽度: {market_breadth:.2f}%")
                print(f"  平均涨跌幅: {avg_change_pct:.2f}%")
                
                return {
                    'total_count': total_count,
                    'up_count': up_count,
                    'down_count': down_count,
                    'limit_up': limit_up,
                    'limit_down': limit_down,
                    'market_breadth': round(market_breadth, 2),
                    'data_quality': 'full' if total_count >= 5000 else 'partial',
                    'data_source': '腾讯财经'
                }
            else:
                print("[WARN] 无有效涨跌幅数据")
                return None
        else:
            print(f"[WARN] 缺少涨跌幅列")
            print(f"可用列: {list(df.columns)}")
            return None
            
    except Exception as e:
        print(f"[FAIL] 腾讯财经接口失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    print("=" * 60)
    print("AKShare 市场情绪数据源测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 测试东方财富
    result1 = await test_dongfang_caifu()
    
    # 测试腾讯财经
    result2 = await test_tencent_finance()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if result1:
        print(f"\n[OK] 东方财富: 可用 (获取{result1['total_count']}只股票)")
    else:
        print(f"\n[FAIL] 东方财富: 不可用")
    
    if result2:
        print(f"[OK] 腾讯财经: 可用 (获取{result2['total_count']}只股票)")
    else:
        print(f"[FAIL] 腾讯财经: 不可用")
    
    print("\n结论:")
    if result1 or result2:
        print("AKShare 可以获取市场情绪数据")
        if result1 and result1.get('data_quality') == 'full':
            print("[OK] 数据质量: 完整 (>=5000只股票)")
        elif result2 and result2.get('data_quality') == 'full':
            print("[OK] 数据质量: 完整 (>=5000只股票)")
        else:
            print("[WARN] 数据质量: 部分数据 (<5000只股票)")
    else:
        print("AKShare 当前无法获取市场情绪数据")
        print("可能原因:")
        print("  1. 非交易时间（周末、节假日）")
        print("  2. 网络连接问题")
        print("  3. API服务限制")

if __name__ == "__main__":
    asyncio.run(main())
