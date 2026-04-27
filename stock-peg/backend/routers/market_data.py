"""市场数据路由 - 基于 AKShare 的增强数据接口"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import logging
import re
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession

from datasource import get_datasource, DataSourceType
from services.quote_data_service import quote_data_service
from services.market_sentiment_cache_service import market_sentiment_cache_service
from database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_akshare_source():
    """获取 AkshareDataSource 实例"""
    return get_datasource().get_source(DataSourceType.AKSHARE)


def _resolve_trade_date(sentiment: dict) -> Optional[date]:
    trade_date_value = sentiment.get("trade_date")
    if isinstance(trade_date_value, date):
        return trade_date_value
    if isinstance(trade_date_value, str):
        text = trade_date_value.strip()
        for fmt in ("%Y%m%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
    return None


def _is_complete_sentiment(sentiment: Optional[dict]) -> bool:
    if not sentiment:
        return False
    total_count = int(sentiment.get("total_count") or 0)
    if total_count < 5000:
        return False
    if sentiment.get("data_quality") != "full":
        return False
    up_count = int(sentiment.get("up_count") or 0)
    down_count = int(sentiment.get("down_count") or 0)
    flat_count = int(sentiment.get("flat_count") or 0)
    if up_count <= 0 and down_count <= 0 and flat_count <= 0:
        return False
    return (up_count + down_count + flat_count) >= int(total_count * 0.95)


# ==================== 行业板块接口 ====================

@router.get("/industry-sectors")
async def get_industry_sectors():
    """获取行业板块列表"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        sectors = await source.get_industry_sectors()
        return {"sectors": sectors}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取行业板块失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/concept-sectors")
async def get_concept_sectors():
    """获取概念板块列表"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        sectors = await source.get_concept_sectors()
        return {"sectors": sectors}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取概念板块失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector-stocks/{sector_name}")
async def get_sector_stocks(sector_name: str):
    """获取板块成分股"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        stocks = await source.get_sector_stocks(sector_name)
        return {"sector": sector_name, "stocks": stocks}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取板块成分股失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 资金流向接口 ====================

@router.get("/fund-flow/{stock_code}")
async def get_individual_fund_flow(stock_code: str):
    """获取个股资金流向"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用或无数据")
        flow = await source.get_individual_fund_flow(stock_code)
        return flow
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取个股资金流向失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector-fund-flow")
async def get_sector_fund_flow(
    sector_type: str = Query("行业", description="板块类型: 行业 或 概念")
):
    """获取板块资金流向排行"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        flows = await source.get_sector_fund_flow(sector_type)
        return {"sector_type": sector_type, "flows": flows}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取板块资金流向失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-fund-flow")
async def get_market_fund_flow(
    days: int = Query(20, description="获取最近多少天的数据", ge=1, le=100)
):
    """获取大盘资金流向数据(市场净流入)
    
    返回最近N天的市场资金净流入情况
    """
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用或无数据")
        flows = await source.get_market_fund_flow(days)
        return {"days": days, "flows": flows}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取大盘资金流向失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 龙虎榜接口 ====================

@router.get("/lhb-detail")
async def get_lhb_detail(
    days: int = Query(1, description="查询天数", ge=1, le=30)
):
    """获取龙虎榜详情
    
    Args:
        days: 查询最近几天的数据
    """
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        details = await source.get_lhb_detail(start_date, end_date)
        return {"start_date": start_date, "end_date": end_date, "details": details}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取龙虎榜详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 市场情绪接口 ====================

@router.get("/market-sentiment")
async def get_market_sentiment(db: AsyncSession = Depends(get_db)):
    """获取市场情绪统计（涨跌停、市场宽度等）
    
    数据获取策略：
    1. 优先从缓存读取（当天有效数据，必须>=5000只股票）
    2. 缓存无效时尝试AKShare（必须>=5000只股票）
    3. 数据不足5000时返回错误，不返回不完整数据
    
    Returns:
        成功: 包含5000+股票的市场情绪数据
        失败: HTTP 503 错误，提示数据不足
    """
    try:
        # 获取 AkshareDataSource
        source = _get_akshare_source()
        
        # 1. 检查缓存是否有效(必须有5000+股票)
        cached = await market_sentiment_cache_service.get_latest_sentiment(db)
        if cached and cached.get('total_count', 0) >= 5000:
            logger.info(f"从缓存获取市场情绪数据: {cached['total_count']} 只股票")
            cached['data_source'] = cached.get('data_source', 'cache') + '_cached'
            cached['sample_scope'] = 'a_share_market'
            return cached
        
        # 2. 尝试从AKShare获取
        sentiment = await source.get_market_sentiment() if source else None
        if _is_complete_sentiment(sentiment):
            # 保存到缓存
            await market_sentiment_cache_service.save_sentiment(db, sentiment, _resolve_trade_date(sentiment))
            
            # 同时获取上证指数数据
            try:
                sh_klines = await source.get_index_kline("000001", "day", 2) if source else None
                if sh_klines and len(sh_klines) > 0:
                    latest_kline = sh_klines[-1]
                    sentiment['sh_index_close'] = latest_kline.get('close')
                    # 计算上证指数涨跌幅
                    if len(sh_klines) > 1:
                        prev_close = sh_klines[-2].get('close')
                        curr_close = latest_kline.get('close')
                        if prev_close and curr_close:
                            sentiment['sh_index_change_pct'] = round(
                                (curr_close - prev_close) / prev_close * 100, 2
                            )
                    # 更新缓存
                    await market_sentiment_cache_service.save_sentiment(db, sentiment, _resolve_trade_date(sentiment))
            except Exception as e:
                logger.warning(f"获取上证指数数据失败: {str(e)}")
            
            sentiment['data_source'] = 'akshare'
            sentiment['sample_scope'] = 'a_share_market'
            return sentiment
        
        # 3. 数据不足5000，返回错误（不返回不完整数据）
        # 先检查本地数据库有多少数据
        quotes = await quote_data_service.get_all_quotes_from_db(db)
        local_count = len(quotes) if quotes else 0
        
        error_detail = {
            "error": "insufficient_data",
            "message": "市场情绪数据不足，无法提供准确分析",
            "details": {
                "required_count": 5000,
                "cache_count": cached.get('total_count', 0) if cached else 0,
                "local_count": local_count,
                "akshare_status": "failed" if sentiment is None else f"only_{sentiment.get('total_count', 0)}_stocks"
            },
            "suggestion": "请检查网络连接或稍后重试。系统需要至少5000只A股股票数据才能提供准确的市场情绪分析。"
        }
        
        raise HTTPException(
            status_code=503, 
            detail=error_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取市场情绪统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market-sentiment/refresh")
async def refresh_market_sentiment(db: AsyncSession = Depends(get_db)):
    """手动刷新市场情绪数据
    
    强制从AKShare重新获取数据并更新缓存
    """
    try:
        # 获取 AkshareDataSource
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        
        # 尝试从AKShare获取
        sentiment = await source.get_market_sentiment()
        
        if _is_complete_sentiment(sentiment):
            # 获取上证指数数据
            try:
                sh_klines = await source.get_index_kline("000001", "day", 2)
                if sh_klines and len(sh_klines) > 0:
                    latest_kline = sh_klines[-1]
                    sentiment['sh_index_close'] = latest_kline.get('close')
                    if len(sh_klines) > 1:
                        prev_close = sh_klines[-2].get('close')
                        curr_close = latest_kline.get('close')
                        if prev_close and curr_close:
                            sentiment['sh_index_change_pct'] = round(
                                (curr_close - prev_close) / prev_close * 100, 2
                            )
            except Exception as e:
                logger.warning(f"获取上证指数数据失败: {str(e)}")
            
            # 保存到缓存
            await market_sentiment_cache_service.save_sentiment(db, sentiment, _resolve_trade_date(sentiment))
            
            sentiment['data_source'] = 'akshare'
            sentiment['sample_scope'] = 'a_share_market'
            sentiment['refreshed'] = True
            
            return sentiment
        
        raise HTTPException(status_code=503, detail="市场情绪数据不完整，刷新失败")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新市场情绪数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-sentiment/history")
async def get_market_sentiment_history(
    days: int = Query(30, description="获取最近多少天的数据", ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """获取历史市场情绪数据（从缓存数据库读取）"""
    try:
        # 从缓存数据库读取
        history = await market_sentiment_cache_service.get_sentiment_history(db, days)
        
        if history:
            return {"days": days, "history": history, "source": "cache"}
        
        # 如果缓存为空，返回提示信息
        return {
            "days": days, 
            "history": [], 
            "source": "empty",
            "message": "暂无历史数据，请等待系统自动更新或手动刷新"
        }
        
    except Exception as e:
        logger.error(f"获取历史市场情绪数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 港股美股接口 ====================

@router.get("/hk-spot")
async def get_hk_spot(
    limit: int = Query(100, description="返回数量限制", ge=1, le=500)
):
    """获取港股实时行情"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        stocks = await source.get_hk_spot()
        return {"stocks": stocks[:limit]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取港股实时行情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/us-spot")
async def get_us_spot(
    limit: int = Query(100, description="返回数量限制", ge=1, le=500)
):
    """获取美股实时行情"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        stocks = await source.get_us_spot()
        return {"stocks": stocks[:limit]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取美股实时行情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 宏观经济接口 ====================

@router.get("/macro/cpi")
async def get_china_cpi():
    """获取中国 CPI 数据(最近12个月)"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        data = await source.get_china_cpi()
        return {"data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 CPI 数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macro/gdp")
async def get_china_gdp():
    """获取中国 GDP 数据(最近8个季度)"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        data = await source.get_china_gdp()
        return {"data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 GDP 数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macro/pmi")
async def get_china_pmi():
    """获取中国 PMI 数据(最近12个月)"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        data = await source.get_china_pmi()
        return {"data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 PMI 数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 北向资金接口 ====================

@router.get("/north-money-flow")
async def get_north_money_flow():
    """获取北向资金流向"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        flow = await source.get_north_money_flow()
        return flow
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取北向资金流向失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/north-money-top10")
async def get_north_money_top10():
    """获取北向资金持股前十"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        stocks = await source.get_north_money_top10()
        return {"stocks": stocks}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取北向资金持股前十失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 机构持仓接口 ====================

@router.get("/institution-holdings/{stock_code}")
async def get_institution_holdings(stock_code: str):
    """获取机构持仓数据"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用或无数据")
        holdings = await source.get_institution_holdings(stock_code)
        return {"stock_code": stock_code, "holdings": holdings}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取机构持仓数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 指数数据接口 ====================

@router.get("/index-kline/{index_code}")
async def get_index_kline(
    index_code: str,
    period: str = Query("day", description="K线周期: day/week/month"),
    count: int = Query(100, description="K线数量", ge=1, le=500)
):
    """获取指数 K 线数据
    
    Args:
        index_code: 指数代码,如 '000001' (上证指数)、'399001' (深证成指)
        period: K线周期
        count: K线数量
    """
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        klines = await source.get_index_kline(index_code, period, count)
        return {"index_code": index_code, "period": period, "klines": klines}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取指数 K 线失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index-sh-history")
async def get_sh_index_history(
    days: int = Query(30, description="获取最近多少天的数据", ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """获取上证指数历史数据(用于市场情绪图表)
    
    策略: 本地数据优先,外部数据源异步更新
    1. 优先返回本地数据库中的数据
    2. 后台异步更新数据(如果外部服务可用)
    3. 只有本地无数据且外部服务不可用时才返回错误
    """
    from database.operations.stock_kline_ops import get_kline_data, save_kline_data
    import asyncio
    
    INDEX_CODE = "sh000001"  # 上证指数代码
    
    try:
        # 获取 AkshareDataSource
        source = _get_akshare_source()
        
        # 1. 首先从本地数据库获取数据
        local_klines = await get_kline_data(db, INDEX_CODE, "day", days)
        
        if local_klines:
            # 有本地数据,直接返回
            history = [
                {
                    'date': str(k.trade_date),
                    'close': float(k.close)
                }
                for k in local_klines
            ]
            
            # 异步更新数据(不阻塞响应)
            async def update_index_data():
                try:
                    if source:
                        fresh_klines = await source.get_index_kline("000001", "day", days)
                        if fresh_klines:
                            await save_kline_data(db, INDEX_CODE, fresh_klines, "day")
                            await db.commit()
                            logger.info(f"上证指数数据已更新,共 {len(fresh_klines)} 条")
                except Exception as e:
                    logger.warning(f"后台更新上证指数数据失败: {str(e)}")
            
            asyncio.create_task(update_index_data())
            
            return {
                "days": len(history),
                "history": history,
                "data_source": "local_db",
                "is_updating": True
            }
        
        # 2. 本地无数据,尝试从外部API获取
        if not source:
            raise HTTPException(status_code=503, detail="本地无数据且外部数据源不可用")
        
        klines = await source.get_index_kline("000001", "day", days)
        
        if klines:
            # 保存到本地数据库
            await save_kline_data(db, INDEX_CODE, klines, "day")
            await db.commit()
            
            history = [
                {
                    'date': k['date'],
                    'close': k['close']
                }
                for k in klines
            ]
            
            return {
                "days": len(history),
                "history": history,
                "data_source": "akshare_api",
                "is_updating": False
            }
        
        # 3. 本地无数据,外部服务也不可用
        raise HTTPException(
            status_code=503, 
            detail="本地无数据且外部数据源不可用,请稍后重试"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取上证指数历史数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ETF 基金接口 ====================

@router.get("/etf-spot")
async def get_etf_spot(
    limit: int = Query(100, description="返回数量限制", ge=1, le=500)
):
    """获取 ETF 实时行情"""
    try:
        source = _get_akshare_source()
        if not source:
            raise HTTPException(status_code=503, detail="AKShare 服务不可用")
        etfs = await source.get_etf_spot()
        return {"etfs": etfs[:limit]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 ETF 实时行情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
