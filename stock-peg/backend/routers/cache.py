"""
缓存管理 API 路由

提供缓存管理功能：
1. 查看缓存统计
2. 清空缓存
3. 删除特定缓存项
"""
from fastapi import APIRouter, HTTPException
from models.response import APIResponse, ResponseBuilder
from services.cache_service import global_cache_service, cache_stats, cache_clear, cache_delete
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats", response_model=APIResponse)
async def get_cache_stats():
    """
    获取缓存统计信息
    
    Returns:
        缓存统计信息（命中率、大小等）
    """
    try:
        stats = cache_stats()
        
        return ResponseBuilder.success(
            data=stats,
            message="缓存统计信息"
        )
        
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear", response_model=APIResponse)
async def clear_cache():
    """
    清空缓存
    
    Returns:
        操作结果
    """
    try:
        cache_clear()
        
        logger.info("缓存已清空")
        
        return ResponseBuilder.success(
            message="缓存已清空"
        )
        
    except Exception as e:
        logger.error(f"清空缓存失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{key}", response_model=APIResponse)
async def delete_cache_item(key: str):
    """
    删除特定缓存项
    
    Args:
        key: 缓存键
        
    Returns:
        操作结果
    """
    try:
        deleted = cache_delete(key)
        
        if deleted:
            return ResponseBuilder.success(
                message=f"缓存项 '{key}' 已删除"
            )
        else:
            return ResponseBuilder.error(
                message=f"缓存项 '{key}' 不存在",
                error_code="CACHE_NOT_FOUND"
            )
        
    except Exception as e:
        logger.error(f"删除缓存项失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup", response_model=APIResponse)
async def cleanup_expired_cache():
    """
    清理过期缓存项
    
    Returns:
        清理的项数
    """
    try:
        cleaned = global_cache_service.cleanup_expired()
        
        logger.info(f"清理了 {cleaned} 个过期缓存项")
        
        return ResponseBuilder.success(
            data={"cleaned_count": cleaned},
            message=f"清理了 {cleaned} 个过期缓存项"
        )
        
    except Exception as e:
        logger.error(f"清理过期缓存失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
