"""测试Tushare daily接口"""
import asyncio
import sys
from datetime import datetime
from config.settings import settings
from services.data_sources.tushare_source import TushareDataSource

async def main():
    print("=" * 60)
    print("测试 Tushare daily 接口")
    print("=" * 60)
    
    if not settings.tushare_token:
        print("[FAIL] Tushare Token 未配置")
        return
    
    print(f"[OK] Token: {settings.tushare_token[:20]}...")
    
    tushare = TushareDataSource(settings.tushare_token)
    
    # 测试daily接口
    today = datetime.now().strftime('%Y%m%d')
    print(f"\n当前日期: {today} ({datetime.now().strftime('%A')})")
    
    print("\n[1] 尝试获取今天的daily数据...")
    try:
        df = tushare._call_tushare_api(
            'daily',
            trade_date=today,
            start_date=today,
            end_date=today
        )
        
        if df.empty:
            print(f"[WARN] daily接口返回空数据（可能是非交易日）")
        else:
            print(f"[OK] daily接口成功: {len(df)} 只股票")
            print(f"列名: {list(df.columns)}")
            print(f"\n前5行数据:")
            print(df.head())
            
            # 计算涨跌
            df['change_pct'] = ((df['close'] - df['pre_close']) / df['pre_close'] * 100).round(2)
            print(f"\n涨跌统计:")
            print(f"  上涨: {(df['change_pct'] > 0).sum()}")
            print(f"  下跌: {(df['change_pct'] < 0).sum()}")
            print(f"  涨停: {(df['change_pct'] >= 9.9).sum()}")
            print(f"  跌停: {(df['change_pct'] <= -9.9).sum()}")
    except Exception as e:
        print(f"[FAIL] daily接口失败: {str(e)}")
    
    # 测试最近几个交易日
    print("\n[2] 尝试获取最近3个交易日的数据...")
    for i in range(1, 8):
        date = (datetime.now() - __import__('datetime').timedelta(days=i)).strftime('%Y%m%d')
        try:
            df = tushare._call_tushare_api(
                'daily',
                trade_date=date,
                start_date=date,
                end_date=date
            )
            
            if not df.empty:
                print(f"[OK] {date}: {len(df)} 只股票")
                
                # 计算涨跌
                df['change_pct'] = ((df['close'] - df['pre_close']) / df['pre_close'] * 100).round(2)
                up = (df['change_pct'] > 0).sum()
                down = (df['change_pct'] < 0).sum()
                limit_up = (df['change_pct'] >= 9.9).sum()
                limit_down = (df['change_pct'] <= -9.9).sum()
                
                print(f"     上涨:{up} 下跌:{down} 涨停:{limit_up} 跌停:{limit_down}")
                break
            else:
                print(f"[WARN] {date}: 无数据（可能非交易日）")
        except Exception as e:
            print(f"[FAIL] {date}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
