import os
import sys
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
config_dir = BACKEND_ROOT / "config"
config_init = config_dir / "__init__.py"
config_spec = importlib.util.spec_from_file_location(
    "config",
    config_init,
    submodule_search_locations=[str(config_dir)],
)
if config_spec is None or config_spec.loader is None:
    raise RuntimeError("failed to load backend config package")
config_module = importlib.util.module_from_spec(config_spec)
sys.modules["config"] = config_module
config_spec.loader.exec_module(config_module)

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{BACKEND_ROOT / 'data' / 'stock_peg.db'}")


def _load_modules() -> tuple[Any, Any]:
    from routers import stock as stock_router
    from services import extended_cache
    return stock_router, extended_cache


class _FakePMRCache:
    def __init__(self, data: Any = None) -> None:
        self.data = data

    async def get(self, *args: Any, **kwargs: Any) -> Any:
        return self.data


@pytest.mark.asyncio
async def test_get_stock_pmr_cache_hit_returns_metadata(monkeypatch: MonkeyPatch) -> None:
    stock_router, extended_cache = _load_modules()
    cached_payload = {
        "dates": ["2026-01-01"],
        "pmr5": [1.2],
        "pmr10": [1.1],
        "pmr20": [1.0],
        "pmr30": [0.9],
        "pmr60": [0.8],
    }
    monkeypatch.setattr(extended_cache, "pmr_cache", _FakePMRCache(cached_payload))

    result = await stock_router.get_stock_pmr("600219", 100, db=None)

    assert result["data"] == cached_payload
    assert result["metadata"]["data_source"] == "cache"
    assert result["metadata"]["stock_code"] == "600219"


@pytest.mark.asyncio
async def test_get_stock_pmr_cache_miss_returns_db_result(monkeypatch: MonkeyPatch) -> None:
    stock_router, extended_cache = _load_modules()
    monkeypatch.setattr(extended_cache, "pmr_cache", _FakePMRCache(None))

    async def _fake_get_kline_from_db(*args: Any, **kwargs: Any) -> list[object]:
        return [object()] * 220

    async def _fake_get_pmr(stock_code: str, days: int) -> dict[str, Any]:
        return {
            "dates": ["2026-01-01", "2026-01-02"],
            "pmr5": [1.1, 1.2],
            "pmr10": [1.0, 1.1],
            "pmr20": [0.9, 1.0],
            "pmr30": [0.8, 0.9],
            "pmr60": [0.7, 0.8],
        }

    monkeypatch.setattr(stock_router.stock_data_service, "get_kline_from_db", _fake_get_kline_from_db)
    monkeypatch.setattr(stock_router.stock_service, "get_pmr", _fake_get_pmr)

    result = await stock_router.get_stock_pmr("600219", 100, db=None)

    assert result["metadata"]["data_source"] == "db"
    assert result["metadata"]["stock_code"] == "600219"
    assert result["data"]["pmr5"] == [1.1, 1.2]


@pytest.mark.asyncio
async def test_stock_service_get_pmr_writes_cache_with_data_first(monkeypatch: MonkeyPatch) -> None:
    stock_router, extended_cache = _load_modules()
    async def _fake_cache_get(*args: Any, **kwargs: Any) -> None:
        return None

    captured = {}

    async def _fake_cache_set(data: Any, *args: Any) -> None:
        captured["data"] = data
        captured["args"] = args

    monkeypatch.setattr(extended_cache.pmr_cache, "get", _fake_cache_get)
    monkeypatch.setattr(extended_cache.pmr_cache, "set", _fake_cache_set)

    async def _fake_get_kline(*args: Any, **kwargs: Any) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(date="2026-01-01", close=10.0),
            SimpleNamespace(date="2026-01-02", close=10.5),
            SimpleNamespace(date="2026-01-03", close=10.2),
        ]

    monkeypatch.setattr(stock_router.stock_service, "get_kline", _fake_get_kline)
    monkeypatch.setattr(
        stock_router.stock_service,
        "_calculate_pmr",
        lambda klines: {"dates": [k.date for k in klines], "pmr5": [None, None, None]},
    )

    result = await stock_router.stock_service.get_pmr("600219", days=2)

    assert result["dates"] == ["2026-01-02", "2026-01-03"]
    assert captured["data"] == result
    assert captured["args"] == ("600219", 2)
