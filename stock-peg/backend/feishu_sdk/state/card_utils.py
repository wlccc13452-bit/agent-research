"""
Card Utils - 卡片工具函数

提供卡片处理相关的工具函数：
- 按钮名称处理
- Action value 规范化
- 按钮禁用
- 卡片结构遍历
"""

import copy
import hashlib
import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
_ACTION_DEDUP_LOCK = threading.Lock()
_ACTION_DEDUP_CACHE: dict[str, float] = {}
_DEDUP_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "card_action_dedup.db"
_DEDUP_DB_INIT = False
_DEDUP_DB_CLEANUP_AT = 0.0


def ensure_button_names(card: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure all buttons have name field for proper callback
    
    Feishu requires all interactive buttons to have a unique 'name' field
    to properly trigger callback events.
    
    Args:
        card: Card JSON structure
        
    Returns:
        Card with all buttons having name field
    """
    button_counter = 0
    used_names: set[str] = set()
    
    def walk(node: Any) -> None:
        nonlocal button_counter
        if isinstance(node, dict):
            if node.get("tag") == "button":
                action_value = node.get("value", {})
                action_type = action_value.get("action", "") if isinstance(action_value, dict) else ""
                base_name = f"btn_{action_type}" if action_type else "btn"
                current_name = str(node.get("name", "")).strip()

                if current_name and current_name not in used_names:
                    used_names.add(current_name)
                else:
                    candidate = f"{base_name}_{button_counter}"
                    while candidate in used_names:
                        button_counter += 1
                        candidate = f"{base_name}_{button_counter}"
                    node["name"] = candidate
                    used_names.add(candidate)
                    button_counter += 1
                    logger.debug(f"Set unique button name '{candidate}'")
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    
    walk(card)
    
    if button_counter > 0:
        logger.info(f"Ensured {button_counter} buttons have name field")
    
    return card


def ensure_flat_action_values(card: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure action values are flat dictionaries, not nested
    
    Fixes: value.value -> value
    
    Args:
        card: Card JSON structure
        
    Returns:
        Card with normalized action values
    """
    def normalize(node: Any) -> Any:
        if isinstance(node, dict):
            if "value" in node:
                raw_value = node.get("value")
                if isinstance(raw_value, dict) and len(raw_value) == 1 and isinstance(raw_value.get("value"), dict):
                    node["value"] = raw_value["value"]
                elif raw_value is None:
                    node["value"] = {}
            for key, value in list(node.items()):
                node[key] = normalize(value)
            return node
        if isinstance(node, list):
            return [normalize(item) for item in node]
        return node

    normalized_card = normalize(card)
    return normalized_card if isinstance(normalized_card, dict) else card


def disable_all_buttons(card: dict) -> dict:
    """
    Recursively disable all buttons in card JSON
    
    **递归策略**:
    1. 遍历所有 elements
    2. 对于 action 元素,禁用所有 buttons
    3. 递归处理嵌套结构 (columns, elements)
    
    Args:
        card: Card JSON structure
        
    Returns:
        Card with all buttons disabled
    """
    def disable_buttons_recursive(node: Any) -> None:
        """Recursively process card structure"""
        if isinstance(node, dict):
            # Process action elements
            if node.get("tag") == "action":
                for action in node.get("actions", []):
                    if action.get("tag") == "button":
                        action["disabled"] = True
            
            # Process columns in column_set
            if node.get("tag") == "column_set":
                for column in node.get("columns", []):
                    for element in column.get("elements", []):
                        disable_buttons_recursive(element)
            
            # Recursively process nested elements
            if "elements" in node:
                for element in node["elements"]:
                    disable_buttons_recursive(element)
        
        elif isinstance(node, list):
            for item in node:
                disable_buttons_recursive(item)
    
    # Create a deep copy to avoid modifying original
    card_copy = copy.deepcopy(card)
    disable_buttons_recursive(card_copy)
    
    return card_copy


def create_simple_status_card(
    title: str,
    content: str,
    status: str = "blue",
    schema: str = "2.0"
) -> dict[str, Any]:
    """
    Create a simple status card with title and content
    
    Args:
        title: Card title
        content: Card content (Markdown supported)
        status: Card status color (green/red/yellow/blue/orange/purple/carmine/grey/turquoise/wathet)
        schema: Schema version (default: "2.0")
    
    Returns:
        Card JSON structure
    """
    return {
        "schema": schema,
        "config": {"wide_screen_mode": True},
        "header": {
            "template": status,
            "title": {"tag": "plain_text", "content": title}
        },
        "body": {
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": content}
                }
            ]
        }
    }


def create_error_card(error_msg: str, schema: str = "2.0") -> dict[str, Any]:
    """
    Create error card
    
    Args:
        error_msg: Error message to display
        schema: Schema version (default: "2.0")
    
    Returns:
        Card JSON structure
    """
    return {
        "schema": schema,
        "header": {
            "template": "red",
            "title": {
                "tag": "plain_text",
                "content": "[ERROR] 查询失败"
            }
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": error_msg
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "💡 请检查股票代码是否正确,或联系管理员"
                }
            }
        ]
    }


def create_disabled_card(
    title: str = "[WARN]️ 此卡片已失效",
    message: str = "💡 请使用最新卡片进行操作，避免重复提交。",
    schema: str = "2.0"
) -> dict[str, Any]:
    """
    Create a disabled card template
    
    Args:
        title: Disabled card title
        message: Disabled card message
        schema: Schema version (default: "2.0")
    
    Returns:
        Card JSON structure
    """
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "grey",  # Grey color indicates disabled
            "title": {"tag": "plain_text", "content": title}
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": message
                }
            }
        ]
    }


def create_loading_card(
    title: str = "⏳ 处理中...",
    content: str = "🔄 AI 正在分析，请稍候...",
    schema: str = "2.0"
) -> dict[str, Any]:
    """
    Create a loading card with disabled button
    
    Args:
        title: Loading card title
        content: Loading card content
        schema: Schema version (default: "2.0")
    
    Returns:
        Card JSON structure
    """
    return {
        "schema": schema,
        "header": {
            "template": "blue",
            "title": {
                "tag": "plain_text",
                "content": title
            }
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": content
                }
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "⏳ 请稍候..."},
                "type": "default",
                "size": "medium",
                "disabled": True,  # Disable button
                "value": {}
            }
        ]
    }


def prepare_card_for_send(card: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare card for sending: ensure button names and flat values
    
    Args:
        card: Card JSON structure
    
    Returns:
        Prepared card ready for Feishu API
    """
    card = normalize_card_schema(card)
    card = sanitize_input_elements(card)
    card = ensure_flat_action_values(card)
    card = ensure_button_names(card)
    return card


def sanitize_input_elements(card: dict[str, Any]) -> dict[str, Any]:
    cleaned = copy.deepcopy(card)

    def walk(node: Any, path: str = "") -> None:
        if isinstance(node, dict):
            if node.get("tag") == "input":
                # Remove action_type (not needed in Schema 2.0)
                if "action_type" in node:
                    logger.debug(f"[SANITIZE] Removing action_type from input at {path}")
                    node.pop("action_type", None)
                # Note: input_type is valid and should be kept for number/date inputs
                # Valid values: text (default), number, date
            for key, value in node.items():
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                walk(item, f"{path}[{idx}]")

    walk(cleaned)
    return cleaned


def normalize_card_schema(card: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(card)
    if "schema" not in normalized:
        normalized["schema"] = "2.0"
    if "body" not in normalized:
        elements = normalized.pop("elements", [])
        normalized["body"] = {"elements": elements}
    elif "elements" in normalized and "elements" not in normalized.get("body", {}):
        normalized["body"]["elements"] = normalized.pop("elements")
    return normalized


def build_action_fingerprint(
    chat_id: str,
    user_id: str,
    action_type: str,
    action_value: dict[str, Any],
    form_data: dict[str, Any]
) -> str:
    payload = {
        "chat_id": chat_id or "",
        "user_id": user_id or "",
        "action_type": action_type or "",
        "action_value": action_value if isinstance(action_value, dict) else {},
        "form_data": form_data if isinstance(form_data, dict) else {},
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_duplicate_action(fingerprint: str, window_seconds: float = 3.0) -> bool:
    now = time.time()
    cleanup_before = now - max(10.0, window_seconds * 5)
    with _ACTION_DEDUP_LOCK:
        expired = [key for key, ts in _ACTION_DEDUP_CACHE.items() if ts < cleanup_before]
        for key in expired:
            _ACTION_DEDUP_CACHE.pop(key, None)
        existing = _ACTION_DEDUP_CACHE.get(fingerprint)
        if existing is not None and now - existing < window_seconds:
            return True
        _ACTION_DEDUP_CACHE[fingerprint] = now
    return False


def _init_dedup_db() -> None:
    global _DEDUP_DB_INIT
    if _DEDUP_DB_INIT:
        return
    _DEDUP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DEDUP_DB_PATH, timeout=3)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS action_dedup ("
            "fingerprint TEXT PRIMARY KEY,"
            "created_at REAL NOT NULL,"
            "expire_at REAL NOT NULL)"
        )
        conn.commit()
        _DEDUP_DB_INIT = True
    finally:
        conn.close()


def is_duplicate_action_persistent(fingerprint: str, window_seconds: float = 3.0) -> bool:
    global _DEDUP_DB_CLEANUP_AT
    now = time.time()
    expire_at = now + window_seconds
    try:
        with _ACTION_DEDUP_LOCK:
            _init_dedup_db()
            conn = sqlite3.connect(_DEDUP_DB_PATH, timeout=3)
            try:
                if now - _DEDUP_DB_CLEANUP_AT > max(15.0, window_seconds * 5):
                    conn.execute("DELETE FROM action_dedup WHERE expire_at < ?", (now,))
                    _DEDUP_DB_CLEANUP_AT = now
                row = conn.execute(
                    "SELECT expire_at FROM action_dedup WHERE fingerprint = ?",
                    (fingerprint,)
                ).fetchone()
                if row and float(row[0]) > now:
                    return True
                conn.execute(
                    "INSERT OR REPLACE INTO action_dedup(fingerprint, created_at, expire_at) VALUES (?, ?, ?)",
                    (fingerprint, now, expire_at)
                )
                conn.commit()
                return False
            finally:
                conn.close()
    except Exception as e:
        logger.warning(f"Persistent dedup unavailable, fallback to memory: {e}")
        return is_duplicate_action(fingerprint, window_seconds=window_seconds)


def save_card_to_log(card: dict[str, Any], chat_id: str, log_dir: str = "logs/bot-chat") -> None:
    """
    Save card JSON to log files
    
    Args:
        card: Card dict object
        chat_id: Target chat ID
        log_dir: Log directory path
    """
    try:
        from datetime import datetime
        from pathlib import Path
        
        # 获取日志目录
        backend_dir = Path(__file__).resolve().parent.parent
        log_path = backend_dir / log_dir
        log_path.mkdir(parents=True, exist_ok=True)
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%H%M%S")
        card_json_str = json.dumps(card, ensure_ascii=False)
        
        # 1. 保存完整的卡片 JSON 到独立文件（易读格式）
        card_file = log_path / f"card-{current_date}-{timestamp}.json"
        with open(card_file, 'w', encoding='utf-8') as f:
            json.dump(card, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Card JSON saved to: {card_file}")
        
        # 2. 同时保存到汇总日志（每行一个记录）
        from config.settings import settings
        json_log_file = log_path / f"card-{current_date}.jsonl"
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "chat_id": chat_id,
            "card_file": str(card_file.name),  # 仅保存文件名
            "card_size": len(card_json_str),
            "bot_name": getattr(settings, 'bot_name', 'PegBot'),
            "bot_version": getattr(settings, 'bot_version', '1.0')
        }
        
        with open(json_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        logger.debug(f"Card log entry saved to: {json_log_file}")
        
    except Exception as e:
        logger.error(f"Failed to save card JSON to log: {e}")
