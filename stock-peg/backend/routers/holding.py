"""持仓管理路由"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging
import asyncio

from models import (
    Holdings,
    AddStockRequest,
    RemoveStockRequest,
    UpdateStockRequest,
    UpdateStockTargetRequest,
    AddSectorRequest,
    RenameSectorRequest,
    StockInfo,
    SectorInfo
)
from services import HoldingManager
from config.settings import settings

logger = logging.getLogger(__name__)

# 创建持仓管理器
holding_manager = HoldingManager(settings.holdings_file_path)

router = APIRouter()


async def _check_and_resolve_unknown_holdings(holdings: Holdings):
    """检查并异步解析自持股票中的UNKNOWN代码
    
    使用后台线程确保任务不受请求生命周期影响
    """
    if not holdings or not holdings.sectors:
        return
    
    unknown_stocks = []
    for sector in holdings.sectors:
        for stock in sector.stocks:
            if stock.code and stock.code.startswith('UNKNOWN'):
                unknown_stocks.append((stock.code, stock.name))
    
    if not unknown_stocks:
        return
    
    logger.info(f"[UNKNOWN-HOLDINGS] 发现 {len(unknown_stocks)} 个UNKNOWN自持股票，启动异步解析")
    
    # 使用后台线程启动解析任务
    import threading
    
    def run_async_task():
        """在新线程中运行异步任务"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                from services.background_updater import background_updater
                
                async def resolve_all():
                    for stock_code, stock_name in unknown_stocks:
                        try:
                            logger.info(f"[UNKNOWN-HOLDINGS] 开始解析: {stock_name} ({stock_code})")
                            
                            result = await background_updater.submit_kline_update_task(
                                stock_code, 
                                period='day', 
                                force=False
                            )
                            
                            logger.info(f"[UNKNOWN-HOLDINGS] 解析结果: {stock_name} - {result}")
                        except Exception as e:
                            logger.error(f"[UNKNOWN-HOLDINGS] 解析失败 {stock_name}: {str(e)}")
                
                loop.run_until_complete(resolve_all())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"[UNKNOWN-HOLDINGS] 后台线程失败: {str(e)}")
    
    # 启动后台线程
    thread = threading.Thread(target=run_async_task, daemon=True)
    thread.start()
    
    logger.info(f"[UNKNOWN-HOLDINGS] 已启动后台解析线程")


@router.get("/", response_model=Holdings)
async def get_holdings():
    """获取持仓数据 - Non-Blocking版本
    
    核心原则：
    1. 立即返回现有数据或空数据（不等待任何IO操作）
    2. 后台异步加载真实数据
    3. 更新完成后通过WebSocket推送通知
    4. 返回 sync_status 告知前端数据同步状态
    """
    try:
        logger.warning("📡 收到获取自持股票请求")
        
        # 获取预加载状态
        from main import _preload_state
        sync_status = _preload_state.get('status', 'pending')
        sync_progress = _preload_state.get('progress', 0)
        sync_message = _preload_state.get('message', '')
        
        # 步骤1：立即返回现有数据（如果有缓存）
        if holding_manager.holdings:
            total_sectors = len(holding_manager.holdings.sectors)
            total_stocks = sum(len(s.stocks) for s in holding_manager.holdings.sectors)
            logger.warning(f"📡 立即返回缓存数据: {total_sectors} 个板块, {total_stocks} 只股票")
            
            # 检查是否需要后台更新
            import os
            import asyncio
            try:
                current_modified = await asyncio.to_thread(os.path.getmtime, holding_manager.file_path)
                if current_modified != holding_manager.last_modified:
                    logger.info("📡 文件已修改，启动后台更新...")
                    asyncio.create_task(holding_manager._reload_holdings_background())
            except Exception as e:
                logger.warning(f"检查文件修改时间失败: {str(e)}")
            
            # 返回数据，包含同步状态
            result = holding_manager.holdings.model_dump() if hasattr(holding_manager.holdings, 'model_dump') else holding_manager.holdings
            result['sync_status'] = sync_status
            result['sync_progress'] = sync_progress
            result['sync_message'] = sync_message
            return result
        
        # 步骤2：无缓存时，立即返回空数据，后台异步加载
        logger.warning("📡 无缓存数据，立即返回空数据，后台异步加载...")
        asyncio.create_task(holding_manager.load_holdings())
        
        # 返回空数据，包含同步状态（前端会在收到WebSocket通知后刷新）
        return {
            "sectors": [],
            "last_updated": None,
            "sync_status": sync_status,
            "sync_progress": sync_progress,
            "sync_message": sync_message
        }
    except Exception as e:
        logger.error(f"获取持仓数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_holdings():
    """强制重新从文件加载持仓数据"""
    try:
        holdings = await holding_manager.load_holdings()
        # 广播更新通知给所有WebSocket客户端
        try:
            from services.realtime_pusher import realtime_pusher
            from datetime import datetime
            await realtime_pusher.broadcast({
                "type": "holdings_updated",
                "message": "持仓数据已手动刷新",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.warning(f"广播持仓更新失败: {str(e)}")
            
        return {"message": "成功重新加载自持数据", "count": len(holdings.sectors)}
    except Exception as e:
        logger.error(f"刷新持仓数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock")
async def add_stock(request: AddStockRequest):
    """添加股票"""
    try:
        success = await holding_manager.add_stock(
            request.sector_name,
            request.stock_name,
            request.stock_code
        )
        if success:
            return {"message": f"成功添加股票 {request.stock_name}"}
        else:
            raise HTTPException(status_code=400, detail="添加股票失败")
    except Exception as e:
        logger.error(f"添加股票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stock")
async def remove_stock(request: RemoveStockRequest):
    """删除股票"""
    try:
        success = await holding_manager.remove_stock(
            request.sector_name,
            request.stock_name
        )
        if success:
            return {"message": f"成功删除股票 {request.stock_name}"}
        else:
            raise HTTPException(status_code=400, detail="删除股票失败")
    except Exception as e:
        logger.error(f"删除股票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/stock")
async def update_stock(request: UpdateStockRequest):
    """更新股票信息"""
    try:
        success = await holding_manager.update_stock(
            request.sector_name,
            request.old_name,
            request.new_name,
            request.new_code,
            request.new_sector
        )
        if success:
            return {"message": f"成功更新股票 {request.old_name}"}
        else:
            raise HTTPException(status_code=400, detail="更新股票失败")
    except Exception as e:
        logger.error(f"更新股票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sector")
async def add_sector(request: AddSectorRequest):
    """添加板块"""
    try:
        success = await holding_manager.add_sector(request.sector_name)
        if success:
                return {"message": f"成功添加板块 {request.sector_name}"}
        else:
            raise HTTPException(status_code=400, detail="添加板块失败")
    except Exception as e:
        logger.error(f"添加板块失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sector/{sector_name}")
async def remove_sector(sector_name: str):
    """删除板块"""
    try:
        success = await holding_manager.remove_sector(sector_name)
        if success:
                return {"message": f"成功删除板块 {sector_name}"}
        else:
            raise HTTPException(status_code=400, detail="删除板块失败")
    except Exception as e:
        logger.error(f"删除板块失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sector")
async def rename_sector(request: RenameSectorRequest):
    """重命名板块"""
    try:
        success = await holding_manager.rename_sector(
            request.old_name,
            request.new_name
        )
        if success:
            return {"message": f"成功重命名板块 {request.old_name} 为 {request.new_name}"}
        else:
            raise HTTPException(status_code=400, detail="重命名板块失败")
    except Exception as e:
        logger.error(f"重命名板块失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors", response_model=List[SectorInfo])
async def get_sectors():
    """获取所有板块"""
    try:
        holdings = await holding_manager.load_holdings()
        return holdings.sectors
    except Exception as e:
        logger.error(f"获取板块列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector/{sector_name}/stocks", response_model=List[StockInfo])
async def get_sector_stocks(sector_name: str):
    """获取指定板块的股票列表"""
    try:
        holdings = await holding_manager.load_holdings()
        sector = next((s for s in holdings.sectors if s.name == sector_name), None)
        if not sector:
            raise HTTPException(status_code=404, detail=f"板块 {sector_name} 不存在")
        return sector.stocks
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取板块股票列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/stock/target")
async def update_stock_target(request: UpdateStockTargetRequest):
    """更新股票目标价和涨跌控制比例"""
    try:
        success = await holding_manager.update_stock_target(
            request.sector_name,
            request.stock_name,
            request.target_price,
            request.change_up_pct,
            request.change_down_pct
        )
        if success:
            return {"message": f"成功更新股票 {request.stock_name} 的目标价设置"}
        else:
            raise HTTPException(status_code=400, detail="更新股票目标价失败")
    except Exception as e:
        logger.error(f"更新股票目标价失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
