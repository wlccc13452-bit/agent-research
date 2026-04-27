"""检查缓存的市场情绪数据"""
import asyncio
from database.session import get_db
from services.market_sentiment_cache_service import market_sentiment_cache_service

async def main():
    async for db in get_db():
        # 获取最新缓存
        cached = await market_sentiment_cache_service.get_latest_sentiment(db)
        
        if cached:
            print("=" * 60)
            print("缓存的市场情绪数据：")
            print("=" * 60)
            print(f"总股票数: {cached.get('total_count')}")
            print(f"上涨家数: {cached.get('up_count')}")
            print(f"下跌家数: {cached.get('down_count')}")
            print(f"涨停家数: {cached.get('limit_up')}")
            print(f"跌停家数: {cached.get('limit_down')}")
            print(f"市场宽度: {cached.get('market_breadth')}%")
            print(f"数据质量: {cached.get('data_quality')}")
            print(f"数据源: {cached.get('data_source')}")
            print(f"时间戳: {cached.get('timestamp')}")
            print("=" * 60)
        else:
            print("无缓存数据")
        
        break

if __name__ == "__main__":
    asyncio.run(main())
