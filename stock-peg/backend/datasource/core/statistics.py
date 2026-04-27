"""数据源调用统计"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from datasource.core.constants import FunctionType, DataSourceType


class CallStatus(Enum):
    """调用状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    UNAUTHORIZED = "unauthorized"


@dataclass
class CallRecord:
    """单次调用记录"""
    timestamp: datetime
    function_type: FunctionType
    source_type: DataSourceType
    status: CallStatus
    duration_ms: float
    error_message: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'function_type': self.function_type.name,
            'source_type': self.source_type.value,
            'status': self.status.value,
            'duration_ms': round(self.duration_ms, 2),
            'error_message': self.error_message,
        }


@dataclass
class FunctionStatistics:
    """单个功能的统计数据"""
    function_type: FunctionType
    total_calls: int = 0
    success_calls: int = 0
    failure_calls: int = 0
    timeout_calls: int = 0
    rate_limit_calls: int = 0
    unauthorized_calls: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    recent_records: List[CallRecord] = field(default_factory=list)
    max_recent_records: int = 100
    success_rate_window: int = 20
    recent_success: List[bool] = field(default_factory=list)

    def add_record(self, record: CallRecord):
        self.total_calls += 1
        status_map = {
            CallStatus.SUCCESS: 'success_calls',
            CallStatus.FAILURE: 'failure_calls',
            CallStatus.TIMEOUT: 'timeout_calls',
            CallStatus.RATE_LIMIT: 'rate_limit_calls',
            CallStatus.UNAUTHORIZED: 'unauthorized_calls',
        }
        attr = status_map.get(record.status)
        if attr:
            setattr(self, attr, getattr(self, attr) + 1)
        self.total_duration_ms += record.duration_ms
        self.avg_duration_ms = self.total_duration_ms / self.total_calls
        self.min_duration_ms = min(self.min_duration_ms, record.duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, record.duration_ms)
        self.recent_records.append(record)
        if len(self.recent_records) > self.max_recent_records:
            self.recent_records.pop(0)
        self.recent_success.append(record.status == CallStatus.SUCCESS)
        if len(self.recent_success) > self.success_rate_window:
            self.recent_success.pop(0)

    def get_success_rate(self) -> float:
        if not self.recent_success:
            return 0.0
        return sum(self.recent_success) / len(self.recent_success)

    def get_avg_duration(self) -> float:
        if not self.recent_records:
            return 0.0
        return sum(r.duration_ms for r in self.recent_records) / len(self.recent_records)

    def to_dict(self) -> dict:
        return {
            'function_type': self.function_type.name,
            'total_calls': self.total_calls,
            'success_calls': self.success_calls,
            'failure_calls': self.failure_calls,
            'success_rate': round(self.get_success_rate() * 100, 2),
            'avg_duration_ms': round(self.avg_duration_ms, 2),
            'min_duration_ms': round(self.min_duration_ms, 2) if self.min_duration_ms != float('inf') else 0,
            'max_duration_ms': round(self.max_duration_ms, 2),
        }


@dataclass
class DataSourceStatistics:
    """单个数据源的统计数据"""
    source_type: DataSourceType
    priority: int
    function_stats: dict = field(default_factory=dict)
    total_calls: int = 0
    success_calls: int = 0
    last_call_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0

    def get_function_stats(self, function_type: FunctionType) -> FunctionStatistics:
        if function_type not in self.function_stats:
            self.function_stats[function_type] = FunctionStatistics(function_type=function_type)
        return self.function_stats[function_type]

    def add_record(self, record: CallRecord):
        self.total_calls += 1
        if record.status == CallStatus.SUCCESS:
            self.success_calls += 1
            self.last_success_time = record.timestamp
            self.consecutive_failures = 0
        else:
            self.last_failure_time = record.timestamp
            self.consecutive_failures += 1
        self.last_call_time = record.timestamp
        self.get_function_stats(record.function_type).add_record(record)

    def get_overall_success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.success_calls / self.total_calls

    def to_dict(self) -> dict:
        return {
            'source_type': self.source_type.value,
            'priority': self.priority,
            'total_calls': self.total_calls,
            'success_calls': self.success_calls,
            'overall_success_rate': round(self.get_overall_success_rate() * 100, 2),
            'consecutive_failures': self.consecutive_failures,
        }
