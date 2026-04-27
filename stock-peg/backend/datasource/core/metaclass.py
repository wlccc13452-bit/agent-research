"""数据源元类 - 自动收集支持的功能"""
from typing import Set, Dict, Type
from abc import ABCMeta
from datasource.core.constants import FunctionType


class DataSourceMeta(ABCMeta):
    """
    数据源元类，自动扫描并收集类中所有被@provider装饰的方法
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, name, bases, namespace)

        supported_functions: Set[FunctionType] = set()

        for base in bases:
            if hasattr(base, 'supported_functions'):
                supported_functions.update(base.supported_functions)

        for attr_name, attr_value in namespace.items():
            if callable(attr_value) and hasattr(attr_value, '_provider_functions'):
                supported_functions.update(attr_value._provider_functions)

        cls.supported_functions = supported_functions

        function_methods: Dict[FunctionType, list] = {}
        for func_type in supported_functions:
            function_methods[func_type] = []

        for attr_name in dir(cls):
            attr_value = getattr(cls, attr_name)
            if callable(attr_value) and hasattr(attr_value, '_provider_functions'):
                for func_type in attr_value._provider_functions:
                    if func_type not in function_methods:
                        function_methods[func_type] = []
                    function_methods[func_type].append(attr_name)

        cls._function_methods = function_methods

        return cls
