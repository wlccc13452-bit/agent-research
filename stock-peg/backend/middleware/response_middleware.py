"""
响应标准化中间件

功能：
1. 自动包装所有 API 响应为统一格式
2. 统一错误处理
3. 添加请求追踪 ID
4. 记录响应日志
"""
import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from models.response import APIResponse, ErrorCode, ResponseBuilder

logger = logging.getLogger(__name__)


class ResponseStandardizationMiddleware(BaseHTTPMiddleware):
    """
    响应标准化中间件
    
    自动将所有响应包装为统一的 APIResponse 格式
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # 不需要标准化的路由前缀
        self.excluded_paths = {
            "/docs",
            "/openapi.json",
            "/redoc",
            "/health",
            "/metrics",
            "/favicon.ico"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 生成请求 ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 检查是否需要排除
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # 检查是否是静态文件或 WebSocket
        if (
            request.url.path.startswith("/static") or
            request.url.path.startswith("/ws") or
            request.headers.get("upgrade") == "websocket"
        ):
            return await call_next(request)
        
        try:
            # 调用下一个中间件或路由处理器
            response = await call_next(request)
            
            # 计算响应时间
            process_time = (time.time() - start_time) * 1000
            
            # 记录响应日志
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"- {response.status_code} - {process_time:.2f}ms"
            )
            
            # 如果响应已经是 JSONResponse，不需要重复包装
            # 只包装自定义响应（如字典返回）
            return response
            
        except Exception as e:
            # 处理未捕获的异常
            logger.error(
                f"[{request_id}] Unhandled exception: {e}",
                exc_info=True
            )
            
            # 构建错误响应
            error_response = ResponseBuilder.error(
                message=f"服务器内部错误: {str(e)}",
                error_code=ErrorCode.UNKNOWN_ERROR,
                error_details={
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                },
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.model_dump()
            )


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    异常处理中间件
    
    捕获所有未处理的异常并返回标准化错误响应
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        request_id = getattr(request.state, "request_id", "unknown")
        
        try:
            return await call_next(request)
            
        except ValueError as e:
            # 参数验证错误
            logger.warning(f"[{request_id}] Validation error: {e}")
            
            error_response = ResponseBuilder.error(
                message=f"参数验证失败: {str(e)}",
                error_code=ErrorCode.INVALID_PARAM,
                error_details={"exception": str(e)},
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=400,
                content=error_response.model_dump()
            )
            
        except PermissionError as e:
            # 权限错误
            logger.warning(f"[{request_id}] Permission denied: {e}")
            
            error_response = ResponseBuilder.error(
                message="权限不足",
                error_code=ErrorCode.PERMISSION_DENIED,
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=403,
                content=error_response.model_dump()
            )
            
        except FileNotFoundError as e:
            # 资源未找到
            logger.warning(f"[{request_id}] Resource not found: {e}")
            
            error_response = ResponseBuilder.error(
                message="请求的资源不存在",
                error_code=ErrorCode.NOT_FOUND,
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=404,
                content=error_response.model_dump()
            )
            
        except TimeoutError as e:
            # 超时错误
            logger.error(f"[{request_id}] Timeout error: {e}")
            
            error_response = ResponseBuilder.error(
                message="请求超时，请稍后重试",
                error_code=ErrorCode.TIMEOUT,
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=504,
                content=error_response.model_dump()
            )
            
        except Exception as e:
            # 其他未处理的异常
            logger.error(
                f"[{request_id}] Unhandled exception: {e}",
                exc_info=True
            )
            
            error_response = ResponseBuilder.error(
                message="服务器内部错误",
                error_code=ErrorCode.UNKNOWN_ERROR,
                error_details={
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                } if logger.isEnabledFor(logging.DEBUG) else None,
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.model_dump()
            )
