#!/usr/bin/env python3
"""Datasource 模块单元测试

测试内容：
1. 数据源初始化和注册
2. 智能路由功能
3. 熔断保护机制
4. 统一限流控制
5. 调用统计记录
6. AkshareDataSource 核心方法
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pandas as pd

# 导入待测试模块
import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from datasource import get_datasource, DataSourceType, FunctionType
from datasource.core.manager import DataSourceManager
from datasource.core.smart_router import SmartRouter
from datasource.core.rate_limiter import UnifiedRateLimiter
from datasource.core.call_recorder import CallRecorder
from datasource.sources.akshare_source import AkshareDataSource


class TestDataSourceManager:
    """测试 DataSourceManager"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = get_datasource()
        manager2 = get_datasource()
        assert manager1 is manager2, "DataSourceManager 应该是单例"
    
    def test_sources_registration(self):
        """测试数据源注册"""
        manager = get_datasource()
        assert len(manager.sources) > 0, "应该至少注册一个数据源"
        
        # 检查关键数据源
        source_types = [s.source_type for s in manager.sources]
        assert DataSourceType.TUSHARE in source_types, "应该注册 Tushare"
        assert DataSourceType.AKSHARE in source_types, "应该注册 Akshare"
    
    def test_get_source(self):
        """测试获取数据源"""
        manager = get_datasource()
        
        # 获取 Akshare 数据源
        akshare_source = manager.get_source(DataSourceType.AKSHARE)
        assert akshare_source is not None, "应该能获取 Akshare 数据源"
        assert akshare_source.source_type == DataSourceType.AKSHARE
        
        # 获取不存在的数据源
        unknown_source = manager.get_source(DataSourceType.UNKNOWN)
        assert unknown_source is None, "未知数据源应该返回 None"
    
    @pytest.mark.asyncio
    async def test_facade_methods(self):
        """测试 Facade 便捷方法"""
        manager = get_datasource()
        
        # 测试 get_realtime_quote（需要 mock）
        with patch.object(manager, 'call') as mock_call:
            mock_call.return_value = {'code': '600219', 'price': 10.5}
            result = await manager.get_realtime_quote('600219')
            assert result is not None
            mock_call.assert_called_once_with(
                FunctionType.REALTIME_QUOTE,
                stock_code='600219'
            )


class TestSmartRouter:
    """测试 SmartRouter"""
    
    def test_route_by_priority(self):
        """测试按优先级路由"""
        router = SmartRouter()
        
        # 创建模拟数据源
        source1 = Mock()
        source1.source_type = DataSourceType.TUSHARE
        source1.priority = 10
        source1.is_available = AsyncMock(return_value=True)
        
        source2 = Mock()
        source2.source_type = DataSourceType.AKSHARE
        source2.priority = 20
        source2.is_available = AsyncMock(return_value=True)
        
        sources = [source2, source1]  # 注意顺序
        router.register_sources(sources)
        
        # 路由应该选择优先级更高的 Tushare
        result = router.select_source(FunctionType.REALTIME_QUOTE)
        assert result.source_type == DataSourceType.TUSHARE
    
    @pytest.mark.asyncio
    async def test_route_with_failure(self):
        """测试失败后的路由切换"""
        router = SmartRouter()
        
        # 创建模拟数据源
        source1 = Mock()
        source1.source_type = DataSourceType.TUSHARE
        source1.priority = 10
        source1.is_available = AsyncMock(return_value=False)
        
        source2 = Mock()
        source2.source_type = DataSourceType.AKSHARE
        source2.priority = 20
        source2.is_available = AsyncMock(return_value=True)
        
        sources = [source1, source2]
        router.register_sources(sources)
        
        # Tushare 不可用，应该切换到 Akshare
        result = router.select_source(FunctionType.REALTIME_QUOTE)
        assert result.source_type == DataSourceType.AKSHARE


class TestUnifiedRateLimiter:
    """测试 UnifiedRateLimiter"""
    
    def test_rate_limit_check(self):
        """测试限流检查"""
        limiter = UnifiedRateLimiter()
        
        # 第一次调用应该允许
        assert limiter.check(DataSourceType.TUSHARE) is True
        
        # 连续快速调用可能被限流（取决于配置）
        # 这里只测试方法存在性
        for _ in range(10):
            limiter.check(DataSourceType.TUSHARE)
    
    def test_rate_limit_record(self):
        """测试限流记录"""
        limiter = UnifiedRateLimiter()
        
        # 记录调用
        limiter.record(DataSourceType.TUSHARE)
        
        # 检查内部状态（如果有）
        # 具体实现取决于 UnifiedRateLimiter 的设计


class TestCallRecorder:
    """测试 CallRecorder"""
    
    def test_record_call(self):
        """测试调用记录"""
        recorder = CallRecorder()
        
        # 记录一次成功调用
        recorder.record(
            source_type=DataSourceType.AKSHARE,
            function_type=FunctionType.REALTIME_QUOTE,
            success=True,
            duration=0.5
        )
        
        # 检查统计数据
        stats = recorder.get_statistics(DataSourceType.AKSHARE)
        assert stats is not None
        assert stats['total_calls'] == 1
        assert stats['success_calls'] == 1
        assert stats['success_rate'] == 1.0
    
    def test_record_failure(self):
        """测试失败记录"""
        recorder = CallRecorder()
        
        # 记录一次失败调用
        recorder.record(
            source_type=DataSourceType.AKSHARE,
            function_type=FunctionType.REALTIME_QUOTE,
            success=False,
            duration=0.0,
            error="Connection timeout"
        )
        
        stats = recorder.get_statistics(DataSourceType.AKSHARE)
        assert stats['total_calls'] == 1
        assert stats['failed_calls'] == 1
        assert stats['success_rate'] == 0.0
    
    def test_average_duration(self):
        """测试平均响应时间计算"""
        recorder = CallRecorder()
        
        # 记录多次调用
        durations = [0.1, 0.2, 0.3, 0.4, 0.5]
        for d in durations:
            recorder.record(
                source_type=DataSourceType.AKSHARE,
                function_type=FunctionType.REALTIME_QUOTE,
                success=True,
                duration=d
            )
        
        stats = recorder.get_statistics(DataSourceType.AKSHARE)
        expected_avg = sum(durations) / len(durations)
        assert abs(stats['avg_duration'] - expected_avg) < 0.01


class TestAkshareDataSource:
    """测试 AkshareDataSource"""
    
    @pytest.fixture
    def akshare_source(self):
        """创建 AkshareDataSource 实例"""
        return AkshareDataSource()
    
    def test_source_type(self, akshare_source):
        """测试数据源类型"""
        assert akshare_source.source_type == DataSourceType.AKSHARE
    
    def test_priority(self, akshare_source):
        """测试优先级"""
        assert akshare_source.priority == 20
    
    @pytest.mark.asyncio
    async def test_is_available(self, akshare_source):
        """测试可用性检查"""
        # 应该能正常调用
        available = await akshare_source.is_available()
        assert isinstance(available, bool)
    
    @pytest.mark.asyncio
    async def test_get_realtime_quote_mock(self, akshare_source):
        """测试实时行情（使用 mock）"""
        with patch.object(akshare_source, '_call_akshare') as mock_call:
            # 模拟返回数据
            mock_df = pd.DataFrame({
                '代码': ['600219'],
                '名称': ['南山铝业'],
                '最新价': [10.5],
                '涨跌幅': [2.5],
                '成交量': [1000000]
            })
            mock_call.return_value = mock_df
            
            # 调用方法
            result = await akshare_source.get_realtime_quote('600219')
            
            # 验证结果
            assert result is not None
            assert result['code'] == '600219'
    
    @pytest.mark.asyncio
    async def test_get_kline_mock(self, akshare_source):
        """测试K线数据（使用 mock）"""
        with patch.object(akshare_source, '_call_akshare') as mock_call:
            # 模拟返回数据
            mock_df = pd.DataFrame({
                '日期': ['2026-03-22', '2026-03-21'],
                '开盘': [10.0, 9.8],
                '收盘': [10.5, 10.0],
                '最高': [10.6, 10.2],
                '最低': [9.9, 9.7],
                '成交量': [1000000, 1200000]
            })
            mock_call.return_value = mock_df
            
            # 调用方法
            result = await akshare_source.get_kline('600219', 'day', 10)
            
            # 验证结果
            assert result is not None
            assert len(result) == 2
            assert result[0]['date'] == '2026-03-22'
    
    def test_failure_cache(self, akshare_source):
        """测试失败缓存"""
        # 添加到失败缓存
        akshare_source._add_to_failure_cache('600219', 'get_kline', hours=1)
        
        # 检查是否在缓存中
        is_cached = akshare_source._is_in_failure_cache('600219', 'get_kline')
        assert is_cached is True
        
        # 清除缓存
        akshare_source._clear_failure_cache('600219', 'get_kline')
        is_cached = akshare_source._is_in_failure_cache('600219', 'get_kline')
        assert is_cached is False


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        manager = get_datasource()
        
        # 1. 获取数据源
        akshare_source = manager.get_source(DataSourceType.AKSHARE)
        assert akshare_source is not None
        
        # 2. 检查可用性
        available = await akshare_source.is_available()
        
        # 3. 如果可用，尝试获取数据
        if available:
            # 使用 mock 避免实际网络调用
            with patch.object(akshare_source, '_call_akshare') as mock_call:
                mock_df = pd.DataFrame({
                    '代码': ['600219'],
                    '名称': ['南山铝业'],
                    '最新价': [10.5]
                })
                mock_call.return_value = mock_df
                
                result = await akshare_source.get_realtime_quote('600219')
                assert result is not None
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self):
        """测试 fallback 机制"""
        manager = get_datasource()
        
        # 模拟高优先级数据源失败
        # 应该自动切换到低优先级数据源
        # 具体测试取决于 SmartRouter 的实现
        pass


# ============ 运行测试 ============

if __name__ == "__main__":
    # 运行 pytest
    pytest.main([__file__, "-v", "-s"])
