"""数据源提供者装饰器"""
from typing import Callable, Set, Union
from functools import wraps
from datasource.core.constants import FunctionType


def provider(*function_types: Union[FunctionType, str]) -> Callable:
    """
    装饰器：标记方法支持的功能类型

    用法:
        @provider(FunctionType.REALTIME_QUOTE)
        async def get_quote(self, code: str):
            ...

        @provider("realtime_quote", "kline_daily")  # 也支持字符串
        async def get_quote(self, code: str):
            ...
    """
    def decorator(method: Callable) -> Callable:
        func_types: Set[FunctionType] = set()
        for ft in function_types:
            if isinstance(ft, str):
                try:
                    func_types.add(FunctionType[ft.upper()])
                except KeyError:
                    raise ValueError(f"Unknown function type: {ft}")
            else:
                func_types.add(ft)

        method._provider_functions = func_types

        @wraps(method)
        async def async_wrapper(*args, **kwargs):
            return await method(*args, **kwargs)

        @wraps(method)
        def sync_wrapper(*args, **kwargs):
            return method(*args, **kwargs)

        import asyncio
        if asyncio.iscoroutinefunction(method):
            async_wrapper._provider_functions = func_types
            return async_wrapper
        else:
            sync_wrapper._provider_functions = func_types
            return sync_wrapper

    return decorator
