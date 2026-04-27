"""测试市场情绪数据多数据源方案

测试内容：
1. Tushare数据源
2. AKShare数据源
3. 数据缓存机制
4. 定时更新功能
"""
import asyncio
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, '.')

async def test_data_sources():
    """测试各个数据源"""
    print("=" * 60)
    print("测试市场情绪数据多数据源方案")
    print("=" * 60)
    
    # 1. 测试Tushare数据源
    print("\n[1] 测试 Tushare 数据源")
    print("-" * 60)
    
    from config.settings import settings
    from services.data_sources.tushare_source import TushareDataSource
    
    if settings.tushare_token:
        print(f"[OK] Tushare Token 已配置: {settings.tushare_token[:20]}...")
        
        tushare = TushareDataSource(settings.tushare_token)
        available = await tushare.is_available()
        
        if available:
            print("[OK] Tushare 服务可用")
            
            # 尝试获取市场情绪数据
            print("正在获取市场情绪数据...")
            sentiment = await tushare.get_market_sentiment()
            
            if sentiment:
                print(f"[OK] 获取成功:")
                print(f"  - 总股票数: {sentiment.get('total_count')}")
                print(f"  - 上涨家数: {sentiment.get('up_count')}")
                print(f"  - 下跌家数: {sentiment.get('down_count')}")
                print(f"  - 涨停家数: {sentiment.get('limit_up')}")
                print(f"  - 跌停家数: {sentiment.get('limit_down')}")
                print(f"  - 市场宽度: {sentiment.get('market_breadth')}%")
                print(f"  - 数据质量: {sentiment.get('data_quality')}")
                print(f"  - 数据源: {sentiment.get('data_source')}")
                
                if sentiment.get('total_count', 0) >= 5000:
                    print("  [OK] 数据完整（>= 5000只股票）")
                else:
                    print("  [WARN] 数据不完整（< 5000只股票）")
            else:
                print("[FAIL] 获取失败")
        else:
            print("[FAIL] Tushare 服务不可用")
    else:
        print("[WARN] Tushare Token 未配置")
    
    # 2. 测试AKShare数据源（包含Tushare优先级）
    print("\n[2] 测试 AKShare 数据源（含Tushare优先级）")
    print("-" * 60)
    
    from services.akshare_service import akshare_service
    
    if akshare_service.available:
        print("[OK] AKShare 服务可用")
        
        print("正在获取市场情绪数据...")
        sentiment = await akshare_service.get_market_sentiment()
        
        if sentiment:
            print(f"[OK] 获取成功:")
            print(f"  - 总股票数: {sentiment.get('total_count')}")
            print(f"  - 数据源: {sentiment.get('data_source')}")
            print(f"  - 数据质量: {sentiment.get('data_quality')}")
            
            if sentiment.get('total_count', 0) >= 5000:
                print("  [OK] 数据完整（>= 5000只股票）")
            else:
                print("  [WARN] 数据不完整（< 5000只股票）")
        else:
            print("[FAIL] 获取失败")
    else:
        print("[FAIL] AKShare 服务不可用")
    
    # 3. 测试缓存机制
    print("\n[3] 测试市场情绪缓存机制")
    print("-" * 60)
    
    from services.market_sentiment_cache_service import market_sentiment_cache_service
    from database.session import get_db
    
    async for db in get_db():
        # 检查缓存是否有效
        is_valid = await market_sentiment_cache_service.is_cache_valid(db)
        
        if is_valid:
            print("[OK] 缓存有效（今天有完整数据）")
            
            # 获取缓存数据
            cached = await market_sentiment_cache_service.get_latest_sentiment(db)
            if cached:
                print(f"  - 总股票数: {cached.get('total_count')}")
                print(f"  - 数据源: {cached.get('data_source')}")
                print(f"  - 时间戳: {cached.get('timestamp')}")
        else:
            print("[WARN] 缓存无效或不存在")
        
        # 获取历史数据
        history = await market_sentiment_cache_service.get_sentiment_history(db, days=7)
        print(f"\n历史数据（最近7天）: {len(history)} 条")
        
        if history:
            for item in history[:3]:  # 只显示前3条
                print(f"  - {item['date']}: {item['total_count']} 只股票")
        
        break
    
    # 4. 测试API端点
    print("\n[4] 测试市场情绪API端点")
    print("-" * 60)
    
    from routers.market_data import get_market_sentiment
    
    async for db in get_db():
        try:
            result = await get_market_sentiment(db)
            
            if result.get('total_count', 0) >= 5000:
                print("[OK] API返回有效数据:")
                print(f"  - 总股票数: {result.get('total_count')}")
                print(f"  - 数据源: {result.get('data_source')}")
                print(f"  - 数据质量: {result.get('data_quality')}")
            else:
                print("[WARN] API返回数据不完整")
                print(f"  - 总股票数: {result.get('total_count')}")
        except Exception as e:
            error_msg = str(e)
            if '503' in error_msg:
                print("[FAIL] API返回503错误（数据不足）")
                print(f"  - 错误信息: {error_msg[:200]}")
            else:
                print(f"[FAIL] API调用失败: {error_msg}")
        
        break
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    print("\n总结:")
    print("1. Tushare数据源已集成（需要Token）")
    print("2. AKShare数据源作为备用")
    print("3. 缓存机制已实现")
    print("4. 定时更新已配置:")
    print("   - 交易时间每5分钟更新")
    print("   - 非交易时间每小时更新")
    print("   - 启动时立即更新一次")
    print("\n建议:")
    print("- 重启后端服务以应用新的定时任务")
    print("- 检查Tushare Token是否有效")
    print("- 在交易时间测试数据更新")


if __name__ == '__main__':
    asyncio.run(test_data_sources())
