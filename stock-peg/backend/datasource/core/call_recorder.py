"""数据源调用记录器"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Set
from threading import Lock

from datasource.core.constants import FunctionType, DataSourceType
from datasource.core.statistics import CallRecord, CallStatus, DataSourceStatistics

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_FILE = Path(__file__).parent.parent / "datasource_config.json"


class CallRecorder:
    """调用记录器 — 记录调用、计算指标、熔断判断、JSON持久化"""

    def __init__(self):
        self.stats: Dict[DataSourceType, DataSourceStatistics] = {}
        self.lock = Lock()
        self.circuit_breaker_threshold = 3
        self.circuit_breaker_recovery_time = 180
        self.half_open_recovery_time = 60
        self.score_weights = {
            'success_rate': 0.5,
            'response_time': 0.2,
            'priority': 0.2,
            'stability': 0.1,
        }
        # JSON持久化相关
        self.config: Dict = {}
        self.disabled_sources: Set[str] = set()
        self._load_config()

    def record_call(self, function_type, source_type, status, duration_ms,
                    error_message=None, metadata=None) -> CallRecord:
        record = CallRecord(
            timestamp=datetime.now(), function_type=function_type,
            source_type=source_type, status=status, duration_ms=duration_ms,
            error_message=error_message, metadata=metadata or {},
        )
        with self.lock:
            if source_type not in self.stats:
                self.stats[source_type] = DataSourceStatistics(source_type=source_type, priority=50)
            self.stats[source_type].add_record(record)
            # 更新JSON持久化
            self._update_source_usage(source_type, status)
        return record

    def should_skip_source(self, source_type, function_type=None) -> bool:
        # 首先检查JSON配置中的禁用状态
        if not self.is_source_enabled(source_type):
            return True
        with self.lock:
            if source_type not in self.stats:
                return False
            stats = self.stats[source_type]
            if stats.consecutive_failures >= self.circuit_breaker_threshold:
                if stats.last_failure_time:
                    elapsed = (datetime.now() - stats.last_failure_time).total_seconds()
                    if elapsed >= self.circuit_breaker_recovery_time:
                        stats.consecutive_failures = 0
                        return False
                    if elapsed > self.half_open_recovery_time:
                        return False
                    return True
            return False

    def get_source_score(self, source_type, function_type, priority) -> float:
        with self.lock:
            if source_type not in self.stats:
                return 100 - priority
            stats = self.stats[source_type]
            func_stats = stats.get_function_stats(function_type)
            success_rate = func_stats.get_success_rate()
            avg_duration = func_stats.get_avg_duration()
            response_score = 100 if avg_duration == 0 else max(0, 100 - (avg_duration / 10))
            priority_score = 100 - priority
            stability_score = 100 if success_rate > 0.8 else success_rate * 100
            total = (
                success_rate * 100 * self.score_weights['success_rate']
                + response_score * self.score_weights['response_time']
                + priority_score * self.score_weights['priority']
                + stability_score * self.score_weights['stability']
            )
            return total

    def update_priority(self, source_type, priority):
        with self.lock:
            if source_type in self.stats:
                self.stats[source_type].priority = priority

    def get_statistics(self, source_type=None) -> dict:
        with self.lock:
            if source_type:
                return self.stats[source_type].to_dict() if source_type in self.stats else {}
            return {st.value: s.to_dict() for st, s in self.stats.items()}

    def reset_statistics(self, source_type=None):
        with self.lock:
            if source_type:
                self.stats.pop(source_type, None)
            else:
                self.stats.clear()

    # ==================== JSON持久化方法 ====================

    def _load_config(self):
        """从JSON加载配置"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # 加载禁用的数据源
                self.disabled_sources = set(self.config.get('disabled_sources', []))
                logger.info(f"Loaded datasource config: {len(self.disabled_sources)} disabled sources")
            else:
                self._create_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._create_default_config()

    def _create_default_config(self):
        """创建默认配置"""
        self.config = {
            "version": "1.0",
            "last_check_time": None,
            "disabled_sources": [],
            "source_usage": {},
            "settings": {
                "inactivity_threshold_days": 7,
                "auto_disable_inactive": True,
                "min_calls_before_disable": 0
            }
        }
        # 初始化所有数据源
        for ds in DataSourceType:
            self.config["source_usage"][ds.value] = {
                "last_used": None,
                "total_calls": 0,
                "success_rate": 0.0,
                "enabled": True
            }
        self._save_config()

    def _save_config(self):
        """保存配置到JSON"""
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _update_source_usage(self, source_type: DataSourceType, status: CallStatus):
        """更新数据源使用记录（用于JSON持久化）"""
        source_key = source_type.value
        if source_key not in self.config.get("source_usage", {}):
            self.config.setdefault("source_usage", {})[source_key] = {
                "last_used": None,
                "total_calls": 0,
                "success_rate": 0.0,
                "enabled": True
            }

        usage = self.config["source_usage"][source_key]
        usage["last_used"] = datetime.now().isoformat()
        usage["total_calls"] = usage.get("total_calls", 0) + 1

        # 更新成功率（简化计算）
        if status == CallStatus.SUCCESS:
            stats = self.stats.get(source_type)
            if stats:
                usage["success_rate"] = round(stats.get_overall_success_rate() * 100, 2)

    def is_source_enabled(self, source_type: DataSourceType) -> bool:
        """检查数据源是否启用"""
        source_key = source_type.value
        # 检查禁用列表
        if source_key in self.disabled_sources:
            return False
        # 检查配置中的启用状态
        usage = self.config.get("source_usage", {}).get(source_key, {})
        return usage.get("enabled", True)

    def disable_source(self, source_type: DataSourceType, reason: str = "manual"):
        """禁用数据源"""
        source_key = source_type.value
        self.disabled_sources.add(source_key)
        if source_key in self.config.get("source_usage", {}):
            self.config["source_usage"][source_key]["enabled"] = False
        # 更新禁用列表
        self.config["disabled_sources"] = list(self.disabled_sources)
        self._save_config()
        logger.warning(f"Disabled datasource {source_key}: {reason}")

    def enable_source(self, source_type: DataSourceType):
        """启用数据源"""
        source_key = source_type.value
        self.disabled_sources.discard(source_key)
        if source_key in self.config.get("source_usage", {}):
            self.config["source_usage"][source_key]["enabled"] = True
        self.config["disabled_sources"] = list(self.disabled_sources)
        self._save_config()
        logger.info(f"Enabled datasource {source_key}")

    def check_inactive_sources(self, days: int = 7) -> list:
        """检查并返回不活跃的数据源（超过指定天数未使用）"""
        inactive = []
        threshold = datetime.now() - timedelta(days=days)
        settings = self.config.get("settings", {})
        auto_disable = settings.get("auto_disable_inactive", True)

        for source_key, usage in self.config.get("source_usage", {}).items():
            if not usage.get("enabled", True):
                continue

            last_used = usage.get("last_used")
            if last_used:
                try:
                    last_time = datetime.fromisoformat(last_used)
                    if last_time < threshold:
                        inactive.append(source_key)
                        if auto_disable:
                            try:
                                ds_type = DataSourceType(source_key)
                                self.disable_source(ds_type, f"未使用超过{days}天")
                            except ValueError:
                                pass
                except (ValueError, TypeError):
                    pass
            elif usage.get("total_calls", 0) == 0:
                # 从未使用过的数据源也标记为不活跃
                inactive.append(source_key)

        # 更新最后检查时间
        self.config["last_check_time"] = datetime.now().isoformat()
        self._save_config()

        return inactive

    def get_disabled_sources(self) -> list:
        """获取所有禁用的数据源列表"""
        return list(self.disabled_sources)

    def get_source_last_used(self, source_type: DataSourceType) -> Optional[datetime]:
        """获取数据源最后使用时间"""
        source_key = source_type.value
        usage = self.config.get("source_usage", {}).get(source_key, {})
        last_used = usage.get("last_used")
        if last_used:
            try:
                return datetime.fromisoformat(last_used)
            except (ValueError, TypeError):
                return None
        return None


call_recorder = CallRecorder()
