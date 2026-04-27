"""预测分析路由"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging

from services.prediction_engine import PredictionEngine
from routers.holding import holding_manager  # 使用全局单例

logger = logging.getLogger(__name__)

router = APIRouter()

# 创建预测引擎
prediction_engine = PredictionEngine()
# 使用全局单例（已在导入时定义）
# holding_manager 来自 routers.holding


@router.get("/all")
async def predict_all():
    """预测所有持仓股票"""
    try:
        holdings = await holding_manager.load_holdings()
        predictions = await prediction_engine.predict_all_holdings(holdings.dict())
        return {"predictions": predictions, "count": len(predictions)}
    except Exception as e:
        logger.error(f"批量预测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector-rotation")
async def analyze_sector_rotation():
    """板块轮动分析"""
    try:
        from services.prediction_engine import SectorRotationAnalyzer
        
        logger.info("收到板块轮动分析请求")
        holdings = await holding_manager.load_holdings()
        
        if not holdings or not holdings.sectors:
            logger.warning("未找到持仓数据")
            # 返回空的分析结果
            from datetime import datetime
            from models.prediction import SectorRotationAnalysis
            return SectorRotationAnalysis(
                date=datetime.now().strftime('%Y-%m-%d'),
                hotspot_sectors=[],
                hotspot_changes={},
                money_flow={},
                next_hotspot_prediction=None,
                timestamp=datetime.now()
            )
        
        sectors = [sector.name for sector in holdings.sectors]
        logger.info(f"持仓板块: {sectors}")
        
        analyzer = SectorRotationAnalyzer()
        rotation = await analyzer.analyze_rotation(sectors)
        
        if not rotation:
            logger.warning("板块轮动分析返回空结果")
            from datetime import datetime
            from models.prediction import SectorRotationAnalysis
            return SectorRotationAnalysis(
                date=datetime.now().strftime('%Y-%m-%d'),
                hotspot_sectors=[],
                hotspot_changes={},
                money_flow={},
                next_hotspot_prediction=None,
                timestamp=datetime.now()
            )
        
        logger.info(f"板块轮动分析成功: {len(rotation.hotspot_sectors)} 个热点板块")
        return rotation
        
    except Exception as e:
        logger.error(f"板块轮动分析失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"板块轮动分析失败: {str(e)}")


@router.get("/{stock_code}")
async def predict_stock(stock_code: str):
    """预测单只股票"""
    try:
        # 加载持仓数据
        holdings = await holding_manager.load_holdings()
        
        # 查找股票信息
        stock_info = None
        for sector in holdings.sectors:
            for stock in sector.stocks:
                if stock.code == stock_code:
                    stock_info = {'name': stock.name, 'sector': sector.name}
                    break
            if stock_info:
                break
        
        if not stock_info:
            raise HTTPException(status_code=404, detail=f"股票 {stock_code} 不在持仓中")
        
        # 执行预测
        prediction = await prediction_engine.predict(
            stock_code,
            stock_info['name'],
            stock_info['sector']
        )
        
        if not prediction:
            raise HTTPException(status_code=500, detail=f"预测失败 {stock_code}")
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预测失败 {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{stock_code}/technical")
async def analyze_technical(stock_code: str):
    """技术指标分析"""
    try:
        from services.prediction_engine import TechnicalAnalyzer
        
        analyzer = TechnicalAnalyzer()
        analysis = await analyzer.analyze_technical(stock_code)
        
        return analysis
        
    except Exception as e:
        logger.error(f"技术指标分析失败 {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
