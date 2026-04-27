"""HTTP请求日志中间件"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import json
from services.log_service import log_service

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """HTTP请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 记录请求开始时间
        start_time = time.time()
        
        # 读取请求体（如果存在）
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_body = json.loads(body.decode('utf-8'))
                    # 重新构建请求体，因为body()只能读取一次
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive
            except Exception as e:
                logger.debug(f"解析请求体失败: {str(e)}")
        
        # 调用下一个中间件或路由处理器
        response = await call_next(request)
        
        # 计算请求处理时间
        duration_ms = (time.time() - start_time) * 1000
        
        # 读取响应体（如果需要）
        response_body = None
        if hasattr(response, 'body'):
            try:
                response_body = json.loads(response.body.decode('utf-8'))
            except:
                pass
        
        # 记录日志
        try:
            log_service.log_http_request(
                method=request.method,
                path=str(request.url.path),
                request_data=request_body,
                response_data=response_body,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as e:
            logger.error(f"记录HTTP请求日志失败: {str(e)}")
        
        return response
