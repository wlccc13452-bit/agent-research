"""数据源基类"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from datasource.core.metaclass import DataSourceMeta
from datasource.core.constants import FunctionType, DataSourceType


class BaseDataSource(ABC, metaclass=DataSourceMeta):
    """
    数据源基类

    子类需要实现:
    - source_type: 数据源类型
    - priority: 优先级（数字越小优先级越高）
    - is_available(): 检查数据源是否可用

    子类可以使用 @provider 装饰器标记支持的功能:
    - @provider(FunctionType.REALTIME_QUOTE)
    - async def get_realtime_quote(self, code: str): ...
    """

    # 由元类自动填充
    supported_functions: set = set()       # Set[FunctionType]
    _function_methods: dict = {}           # Dict[FunctionType, List[str]]

    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        """数据源类型"""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """优先级（数字越小优先级越高）"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """检查数据源是否可用"""
        pass

    def supports_function(self, function_type) -> bool:
        """检查是否支持某功能"""
        if isinstance(function_type, str):
            try:
                function_type = FunctionType[function_type.upper()]
            except KeyError:
                return False
        return function_type in self.supported_functions

    def get_methods_for_function(self, function_type) -> list:
        """获取支持某功能的所有方法名"""
        if isinstance(function_type, str):
            try:
                function_type = FunctionType[function_type.upper()]
            except KeyError:
                return []
        return self._function_methods.get(function_type, [])

    def get_source_info(self) -> Dict[str, Any]:
        """获取数据源信息"""
        return {
            'type': self.source_type.value,
            'priority': self.priority,
            'supported_functions': [f.name for f in self.supported_functions],
            'available': None,
        }
