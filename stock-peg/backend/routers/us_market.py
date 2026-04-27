"""美股市场分析路由"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from services.us_market_analyzer import USMarketAnalyzer, USMarketDataService, USMarketCorrelationEngine
from routers.holding import holding_manager  # 使用全局单例
from services.background_updater import background_updater
from services.data_update_manager import data_update_manager
from services.data_source_tracker import data_source_tracker
from database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# 创建美股分析器
us_market_analyzer = USMarketAnalyzer()
us_data_service = USMarketDataService()
correlation_engine = USMarketCorrelationEngine()
# 使用全局单例（已在导入时定义）
# holding_manager 来自 routers.holding


@router.get("/indices")
async def get_us_market_indices(db: AsyncSession = Depends(get_db)):
    """获取美股主要指数数据"""
    try:
        # 1. 触发后台更新（美股指数）
        us_indices = ['^GSPC', '^IXIC', '^DJI', '^VIX', '^N225', '^KS11']
        updating_indices = []
        
        for symbol in us_indices:
            # 检查是否需要更新
            update_necessity = await data_update_manager.check_update_necessity(symbol, 'us_index')
            if update_necessity['needs_update']:
                await background_updater.submit_us_index_update_task(symbol)
                updating_indices.append(symbol)
        
        # 2. 从数据库获取（DB-first，真实数据）
        indices = await us_data_service.get_us_market_indices(db=db)
        
        # 3. 判断数据来源
        data_source = 'db' if indices else 'none'
        is_updating = len(updating_indices) > 0
        
        # 4. 记录数据来源
        await data_source_tracker.track_data_read(
            db=db,
            data_type='us_index',
            stock_code='US_INDICES',
            data_source=data_source,
            is_updating=is_updating,
            metadata={'indices': us_indices, 'updating': updating_indices}
        )
        
        # 5. 构建响应
        return data_source_tracker.build_metadata_response(
            data=indices,  # 如果为空，前端收到 {}
            data_type='us_index',
            stock_code='US_INDICES',
            data_source=data_source,
            is_updating=is_updating,
            extra_metadata={'updating_indices': updating_indices}
        )
        
    except Exception as e:
        logger.error(f"获取美股指数失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{symbol}")
async def get_us_stock_data(symbol: str, db: AsyncSession = Depends(get_db)):
    """获取美股个股数据"""
    try:
        # 1. 触发后台更新
        update_necessity = await data_update_manager.check_update_necessity(symbol, 'us_index')
        is_updating = False
        if update_necessity['needs_update']:
            await background_updater.submit_us_index_update_task(symbol)
            is_updating = True
            
        # 2. 从数据库获取（DB-first）
        data = await us_data_service.get_us_stock_data(symbol, db=db)
        
        if not data:
            # 数据库没有数据，触发异步更新并返回 404
            logger.info(f"数据库中无美股 {symbol} 数据，触发后台更新")
            await background_updater.submit_us_index_update_task(symbol)
            
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": f"未找到美股 {symbol} 的数据。已启动后台更新。",
                    "is_updating": True
                }
            )
        
        data_source = 'db'
        
        # 3. 记录数据来源
        await data_source_tracker.track_data_read(
            db=db,
            data_type='us_index',
            stock_code=symbol,
            data_source=data_source,
            last_update_time=update_necessity.get('last_update'),
            is_updating=is_updating
        )
        
        # 4. 构建响应
        return data_source_tracker.build_metadata_response(
            data=data,
            data_type='us_index',
            stock_code=symbol,
            data_source=data_source,
            last_update=update_necessity.get('last_update'),
            is_updating=is_updating
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取美股数据失败 {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/related-stocks/{stock_code}")
async def get_related_us_stocks(stock_code: str):
    """获取A股持仓股票的美股相关标的"""
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
        
        # AI识别相关美股
        correlations = await correlation_engine.identify_related_us_stocks(
            stock_info['name'],
            stock_info['sector']
        )
        
        return correlations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取相关美股失败 {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{stock_code}")
async def analyze_us_market_impact(stock_code: str):
    """分析美股对持仓股票的影响"""
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
        
        # 获取相关美股
        related_stocks = await correlation_engine.identify_related_us_stocks(
            stock_info['name'],
            stock_info['sector']
        )
        
        # 获取美股数据
        us_data = {}
        for category, stocks in related_stocks.items():
            for stock in stocks:
                data = await us_data_service.get_us_stock_data(stock['symbol'])
                if data:
                    us_data[stock['symbol']] = data
        
        # AI分析
        analysis = {}
        for symbol, data in us_data.items():
            analysis[symbol] = await us_market_analyzer.analyze_related_stock(
                symbol,
                data,
                stock_info['name']
            )
        
        return {
            'stock_code': stock_code,
            'stock_name': stock_info['name'],
            'related_stocks': related_stocks,
            'us_data': us_data,
            'analysis': analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"美股影响分析失败 {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-report")
async def get_daily_us_report():
    """获取每日美股市场报告"""
    try:
        holdings = await holding_manager.load_holdings()
        report = await us_market_analyzer.generate_daily_us_report(holdings.dict())
        return {"report": report}
    except Exception as e:
        logger.error(f"生成美股报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vix")
async def get_vix_index():
    """获取VIX恐慌指数"""
    try:
        # 尝试获取VIX数据
        vix_data = await us_data_service.get_us_stock_data('^VIX')
        
        if vix_data:
            return {
                'symbol': 'VIX',
                'name': 'CBOE波动率指数',
                'price': vix_data.get('price'),
                'change': vix_data.get('change'),
                'change_pct': vix_data.get('change_pct'),
                'timestamp': vix_data.get('timestamp')
            }
        
        # 如果获取失败，返回默认值
        return {
            'symbol': 'VIX',
            'name': 'CBOE波动率指数',
            'price': None,
            'change': None,
            'change_pct': None,
            'message': 'VIX数据暂时不可用'
        }
    except Exception as e:
        logger.error(f"获取VIX指数失败: {str(e)}")
        return {
            'symbol': 'VIX',
            'name': 'CBOE波动率指数',
            'price': None,
            'change': None,
            'change_pct': None,
            'error': str(e)
        }
