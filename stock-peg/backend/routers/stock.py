"""股票行情路由"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime
import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession

from models import StockQuote, StockKLine, TechnicalIndicators
from services.stock_service import StockService
from services.stock_data_service import StockDataService
from services.quote_data_service import quote_data_service
from services.background_updater import background_updater
from services.data_update_manager import data_update_manager
from services.debug_log_manager import debug_log_manager
from database.session import get_db
from config.settings import settings

logger = logging.getLogger(__name__)

# 创建股票服务
stock_service = StockService()
stock_data_service = StockDataService()

# 指数配置路径
INDICES_CONFIG_PATH = settings.data_dir / "indices_config.json"

router = APIRouter()


async def is_allowed_stock_or_index(stock_code: str) -> tuple[bool, str]:
    """
    检查股票代码是否在允许更新的列表中（自持股票或指数）
    
    Returns:
        (is_allowed, reason): 是否允许，原因说明
    """
    # 1. 检查是否是自持股票
    from routers.holding import holding_manager
    holdings = await holding_manager.load_holdings()
    
    if holdings and holdings.sectors:
        for sector in holdings.sectors:
            for stock in sector.stocks:
                if stock.code == stock_code:
                    return (True, f"自持股票: {stock.name if hasattr(stock, 'name') else stock_code}")
    
    # 2. 检查是否是内置指数
    if stock_code in CN_INDICES:
        return (True, f"内置指数: {CN_INDICES[stock_code]}")
    
    # 3. 检查是否在配置的指数列表中
    import asyncio
    exists = await asyncio.to_thread(INDICES_CONFIG_PATH.exists)
    if exists:
        try:
            def read_indices():
                with open(INDICES_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            config = await asyncio.to_thread(read_indices)
            for idx in config.get('indices', []):
                code = idx.get('full_code') or idx.get('code')
                if code == stock_code:
                    return (True, f"配置指数: {idx.get('name', stock_code)}")
        except Exception:
            pass
    
    return (False, f"代码 {stock_code} 不在自持股票或指数列表中")





@router.get("/quote/{stock_code}", response_model=StockQuote)
async def get_stock_quote(stock_code: str, db: AsyncSession = Depends(get_db)):
    """
    获取股票实时行情（仅从数据库读取）
    
    策略：
    1. 只从数据库读取本地缓存的行情数据
    2. 如果数据库无数据，返回404错误（不调用网络API）
    3. 数据过期时标记需要更新，但仍返回现有数据
    """
    from services.data_source_tracker import data_source_tracker
    
    try:
        # 1. 只从数据库读取
        quote = await quote_data_service.get_quote_from_db(db, stock_code)
        
        if quote:
            # 检查数据是否过期（超过1分钟）
            update_check = await quote_data_service.check_update_necessity(
                db, stock_code, max_age_seconds=60
            )
            
            # 记录数据来源
            await data_source_tracker.track_data_read(
                db=db,
                data_type='quote',
                stock_code=stock_code,
                data_source='db',
                is_updating=update_check['needs_update'],
                metadata={'type': 'realtime_quote', 'last_update': str(update_check.get('last_update'))}
            )
            
            # 如果需要更新，提交后台任务（不阻塞）
            if update_check['needs_update']:
                logger.info(f"[CHART] 行情数据已过期，提交后台更新: {stock_code}")
                await background_updater.submit_quote_update_task(stock_code)
            
            return quote
        
        # 2. 数据库无数据，立即触发异步更新并通知客户端
        logger.info(f"[ERROR] 数据库无行情数据，立即触发异步更新: {stock_code}")
        
        # 提交异步更新任务
        task_result = await background_updater.submit_quote_update_task(stock_code)
        
        # 返回一个特殊的响应，告知客户端数据正在更新中
        # 虽然 response_model 是 StockQuote，但我们可以返回一个包含基本信息的对象，或者抛出一个带有信息的 404
        # 为了符合 response_model，我们抛出 404 但包含 detail 信息，前端可以据此显示“更新中”
        raise HTTPException(
            status_code=404, 
            detail={
                "message": f"数据库中未找到股票 {stock_code} 的行情数据。已自动启动后台更新任务。",
                "is_updating": True,
                "task_id": task_result.get("task_id") if task_result.get("success") else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票行情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quotes", response_model=List[StockQuote])
async def get_stock_quotes(stock_codes: List[str], db: AsyncSession = Depends(get_db)):
    """
    批量获取股票实时行情（仅从数据库读取）
    
    策略：
    1. 只从数据库批量读取
    2. 数据库中没有的股票，不返回（不调用网络API）
    """
    from services.data_source_tracker import data_source_tracker
    
    try:
        # 1. 批量从数据库读取
        quotes = await quote_data_service.get_quotes_from_db(db, stock_codes)
        
        # 记录数据来源追踪
        if stock_codes:
            await data_source_tracker.track_data_read(
                db=db,
                data_type='quote',
                stock_code=stock_codes[0] if len(stock_codes) == 1 else 'BATCH',
                data_source='db',
                is_updating=False,
                metadata={
                    'type': 'quotes', 
                    'requested': len(stock_codes), 
                    'found': len(quotes)
                }
            )
        
        return quotes
        
    except Exception as e:
        logger.error(f"批量获取股票行情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline/{stock_code}", response_model=List[StockKLine], deprecated=True)
async def get_stock_kline(
    stock_code: str,
    period: str = Query("day", description="K线周期: day/week/month"),
    count: int = Query(100, description="K线数量", ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    获取股票K线数据 (已废弃：仅从数据库读取)
    
    [WARN]️ 已废弃：请使用 /kline-db/{stock_code} 代替
    """
    try:
        # 仅从数据库读取，不触发更新（旧 API 保持最小功能）
        from services.stock_data_service import stock_data_service
        klines = await stock_data_service.get_kline_from_db(db, stock_code, period, count)
        
        if not klines:
            # 触发后台更新（异步）
            await background_updater.submit_kline_update_task(stock_code, period)
            
        return klines
    except Exception as e:
        logger.error(f"获取K线数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# A股主要指数代码
CN_INDICES = {
    '000001.SH': '上证指数',
    '399001.SZ': '深证指数',
    '399006.SZ': '创业板指',
    '000016.SH': '上证50',
    '000300.SH': '沪深300',
    '000905.SH': '中证500',
}

# 行业板块指数映射
SECTOR_INDEX_MAP = {
    '白酒': 'BK0896',
    '新能源': 'BK0493',
    '半导体': 'BK0897',
    '医药': 'BK0727',
    '证券': 'BK0473',
    '汽车': 'BK0481',
    '银行': 'BK0477',
    '保险': 'BK0474',
    '地产': 'BK0451',
    '煤炭': 'BK0437',
    '钢铁': 'BK0479',
    '科技': 'BK0720',
    '通信': 'BK0448',
    '消费': 'BK0428',
    '铝': 'BK0478',
    '光伏': 'BK1031',
    '有色': 'BK0471',
    'AI': 'BK0800',
    '锂': 'BK1030',
    '芯片': 'BK0891',
    '算力': 'BK1135',
    '机器人': 'BK1090',
    '军工': 'BK0895',
    '电力': 'BK0426',
}


@router.get("/intraday/{stock_code}")
async def get_stock_intraday(stock_code: str, db: AsyncSession = Depends(get_db)):
    """获取股票分时数据 (本地缓存优先)"""
    try:
        # 1. 尝试从缓存获取 (分时数据暂不落库，使用内存缓存)
        from services.extended_cache import quote_cache
        cache_key = f"intraday_{stock_code}"
        cached_data = await quote_cache.get(cache_key)
        
        if cached_data:
            logger.info(f"[TARGET] 从缓存获取分时数据: {stock_code}")
            return cached_data

        # 2. 缓存无数据，触发后台更新并告知客户端
        logger.info(f"[ERROR] 缓存无分时数据，触发后台更新: {stock_code}")
        
        # 提交行情更新任务（行情更新通常会包含最新价格，分时数据可以通过WebSocket推送）
        # 注意：这里我们复用 quote_update_task，或者后续增加专门的 intraday 任务
        await background_updater.submit_quote_update_task(stock_code)
        
        # 返回 404，由前端等待 WebSocket 推送
        raise HTTPException(
            status_code=404, 
            detail={
                "message": f"未找到股票 {stock_code} 的分时数据。已启动后台更新。",
                "is_updating": True
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分时数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technical/{stock_code}", response_model=TechnicalIndicators)
async def get_technical_indicators(stock_code: str, db: AsyncSession = Depends(get_db)):
    """获取技术指标 (仅基于本地数据库计算)"""
    try:
        # 强制使用数据库 K 线计算指标，不触发网络请求
        indicators = await stock_service.get_technical_indicators(stock_code, db_session=db)
        if not indicators:
            # 如果没有本地数据，触发 K 线更新任务 (异步)
            import asyncio
            asyncio.create_task(background_updater.submit_kline_update_task(stock_code))
            
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": f"本地数据库中无足够 K 线数据计算股票 {stock_code} 的技术指标。已启动后台更新。",
                    "is_updating": True
                }
            )
            
        # 记录数据来源追踪
        from services.data_source_tracker import data_source_tracker
        await data_source_tracker.track_data_read(
            db=db,
            data_type='kline',
            stock_code=stock_code,
            data_source='db',
            is_updating=False,
            metadata={'type': 'technical'}
        )
            
        return indicators
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取技术指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cn-indices")
async def get_cn_indices(db: AsyncSession = Depends(get_db)):
    """获取A股主要指数数据（仅从本地数据库读取）"""
    try:
        # [START] 性能优化：优先从缓存获取指数列表
        from services.extended_cache import index_list_cache
        
        cache_key = "cn_indices_list_local"
        cached_indices = await index_list_cache.get(cache_key)
        if cached_indices:
            logger.info(f"⚡ 从缓存获取A股指数列表")
            return {
                'indices': cached_indices,
                'data_source': 'cache',
                'is_updating': False
            }
        
        # 1. 批量从数据库获取行情
        cn_index_codes = list(CN_INDICES.keys())
        # 注意：数据库中存储的代码可能不带后缀，或者格式不同，需要匹配
        quotes = await quote_data_service.get_quotes_from_db(db, cn_index_codes)
        
        updating_indices = []
        
        # 2. 检查缺失的指数并提交后台更新
        found_codes = {q.code for q in quotes}
        for code in cn_index_codes:
            # 标准化匹配
            normalized_code = code.replace('.SH', '').replace('.SZ', '')
            if normalized_code not in found_codes and code not in found_codes:
                # 异步更新
                import asyncio
                asyncio.create_task(background_updater.submit_quote_update_task(code))
                updating_indices.append(code)
            else:
                # 已有的也检查是否过期 (异步检查)
                import asyncio
                asyncio.create_task(background_updater.submit_quote_update_task(code))
                # 注意：为了让前端不等待，我们这里不把已有的 code 加入 updating_indices，除非它真的缺失

        # 3. 构建响应数据
        result = []
        for quote in quotes:
            # 找到对应的全名
            full_code = quote.code
            # 优先使用配置中的名称
            display_name = CN_INDICES.get(full_code)
            
            if not display_name:
                # 尝试带后缀匹配 (处理数据库中存储的是 000001 而配置是 000001.SH 的情况)
                for k, v in CN_INDICES.items():
                    if k.startswith(full_code) or full_code.startswith(k.split('.')[0]):
                        # 只有在名称匹配时才认为是同一个指数
                        if v == quote.name or not quote.name:
                            display_name = v
                            break
            
            result.append({
                **quote.dict(),
                'name': display_name or quote.name or full_code,
                'code': full_code # 保持数据库中的原始代码格式
            })

        # 4. 存入缓存（5分钟有效期，因为是本地数据）
        if result:
            await index_list_cache.set(result, cache_key, ttl_seconds=300)
        
        is_updating = len(updating_indices) > 0
        
        # 5. 构建响应
        from services.data_source_tracker import data_source_tracker
        return data_source_tracker.build_metadata_response(
            data={'indices': result},
            data_type='cn_index',
            stock_code='CN_INDICES',
            data_source='db',
            is_updating=is_updating,
            extra_metadata={'updating_indices': updating_indices}
        )
        
    except Exception as e:
        logger.error(f"获取A股指数失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector-index/{sector_name}")
async def get_sector_index(sector_name: str, db: AsyncSession = Depends(get_db)):
    """获取行业指数数据（仅从本地数据库读取）"""
    try:
        index_code = SECTOR_INDEX_MAP.get(sector_name)
        if not index_code:
            return {'sector': sector_name, 'quote': None, 'message': f'未找到行业 {sector_name} 的指数数据'}
        
        # 1. 从数据库获取行情
        quote = await quote_data_service.get_quote_from_db(db, index_code)
        
        # 2. 从数据库获取 K 线 (最近 30 条)
        from services.stock_data_service import stock_data_service
        klines = await stock_data_service.get_kline_from_db(db, index_code, 'day', 30)
        
        # 3. 检查更新必要性 (异步)
        is_updating = False
        if not quote or not klines:
            import asyncio
            asyncio.create_task(background_updater.submit_quote_update_task(index_code))
            asyncio.create_task(background_updater.submit_kline_update_task(index_code, 'day'))
            is_updating = True
        else:
            # 有数据，异步检查更新
            import asyncio
            asyncio.create_task(background_updater.submit_quote_update_task(index_code))
            asyncio.create_task(background_updater.submit_kline_update_task(index_code, 'day'))
        
        # 4. 构建响应
        from services.data_source_tracker import data_source_tracker
        return data_source_tracker.build_metadata_response(
            data={
                'sector': sector_name,
                'index_code': index_code,
                'quote': quote.dict() if quote else None,
                'klines': [k.dict() for k in klines] if klines else []
            },
            data_type='sector_index',
            stock_code=index_code,
            data_source='db',
            is_updating=is_updating,
            extra_metadata={'sector_name': sector_name}
        )
    except Exception as e:
        logger.error(f"获取行业指数失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pmr/{stock_code}")
async def get_stock_pmr(
    stock_code: str,
    days: int = Query(120, description="获取的天数", ge=30, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    获取股票PMR(动量比值)数据 (优先从本地数据库计算)
    """
    from services.data_source_tracker import data_source_tracker
    try:
        # 1. 尝试从缓存获取
        from services.extended_cache import pmr_cache
        cached_pmr = await pmr_cache.get(stock_code, days)
        if cached_pmr:
            return data_source_tracker.build_metadata_response(
                data=cached_pmr,
                data_type='kline',
                stock_code=stock_code,
                data_source='cache',
                is_updating=False,
                extra_metadata={'type': 'pmr'}
            )

        # 2. 检查本地 K 线数据是否足够
        from services.stock_data_service import stock_data_service
        # PMR 计算需要 days + 120 条数据
        klines = await stock_data_service.get_kline_from_db(db, stock_code, 'day', days + 120)
        
        if not klines or len(klines) < days:
            # 数据不足，触发后台更新
            import asyncio
            asyncio.create_task(background_updater.submit_kline_update_task(stock_code))
            
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": f"本地数据库中无足够 K 线数据计算股票 {stock_code} 的 PMR。已启动后台更新。",
                    "is_updating": True
                }
            )
        
        # 3. 基于本地 K 线直接计算 PMR，避免触发远程数据源导致超时
        import asyncio
        pmr_full = await asyncio.to_thread(stock_service._calculate_pmr, klines)
        if pmr_full and len(pmr_full.get('dates', [])) > days:
            start_idx = len(pmr_full['dates']) - days
            pmr_data = {'dates': pmr_full['dates'][start_idx:]}
            for key, value in pmr_full.items():
                if key == 'dates':
                    continue
                pmr_data[key] = value[start_idx:]
        else:
            pmr_data = pmr_full

        if pmr_data:
            await pmr_cache.set(pmr_data, stock_code, days)

        if not pmr_data:
            raise HTTPException(status_code=404, detail=f"无法计算股票 {stock_code} 的PMR数据")
        
        # 4. 构建响应
        return data_source_tracker.build_metadata_response(
            data=pmr_data,
            data_type='kline',
            stock_code=stock_code,
            data_source='db',
            is_updating=False,
            extra_metadata={'type': 'pmr'}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取PMR数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pmr/precompute")
async def precompute_pmr():
    """
    预计算自持股票的PMR数据
    
    功能：
    - 自动获取所有自持股票列表
    - 批量预计算PMR数据并存入缓存
    - WebSocket推送进度通知
    
    Returns:
        {
            'success': bool,
            'precomputed_count': int,
            'failed_count': int,
            'details': list
        }
    """
    try:
        result = await background_updater.precompute_pmr_for_holdings()
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get('error', '预计算失败'))
            
    except Exception as e:
        logger.error(f"预计算PMR失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kline-db/{stock_code}")
async def get_stock_kline_from_db(
    stock_code: str,
    period: str = Query("day", description="K线周期: day/week/month"),
    count: int = Query(100, description="K线数量", ge=1, le=500),
    quick_load: bool = Query(False, description="快速加载模式：只返回最近60条数据"),
    db: AsyncSession = Depends(get_db)
):
    """
    从数据库获取K线数据（推荐使用）
    
    特性：
    - [OK] 优先返回数据库缓存数据（快速响应）
    - [OK] 后台异步检查更新（不阻塞前端）
    - [OK] WebSocket推送更新完成通知
    - [OK] 支持实时数据刷新
    - [OK] 支持快速加载模式（仅返回最近数据）
    
    快速加载模式（quick_load=true）：
    - 优先返回最近60条数据（约3个月）
    - 后台继续更新更多历史数据
    - 适合首次加载，快速响应用户
    
    本地数据说明：
    - local_data_available: 是否有本地数据可直接返回
    - is_updating: 是否正在后台更新数据
    - last_update: 上次更新时间
    """
    from services.data_source_tracker import data_source_tracker
    # 使用任务日志管理器
    task_id = debug_log_manager.start_task(
        'api_request', 
        f'获取K线数据(DB优先) {stock_code}',
        {'stock_code': stock_code, 'period': period, 'count': count, 'quick_load': quick_load}
    )
    
    try:
        # 1. 快速加载模式：优先返回最近数据
        actual_count = 60 if quick_load else count
        
        # 2. 检查数据更新必要性
        update_necessity = await data_update_manager.check_update_necessity(stock_code, 'kline')
        
        # 3. 如果需要更新，则提交后台任务（异步）
        is_updating = False
        if update_necessity['needs_update']:
            debug_log_manager.log_info(task_id, '数据需要更新，提交后台任务', {
                'reason': update_necessity['reason']
            })
            result = await background_updater.submit_kline_update_task(stock_code, period)
            is_updating = result.get('success', False)
        
        # 4. 无论是否更新，都优先从数据库读取现有数据（真实数据）
        debug_log_manager.log_debug(task_id, '从数据库读取现有K线数据', {
            'stock_code': stock_code,
            'period': period,
            'count': actual_count,
            'quick_load': quick_load
        })
        
        # 注意：这里直接调用 get_kline_from_db 而不是 get_or_update_kline
        # 因为我们希望立即返回现有数据，而不是等待更新完成
        klines = await stock_data_service.get_kline_from_db(db, stock_code, period, actual_count)
        local_data_available = bool(klines)
        
        # 5. 如果数据库没数据，确保后台更新已触发
        if not klines and not is_updating:
            debug_log_manager.log_warning(task_id, '数据库无数据，确保后台更新已触发', {
                'stock_code': stock_code
            })
            # 触发后台更新（如果之前没触发）
            result = await background_updater.submit_kline_update_task(stock_code, period)
            is_updating = result.get('success', False)
        
        # 6. 记录数据来源追踪
        await data_source_tracker.track_data_read(
            db=db,
            data_type='kline',
            stock_code=stock_code,
            data_source='db' if local_data_available else 'none',
            last_update_time=update_necessity.get('last_update'),
            is_updating=is_updating,
            metadata={'period': period, 'count': actual_count, 'quick_load': quick_load}
        )
        
        debug_log_manager.log_event(task_id, 'db_query_success', {
            'klines_count': len(klines) if klines else 0,
            'local_data_available': local_data_available,
            'is_updating': is_updating,
            'quick_load': quick_load
        })
        
        debug_log_manager.end_task(task_id, success=True)
        
        # 7. 返回本地数据语义响应
        last_update_value = update_necessity.get('last_update')
        if hasattr(last_update_value, 'isoformat'):
            last_update_value = last_update_value.isoformat()

        return {
            'data': klines,
            'metadata': {
                'stock_code': stock_code,
                'period': period,
                'count': len(klines) if klines else 0,
                'quick_load': quick_load,
                'requested_count': count,
                'actual_count': actual_count,
                'local_data_available': local_data_available,
                'is_updating': is_updating,
                'last_update': last_update_value,
                'needs_update': update_necessity.get('needs_update', False),
                'update_reason': update_necessity.get('reason')
            }
        }
        
    except Exception as e:
        debug_log_manager.log_error(task_id, '获取K线数据失败', {
            'error': str(e)
        })
        debug_log_manager.end_task(task_id, success=False, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-db/{stock_code}")
async def update_stock_kline_db(
    stock_code: str,
    period: str = Query("day", description="K线周期: day/week/month"),
    force_full: bool = Query(False, description="是否强制全量更新"),
    db: AsyncSession = Depends(get_db)
):
    """
    更新股票K线数据到数据库（异步提交模式）
    
    [WARN]️ 警告：该接口已改为异步提交模式，立即返回。
    """
    try:
        # 权限检查：只允许更新自持股票和指数
        is_allowed, reason = await is_allowed_stock_or_index(stock_code)
        if not is_allowed:
            logger.warning(f"拒绝更新 {stock_code}: {reason}")
            raise HTTPException(
                status_code=403, 
                detail=f"仅允许更新自持股票和指数数据。{reason}"
            )
        
        logger.info(f"提交异步更新任务 {stock_code}: {reason}")
        
        # 改为异步提交
        result = await background_updater.submit_kline_update_task(stock_code, period, force=force_full)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交更新K线数据任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices")
async def get_indices():
    """获取配置的指数列表"""
    try:
        if not INDICES_CONFIG_PATH.exists():
            return {'indices': []}
        
        with open(INDICES_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return {'indices': config.get('indices', [])}
    except Exception as e:
        logger.error(f"获取指数列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices/quotes")
async def get_indices_quotes(db: AsyncSession = Depends(get_db)):
    """获取指数的实时行情 (仅从数据库读取) - Non-Blocking版本"""
    try:
        # ✅ 优化：异步读取配置文件，避免阻塞
        import aiofiles
        import asyncio
        
        if not INDICES_CONFIG_PATH.exists():
            return {'indices': []}
        
        async with aiofiles.open(INDICES_CONFIG_PATH, 'r', encoding='utf-8') as f:
            content = await f.read()
            config = json.loads(content)
        
        indices = config.get('indices', [])
        if not indices:
            return {'indices': []}
        
        # 1. 批量从数据库获取实时行情
        from services.quote_data_service import quote_data_service
        codes = [idx.get('full_code', idx['code']) for idx in indices]
        quotes = await quote_data_service.get_quotes_from_db(db, codes)
        
        # 2. 后台异步更新缺失或过期的行情（不阻塞响应）
        found_codes = {q.code for q in quotes}
        for code in codes:
            # ✅ 使用 create_task 确保不阻塞
            if code not in found_codes:
                asyncio.create_task(background_updater.submit_quote_update_task(code))
            else:
                # 即使存在也触发一次后台检查更新（不阻塞）
                asyncio.create_task(background_updater.submit_quote_update_task(code))
        
        # 3. 合并指数信息和行情
        result = []
        for idx in indices:
            target_code = idx.get('full_code', idx['code'])
            # 模糊匹配
            quote = next((q for q in quotes if q.code == idx['code'] or q.code == target_code), None)
            
            result.append({
                **idx,
                'price': float(quote.price) if quote and quote.price else None,
                'change': float(quote.change) if quote and quote.change else None,
                'change_pct': float(quote.change_pct) if quote and quote.change_pct else None,
                'volume': int(quote.volume) if quote and quote.volume else None,
                'amount': float(quote.amount) if quote and quote.amount else None
            })
        
        return {
            'indices': result,
            'is_updating': len(result) < len(indices)
        }
    except Exception as e:
        logger.error(f"获取指数行情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-source/status")
async def get_data_source_status(db: AsyncSession = Depends(get_db)):
    """
    获取所有数据源的状态概览
    
    用于前端数据来源弹出框显示
    """
    try:
        from services.data_source_tracker import data_source_tracker
        
        status = await data_source_tracker.get_current_data_status(db)
        
        return {
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取数据源状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
