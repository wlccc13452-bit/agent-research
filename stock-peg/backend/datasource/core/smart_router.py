"""智能路由 - 选择最优数据源"""
import logging
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

from datasource.core.constants import FunctionType, DataSourceType
from datasource.core.call_recorder import CallRecorder

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    BALANCED = "balanced"
    FASTEST = "fastest"
    RELIABLE = "reliable"
    DEFAULT = "default"


class SmartRouter:
    """智能路由器 — 根据历史记录选择最优数据源"""

    def __init__(self, call_recorder: CallRecorder):
        self.call_recorder = call_recorder
        self.strategy_weights = {
            RoutingStrategy.BALANCED: {'history': 0.6, 'priority': 0.4},
            RoutingStrategy.FASTEST: {'history': 0.4, 'priority': 0.6},
            RoutingStrategy.RELIABLE: {'history': 0.8, 'priority': 0.2},
            RoutingStrategy.DEFAULT: {'history': 0.0, 'priority': 1.0},
        }

    def select_best_source(self, sources, function_type, strategy="balanced"):
        if not sources:
            return None
        candidates = [s for s in sources if s.supports_function(function_type)]
        if not candidates:
            return None
        available = [s for s in candidates
                     if not self.call_recorder.should_skip_source(s.source_type, function_type)]
        if not available:
            return min(candidates, key=lambda s: s.priority)
        if len(available) == 1:
            return available[0]
        try:
            rs = RoutingStrategy(strategy.lower())
        except ValueError:
            rs = RoutingStrategy.BALANCED
        weights = self.strategy_weights.get(rs, self.strategy_weights[RoutingStrategy.BALANCED])
        best = max(available, key=lambda s: (
            self.call_recorder.get_source_score(s.source_type, function_type, s.priority) * weights['history']
            + (100 - s.priority) * weights['priority']
        ))
        return best

    def get_source_ranking(self, sources, function_type) -> List[Dict]:
        ranking = []
        for source in sources:
            if not source.supports_function(function_type):
                continue
            score = self.call_recorder.get_source_score(source.source_type, function_type, source.priority)
            ranking.append({
                'source_type': source.source_type.value,
                'score': round(score, 2),
                'priority': source.priority,
                'skipped': self.call_recorder.should_skip_source(source.source_type, function_type),
            })
        return sorted(ranking, key=lambda x: x['score'], reverse=True)
