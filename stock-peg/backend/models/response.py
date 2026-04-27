"""
统一 API 响应格式

提供标准化的 API 响应结构，包括：
- 成功响应
- 错误响应
- 分页响应
- 批量操作响应
"""
from typing import Any, Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """
    统一 API 响应格式
    
    Attributes:
        success: 是否成功
        message: 响应消息
        data: 响应数据
        error_code: 错误码（失败时）
        error_details: 错误详情（失败时）
        timestamp: 时间戳
        request_id: 请求ID（用于追踪）
    """
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    error_code: Optional[str] = Field(None, description="错误码")
    error_details: Optional[dict[str, Any]] = Field(None, description="错误详情")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="时间戳"
    )
    request_id: Optional[str] = Field(None, description="请求ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {"id": 1, "name": "示例"},
                "timestamp": "2026-03-19T02:30:00",
                "request_id": "req_abc123"
            }
        }


class PagedResponse(BaseModel, Generic[T]):
    """
    分页响应格式
    
    Attributes:
        success: 是否成功
        message: 响应消息
        data: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页大小
        total_pages: 总页数
        has_next: 是否有下一页
        has_prev: 是否有上一页
    """
    success: bool = Field(default=True, description="是否成功")
    message: str = Field(default="查询成功", description="响应消息")
    data: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "查询成功",
                "data": [{"id": 1, "name": "示例1"}, {"id": 2, "name": "示例2"}],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "has_next": True,
                "has_prev": False,
                "timestamp": "2026-03-19T02:30:00"
            }
        }


class BatchResponse(BaseModel, Generic[T]):
    """
    批量操作响应格式
    
    Attributes:
        success: 是否成功
        message: 响应消息
        total: 总操作数
        succeeded: 成功数
        failed: 失败数
        results: 详细结果列表
        errors: 错误列表
    """
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    total: int = Field(..., description="总操作数")
    succeeded: int = Field(..., description="成功数")
    failed: int = Field(..., description="失败数")
    results: List[dict[str, Any]] = Field(default_factory=list, description="详细结果")
    errors: List[dict[str, Any]] = Field(default_factory=list, description="错误列表")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "批量操作完成",
                "total": 10,
                "succeeded": 8,
                "failed": 2,
                "results": [
                    {"id": 1, "success": True},
                    {"id": 2, "success": False, "error": "无效ID"}
                ],
                "errors": [
                    {"id": 2, "error": "无效ID"}
                ],
                "timestamp": "2026-03-19T02:30:00"
            }
        }


class ErrorResponse(BaseModel):
    """
    错误响应格式
    
    Attributes:
        success: 固定为 False
        message: 错误消息
        error_code: 错误码
        error_type: 错误类型
        details: 错误详情
        stack_trace: 堆栈跟踪（仅开发环境）
        timestamp: 时间戳
        request_id: 请求ID
    """
    success: bool = Field(default=False, description="是否成功")
    message: str = Field(..., description="错误消息")
    error_code: str = Field(..., description="错误码")
    error_type: str = Field(..., description="错误类型")
    details: Optional[dict[str, Any]] = Field(None, description="错误详情")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪（仅开发环境）")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="时间戳"
    )
    request_id: Optional[str] = Field(None, description="请求ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "无效的参数",
                "error_code": "INVALID_PARAM",
                "error_type": "ValidationError",
                "details": {"field": "stock_code", "reason": "不能为空"},
                "timestamp": "2026-03-19T02:30:00",
                "request_id": "req_abc123"
            }
        }


# 错误码定义
class ErrorCode:
    """错误码常量"""
    
    # 通用错误 (1xxx)
    UNKNOWN_ERROR = "ERR_1000"
    INVALID_PARAM = "ERR_1001"
    MISSING_PARAM = "ERR_1002"
    INVALID_FORMAT = "ERR_1003"
    
    # 认证错误 (2xxx)
    UNAUTHORIZED = "ERR_2000"
    INVALID_TOKEN = "ERR_2001"
    TOKEN_EXPIRED = "ERR_2002"
    PERMISSION_DENIED = "ERR_2003"
    
    # 资源错误 (3xxx)
    NOT_FOUND = "ERR_3000"
    ALREADY_EXISTS = "ERR_3001"
    RESOURCE_LOCKED = "ERR_3002"
    
    # 业务错误 (4xxx)
    STOCK_NOT_FOUND = "ERR_4000"
    INVALID_STOCK_CODE = "ERR_4001"
    NO_DATA_AVAILABLE = "ERR_4002"
    DATA_UPDATE_FAILED = "ERR_4003"
    
    # 系统错误 (5xxx)
    DATABASE_ERROR = "ERR_5000"
    EXTERNAL_API_ERROR = "ERR_5001"
    TIMEOUT = "ERR_5002"
    RATE_LIMIT_EXCEEDED = "ERR_5003"


# 响应构建器
class ResponseBuilder:
    """响应构建器"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        request_id: Optional[str] = None
    ) -> APIResponse:
        """构建成功响应"""
        return APIResponse(
            success=True,
            message=message,
            data=data,
            request_id=request_id
        )
    
    @staticmethod
    def error(
        message: str,
        error_code: str = ErrorCode.UNKNOWN_ERROR,
        error_details: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> APIResponse:
        """构建错误响应"""
        return APIResponse(
            success=False,
            message=message,
            error_code=error_code,
            error_details=error_details,
            request_id=request_id
        )
    
    @staticmethod
    def paged(
        data: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "查询成功"
    ) -> PagedResponse:
        """构建分页响应"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        return PagedResponse(
            success=True,
            message=message,
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    
    @staticmethod
    def batch(
        results: List[dict[str, Any]],
        message: str = "批量操作完成"
    ) -> BatchResponse:
        """构建批量操作响应"""
        succeeded = sum(1 for r in results if r.get("success", False))
        failed = len(results) - succeeded
        errors = [r for r in results if not r.get("success", False)]
        
        return BatchResponse(
            success=failed == 0,
            message=message,
            total=len(results),
            succeeded=succeeded,
            failed=failed,
            results=results,
            errors=errors
        )
