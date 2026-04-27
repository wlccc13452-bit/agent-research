"""数据源管理器"""
import logging
import asyncio
import time
from typing import List, Optional, Dict, Any

from datasource.core.base import BaseDataSource
from datasource.core.constants import FunctionType, DataSourceType
from datasource.core.call_recorder import CallRecorder, CallStatus
from datasource.core.smart_router import SmartRouter
from datasource.core.data_source_logger import data_source_logger

logger = logging.getLogger(__name__)


class DataSourceManager:
    """
    数据源管理器

    功能:
    1. 管理多个数据源
    2. 智能路由选择最优数据源
    3. 记录调用统计
    4. 熔断保护
    5. 统一日志记录
    6. 高层便捷方法（Facade）
    """

    def __init__(self):
        self.sources: List[BaseDataSource] = []
        self.call_recorder = CallRecorder()
        self.smart_router = SmartRouter(self.call_recorder)
        self.default_strategy = "balanced"
        self.max_retries = 2
        logger.info("数据源管理器已初始化")

    def register_source(self, source: BaseDataSource):
        if source in self.sources:
            return
        self.sources.append(source)
        self.call_recorder.update_priority(source.source_type, source.priority)
        logger.info(f"注册数据源 {source.source_type.value} (优先级:{source.priority}, 支持:{len(source.supported_functions)}个功能)")

    def unregister_source(self, source_type: DataSourceType):
        self.sources = [s for s in self.sources if s.source_type != source_type]

    def get_source(self, source_type: DataSourceType) -> Optional[BaseDataSource]:
        for s in self.sources:
            if s.source_type == source_type:
                return s
        return None

    async def call(self, function_type, *args, strategy=None, retry_on_failure=True, **kwargs) -> Any:
        """按功能类型调用，自动选择最优数据源"""
        strategy = strategy or self.default_strategy
        source = self.smart_router.select_best_source(self.sources, function_type, strategy)
        if not source:
            raise Exception(f"没有可用的数据源支持功能 {function_type.name}")

        tried_sources = []
        last_error = None

        for attempt in range(self.max_retries + 1):
            if attempt > 0 and not retry_on_failure:
                break
            selected = source if attempt == 0 else self._select_next(source, function_type, strategy, tried_sources)
            if not selected:
                break
            tried_sources.append(selected.source_type)
            try:
                return await self._call_source(selected, function_type, *args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"数据源 {selected.source_type.value} 调用失败: {e}")
                if not retry_on_failure:
                    raise
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))

        raise Exception(f"所有数据源均失败: {[s.value for s in tried_sources]}") from last_error

    def _select_next(self, source, function_type, strategy, tried):
        available = [s for s in self.sources
                     if s.supports_function(function_type) and s.source_type not in tried]
        if not available:
            return None
        return self.smart_router.select_best_source(available, function_type, strategy)

    async def _call_source(self, source, function_type, *args, **kwargs) -> Any:
        methods = source.get_methods_for_function(function_type)
        if not methods:
            raise Exception(f"数据源 {source.source_type.value} 没有实现 {function_type.name}")
        method = getattr(source, methods[0])
        task_id = data_source_logger.start_call(function_type, source.source_type, methods[0], args, kwargs)
        start = time.time()
        status = CallStatus.SUCCESS
        error_message = None
        result = None
        try:
            if not await source.is_available():
                raise Exception(f"数据源 {source.source_type.value} 不可用")
            if asyncio.iscoroutinefunction(method):
                result = await method(*args, **kwargs)
            else:
                result = method(*args, **kwargs)
            ms = (time.time() - start) * 1000
            self.call_recorder.record_call(function_type, source.source_type, CallStatus.SUCCESS, ms)
            data_source_logger.log_success(task_id, result, ms)
            return result
        except asyncio.TimeoutError:
            status, error_message = CallStatus.TIMEOUT, "调用超时"
            raise
        except Exception as e:
            err = str(e)
            if "没有接口访问权限" in err or "unauthorized" in err.lower():
                status = CallStatus.UNAUTHORIZED
            elif "rate limit" in err.lower():
                status = CallStatus.RATE_LIMIT
            else:
                status = CallStatus.FAILURE
            error_message = err
            raise
        finally:
            if status != CallStatus.SUCCESS:
                ms = (time.time() - start) * 1000
                self.call_recorder.record_call(function_type, source.source_type, status, ms, error_message)
                data_source_logger.log_failure(task_id, error_message, status, ms)

    # ==================== 高层便捷方法 (Facade) ====================

    async def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """获取实时行情（自动选择最优数据源）"""
        return await self.call(FunctionType.REALTIME_QUOTE, stock_code)

    async def get_kline(self, stock_code: str, period: str = "day", count: int = 120, **kwargs) -> Optional[list]:
        """获取K线数据"""
        period_map = {"day": FunctionType.KLINE_DAILY, "week": FunctionType.KLINE_WEEKLY, "month": FunctionType.KLINE_MONTHLY}
        ft = period_map.get(period, FunctionType.KLINE_DAILY)
        return await self.call(ft, stock_code, count=count, **kwargs)

    async def get_market_sentiment(self) -> Optional[Dict]:
        """获取市场情绪数据"""
        return await self.call(FunctionType.MARKET_SENTIMENT)

    async def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """获取个股信息"""
        return await self.call(FunctionType.STOCK_INFO, stock_code)

    async def search_stock(self, keyword: str) -> Optional[str]:
        """搜索股票代码"""
        return await self.call(FunctionType.STOCK_SEARCH, keyword)

    def get_all_statistics(self) -> Dict[str, Any]:
        return self.call_recorder.get_statistics()


# 全局单例
data_source_manager = DataSourceManager()
