
import asyncio
import logging
import sys
import os

# 添加项目根目录到 sys.path
# 文件在 test/NE1/test_tencent_bk.py，需要向上跳三层到项目根目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.stock_service import StockService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_tencent_bk():
    service = StockService()
    # 行业板块代码示例: BK0897 (房地产)
    bk_code = "BK0897"
    logger.info(f"Testing K-line for {bk_code} from Tencent...")
    
    try:
        # 获取 K 线数据
        klines = await service.get_kline(bk_code, period="day", count=5)
        
        if klines:
            logger.info(f"Successfully retrieved {len(klines)} K-line items for {bk_code}")
            for k in klines:
                logger.info(f"Date: {k.date}, Close: {k.close}")
        else:
            logger.error(f"Failed to retrieve K-line for {bk_code}")
            
    except Exception as e:
        logger.error(f"Error testing Tencent BK: {str(e)}")
    finally:
        if hasattr(service, 'client') and service.client:
            await service.client.aclose()

if __name__ == "__main__":
    asyncio.run(test_tencent_bk())
