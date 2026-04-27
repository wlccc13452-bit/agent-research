"""新闻路由"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from services.news_aggregator import news_aggregator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stock/{stock_code}")
async def get_stock_news(
    stock_code: str,
    stock_name: Optional[str] = Query(None, description="股票名称"),
    limit: int = Query(20, ge=1, le=100, description="新闻数量")
):
    """获取股票相关新闻"""
    try:
        news = await news_aggregator.get_stock_news(stock_code, stock_name or stock_code, limit)
        return {
            "stock_code": stock_code,
            "stock_name": stock_name or stock_code,
            "count": len(news),
            "news": news
        }
    except Exception as e:
        logger.error(f"获取股票新闻失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector/{sector_name}")
async def get_sector_news(
    sector_name: str,
    count: int = Query(20, ge=1, le=100, description="新闻数量")
):
    """获取板块相关新闻"""
    try:
        news = await news_aggregator.get_sector_news(sector_name, count)
        return {
            "sector_name": sector_name,
            "count": len(news),
            "news": news
        }
    except Exception as e:
        logger.error(f"获取板块新闻失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot")
async def get_hot_news(count: int = Query(20, ge=1, le=100, description="新闻数量")):
    """获取热门财经新闻"""
    try:
        news = await news_aggregator.get_hot_news(count)
        return {
            "count": len(news),
            "news": news
        }
    except Exception as e:
        logger.error(f"获取热门新闻失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-sentiment")
async def analyze_news_sentiment(news_list: list):
    """分析新闻情感"""
    try:
        sentiment = await news_aggregator.analyze_news_sentiment(news_list)
        return sentiment
    except Exception as e:
        logger.error(f"分析新闻情感失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
