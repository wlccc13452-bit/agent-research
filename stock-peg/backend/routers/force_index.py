"""Alexander Elder强力指数（Force Index）API路由

提供股票买卖信号评估接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from services.force_index_calculator import force_index_calculator
from database.session import get_db
from routers.holding import holding_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/force-index/{stock_code_or_name}")
async def analyze_force_index(
    stock_code_or_name: str,
    period: str = Query("day", description="K线周期: day/week/month"),
    ema_short: int = Query(2, description="短期EMA周期", ge=1, le=10),
    ema_long: int = Query(13, description="长期EMA周期", ge=5, le=30),
    count: int = Query(100, description="K线数量", ge=50, le=2000),
    use_cache: bool = Query(True, description="是否使用缓存"),
    local_only: bool = Query(True, description="仅使用本地数据库数据"),
    db: AsyncSession = Depends(get_db)
):
    """
    计算股票的Force Index指标并给出买卖建议
    
    支持通过股票代码或股票名称查询
    
    Args:
        stock_code_or_name: 股票代码（如"000001"）或股票名称（如"平安银行"）
        period: K线周期，默认day
        ema_short: 短期EMA周期，默认2
        ema_long: 长期EMA周期，默认13
        count: K线数量，默认100
        
    Returns:
        {
            'stock_code': 股票代码,
            'stock_name': 股票名称,
            'signals': {
                'current_signal': 当前信号,
                'signal_strength': 信号强度,
                'buy_signals': 买入信号列表,
                'sell_signals': 卖出信号列表
            },
            'trend_analysis': 趋势分析,
            'strength_analysis': 力量分析,
            'current_values': 当前值,
            'recent_data': 最近10天数据
        }
    """
    try:
        # 1. 判断输入是股票代码还是股票名称
        stock_code, stock_name = await _resolve_stock_code_and_name(stock_code_or_name)
        
        if not stock_code:
            raise HTTPException(
                status_code=404, 
                detail=f"未找到股票: {stock_code_or_name}"
            )
        
        logger.info(f"Calculating Force Index: {stock_code} ({stock_name})")
        
        # 2. 计算Force Index (传入stock_name以便缓存)
        result = await force_index_calculator.calculate_force_index(
            db=db,
            stock_code=stock_code,
            stock_name=stock_name,
            period=period,
            ema_short=ema_short,
            ema_long=ema_long,
            count=count,
            use_cache=use_cache,
            local_only=local_only
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"无法获取股票 {stock_code} 的数据"
            )
        
        # 3. 确保股票名称在结果中
        if 'stock_name' not in result or not result['stock_name']:
            result['stock_name'] = stock_name
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Force Index analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/force-index-batch")
async def analyze_force_index_batch(
    period: str = Query("day", description="K线周期: day/week/month"),
    db: AsyncSession = Depends(get_db)
):
    """
    批量计算所有自持股票的Force Index
    
    Returns:
        [
            {stock_code, stock_name, signal, signal_strength, trend},
            ...
        ]
    """
    try:
        # 1. 加载所有自持股票
        holdings = await holding_manager.load_holdings()
        
        if not holdings or not holdings.sectors:
            return []
        
        # 2. 收集所有股票
        stocks = []
        for sector in holdings.sectors:
            for stock in sector.stocks:
                if stock.code and stock.code != 'UNKNOWN':
                    stocks.append({
                        'code': stock.code,
                        'name': stock.name
                    })
        
        # 3. 批量计算
        results = []
        for stock in stocks:
            try:
                result = await force_index_calculator.calculate_force_index(
                    db=db,
                    stock_code=stock['code'],
                    period=period,
                    count=50  # 批量计算使用较少数据
                )
                
                if result:
                    results.append({
                        'stock_code': stock['code'],
                        'stock_name': stock['name'],
                        'signal': result['signals']['current_signal'],
                        'signal_strength': result['signals']['signal_strength'],
                        'trend': result['trend_analysis']['trend_direction'],
                        'trend_strength': result['trend_analysis']['trend_strength'],
                        'power_balance': result['strength_analysis']['power_balance']
                    })
            except Exception as e:
                logger.warning(f"Failed to calculate Force Index for {stock['code']}: {str(e)}")
                continue
        
        # 4. 按信号强度排序
        results.sort(key=lambda x: x['signal_strength'], reverse=True)
        
        return results
        
    except Exception as e:
        logger.error(f"Batch Force Index analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _resolve_stock_code_and_name(stock_code_or_name: str) -> tuple[Optional[str], str]:
    """
    解析股票代码或名称，返回(股票代码, 股票名称)
    
    Args:
        stock_code_or_name: 股票代码或名称
        
    Returns:
        (股票代码, 股票名称)
        如果找不到返回 (None, "")
    """
    # 判断是否是股票代码（纯数字或包含数字）
    is_code = any(char.isdigit() for char in stock_code_or_name)
    
    if is_code:
        # 可能是股票代码，直接使用
        stock_code = stock_code_or_name.upper()
        
        # 尝试从持仓中查找名称
        stock_name = await _get_stock_name_from_holdings(stock_code)
        
        return stock_code, stock_name
    else:
        # 是股票名称，从持仓中查找代码
        stock_code = await _get_stock_code_from_holdings(stock_code_or_name)
        
        if stock_code:
            return stock_code, stock_code_or_name
        else:
            return None, ""


async def _get_stock_name_from_holdings(stock_code: str) -> str:
    """从持仓中获取股票名称"""
    try:
        holdings = await holding_manager.load_holdings()
        
        if holdings and holdings.sectors:
            for sector in holdings.sectors:
                for stock in sector.stocks:
                    if stock.code == stock_code:
                        return stock.name
        
        return stock_code  # 找不到就返回代码
    except Exception:
        return stock_code


async def _get_stock_code_from_holdings(stock_name: str) -> Optional[str]:
    """从持仓中获取股票代码，如果找不到则从akshare查询"""
    # 1. 先从持仓中查找
    try:
        holdings = await holding_manager.load_holdings()
        
        if holdings and holdings.sectors:
            for sector in holdings.sectors:
                for stock in sector.stocks:
                    # 支持模糊匹配
                    if stock.name == stock_name or stock_name in stock.name:
                        return stock.code
    except Exception:
        pass
    
    # 2. 如果持仓中找不到，从 datasource 查询
    try:
        from datasource import get_datasource, DataSourceType
        akshare_source = get_datasource().get_source(DataSourceType.AKSHARE)
        if akshare_source:
            stock_code = await akshare_source.search_stock_by_name(stock_name)
            if stock_code:
                logger.info(f"Found stock code {stock_code} for name '{stock_name}' via datasource")
                return stock_code
    except Exception as e:
        logger.warning(f"Failed to search stock code for '{stock_name}': {str(e)}")
    
    return None
