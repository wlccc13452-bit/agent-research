"""系统状态检查路由"""
from fastapi import APIRouter
from typing import Dict
import logging
import httpx
import tushare as ts
from datetime import datetime

from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api-status")
async def check_api_status() -> Dict:
    """检查各个数据源的连接状态"""
    from datasource import get_datasource, DataSourceType
    
    # 检查 Akshare 数据源
    akshare_source = get_datasource().get_source(DataSourceType.AKSHARE)
    akshare_available = await akshare_source.is_available() if akshare_source else False
    
    status = {
        "tushare": await check_tushare(),
        "alphavantage": await check_alphavantage(),
        "finnhub": await check_finnhub(),
        "tencent": await check_tencent(),
        "akshare": {
            "status": "ok" if akshare_available else "error",
            "message": "Akshare API 可用" if akshare_available else "Akshare API 不可用 (未安装或网络问题)"
        },
        "timestamp": str(datetime.now()) if 'datetime' in dir() else "N/A"
    }
    return status


async def check_tushare() -> Dict:
    """检查 Tushare API 状态"""
    import asyncio
    try:
        if not settings.tushare_token:
            return {
                "status": "not_configured",
                "message": "Tushare Token 未配置"
            }
        
        # 封装同步调用
        def _check():
            # 设置token并初始化pro接口
            pro = ts.pro_api(settings.tushare_token)
            
            # 使用基础接口验证连接（不需要高权限）
            # 尝试获取股票列表（这是最基础的接口，通常不需要高积分）
            return pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')
        
        df = await asyncio.to_thread(_check)
        
        if df is not None and not df.empty:
            return {
                "status": "ok",
                "message": f"Tushare API 正常 (可用股票: {len(df)})"
            }
        else:
            return {
                "status": "degraded",
                "message": "Tushare API 响应异常"
            }
            
    except Exception as e:
        error_msg = str(e)
        # 识别权限错误
        if "没有接口访问权限" in error_msg or "权限" in error_msg:
            logger.warning(f"Tushare API 权限不足: {error_msg}")
            return {
                "status": "limited",
                "message": "Tushare 权限不足（需要更高积分）"
            }
        else:
            logger.error(f"Tushare API 检查失败: {error_msg}")
            return {
                "status": "error",
                "message": f"Tushare API 错误: {error_msg[:50]}"
            }


async def check_alphavantage() -> Dict:
    """检查 Alpha Vantage API 状态"""
    try:
        if not settings.alphavantage_api_key:
            return {
                "status": "not_configured",
                "message": "Alpha Vantage Key 未配置"
            }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 测试API连接
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": "AAPL",
                "apikey": settings.alphavantage_api_key
            }
            
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                # 检查是否返回有效数据
                if "Global Quote" in data or "Note" in data:
                    return {
                        "status": "ok",
                        "message": "Alpha Vantage API 正常"
                    }
                else:
                    return {
                        "status": "degraded",
                        "message": "Alpha Vantage API 响应异常"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Alpha Vantage HTTP {response.status_code}"
                }
                
    except httpx.TimeoutException:
        return {
            "status": "timeout",
            "message": "Alpha Vantage 超时（可能需要国际网络）"
        }
    except Exception as e:
        logger.error(f"Alpha Vantage API 检查失败: {str(e)}")
        return {
            "status": "error",
            "message": f"Alpha Vantage 错误: {str(e)[:50]}"
        }


async def check_finnhub() -> Dict:
    """检查 Finnhub API 状态"""
    try:
        if not settings.finnhub_api_key:
            return {
                "status": "not_configured",
                "message": "Finnhub Key 未配置"
            }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = "https://finnhub.io/api/v1/quote"
            params = {
                "symbol": "AAPL",
                "token": settings.finnhub_api_key
            }
            
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'c' in data:
                    return {
                        "status": "ok",
                        "message": "Finnhub API 正常"
                    }
                else:
                    return {
                        "status": "degraded",
                        "message": "Finnhub API 响应异常"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Finnhub HTTP {response.status_code}"
                }
                
    except httpx.TimeoutException:
        return {
            "status": "timeout",
            "message": "Finnhub 超时"
        }
    except Exception as e:
        logger.error(f"Finnhub API 检查失败: {str(e)}")
        return {
            "status": "error",
            "message": f"Finnhub 错误: {str(e)[:50]}"
        }


async def check_tencent() -> Dict:
    """检查腾讯股票 API 状态"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"{settings.tencent_api_base}/q=sh000001"
            response = await client.get(url)
            
            if response.status_code == 200:
                content = response.text
                # 检查是否返回有效数据
                if 'v_sh000001' in content or '上证指数' in content:
                    return {
                        "status": "ok",
                        "message": "腾讯 API 正常"
                    }
                else:
                    return {
                        "status": "degraded",
                        "message": "腾讯 API 响应异常"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"腾讯 HTTP {response.status_code}"
                }
                
    except Exception as e:
        logger.error(f"腾讯 API 检查失败: {str(e)}")
        return {
            "status": "error",
            "message": f"腾讯错误: {str(e)[:50]}"
        }
