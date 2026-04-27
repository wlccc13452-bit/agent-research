"""
客户端日志API
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from services.websocket_manager import manager

router = APIRouter()


class ErrorLogRequest(BaseModel):
    """错误日志请求模型"""
    error: dict
    errorInfo: Optional[dict] = None
    timestamp: str
    userAgent: str
    url: str


@router.post("/log-error")
async def log_error(log_data: ErrorLogRequest):
    """接收前端错误日志
    
    Args:
        log_data: 错误日志数据
        
    Returns:
        dict: 成功响应
    """
    # 简单记录到控制台
    print(f"\n[CLIENT ERROR] {log_data.timestamp}")
    print(f"  URL: {log_data.url}")
    print(f"  Error: {log_data.error.get('message', 'Unknown')}")
    
    # 如果错误消息太长，截断
    if log_data.error.get('stack'):
        stack_preview = log_data.error['stack'][:200]
        print(f"  Stack: {stack_preview}...")
    
    # 可以扩展：保存到数据库或文件
    # 这里简化处理，只打印到控制台
    
    return {"status": "logged", "timestamp": datetime.now().isoformat()}


@router.get("/stats")
async def get_client_log_stats():
    """获取客户端日志统计信息"""
    try:
        stats = await manager.client_log_handler.get_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_logs(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """获取指定会话的客户端日志"""
    try:
        logs = await manager.client_log_handler.get_session_logs(session_id, limit)
        return {
            "success": True,
            "session_id": session_id,
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
