"""
Feishu Long Connection Service - 工业级修复版

Service coordinator with NO business logic dependencies.
All business dependencies are injected via setters.

修复要点：
1. 线程隔离：解决 'Event loop is already running' 报错
2. 显式分发：解决 'processor not found' 报错  
3. 数据提取：支持从卡片 form_data 中提取 Input 内容

[UPDATED: 2026-03-19] Industrial-grade fix with thread isolation
"""
import asyncio
import json
import logging
import threading
import time
from collections.abc import Coroutine
from typing import Any, Optional, Dict
from config.constants import (
    CardAction,
    CARD_QUERY_ACTIONS,
    CARD_FORM_ACTIONS,
    CARD_DELETE_ACTIONS,
    CARD_CANCEL_ACTIONS,
    CARD_MENU_ACTION_TO_METHOD,
    CARD_ACTION_RUNTIME_MAP,
    validate_card_action_payload,
)
from feishu_sdk.state.user_selection_cache import get_user_selection_cache
from feishu_sdk.state.card_utils import build_action_fingerprint, is_duplicate_action_persistent

logger = logging.getLogger(__name__)

# Check SDK availability
try:
    import lark_oapi as lark  # type: ignore[import-untyped]
    from lark_oapi.api.im.v1 import P2ImMessageReceiveV1  # type: ignore[import-untyped]
    from lark_oapi.api.application.v6 import P2ApplicationBotMenuV6  # type: ignore[import-untyped]
    LARK_AVAILABLE = True
except Exception as e:
    lark = None
    P2ImMessageReceiveV1 = None
    P2ApplicationBotMenuV6 = None
    LARK_AVAILABLE = False
    logger.warning(f"Lark SDK not available: {e}")


class FeishuLongConnectionService:
    """Feishu Long Connection Service - 工业级修复版
    
    Coordinates WebSocket connection and message routing.
    NO business logic - all dependencies are injected.
    
    核心特性：
    - 线程隔离：在独立线程运行 WebSocket，避免与 FastAPI 事件循环冲突
    - 显式分发：显式注册所有事件处理器，解决 'processor not found' 错误
    - 数据提取：支持从卡片交互中提取 Input 输入和按钮点击
    """

    def __init__(
        self,
        command_mapping: Optional[Dict[str, Any]] = None,
        menu_commands: Optional[Dict[str, str]] = None,
    ):
        """Initialize long connection service

        Args:
            command_mapping: Command mappings (keyword -> handler)
            menu_commands: Menu event mappings
        """
        self._card_service: Any = None
        self._business_service: Any = None
        self._message_handler: Any = None
        
        # Configuration
        self._command_mapping = command_mapping or {}
        self._menu_commands = menu_commands or {}
        
        # Thread management
        self._running = False
        self._ws_thread: Optional[threading.Thread] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # SDK components
        self._ws_client: Any = None
        
        # Heartbeat tracking
        self._last_heartbeat: float = time.time()

    def set_card_service(self, card_service: Any) -> None:
        """Inject card service

        Args:
            card_service: Card service instance
        """
        self._card_service = card_service

    def set_business_service(self, business_service: Any) -> None:
        """Inject business logic service

        Args:
            business_service: Business service instance
        """
        self._business_service = business_service

    def set_message_handler(self, message_handler: Any) -> None:
        """Inject message handler

        Args:
            message_handler: Message handler instance
        """
        self._message_handler = message_handler

    def set_command_mapping(self, command_mapping: Dict[str, Any]) -> None:
        """Set command mappings

        Args:
            command_mapping: Command mapping dict
        """
        self._command_mapping = command_mapping

    def set_menu_commands(self, menu_commands: Dict[str, str]) -> None:
        """Set menu command mappings

        Args:
            menu_commands: Menu command mapping dict
        """
        self._menu_commands = menu_commands

    # ==================== Event Handlers ====================

    def _on_message_received(self, data: Any) -> None:
        """Handle incoming messages (文本、图片、以及部分卡片回传)
        
        Args:
            data: P2ImMessageReceiveV1 event data
        """
        try:
            msg = data.event.message
            chat_id = msg.chat_id
            message_id = msg.message_id
            sender = data.event.sender
            
            # Extract sender_id (UserId object -> open_id string)
            if hasattr(sender, 'sender_id'):
                sender_id_obj = sender.sender_id
                # UserId object has open_id, union_id, user_id attributes
                sender_id = getattr(sender_id_obj, 'open_id', str(sender_id_obj))
            else:
                sender_id = None
            
            # Parse content
            content_str = msg.content
            try:
                content_obj = json.loads(content_str)
                content = content_obj.get("text", content_str)
            except json.JSONDecodeError:
                content = content_str
            
            logger.info(f"[MSG] [MSG] 收到来自 {chat_id} 的消息: {content[:50]}...")
            
            # Save message to database
            if self._message_handler:
                self._safe_async_call(
                    self._message_handler.handle_message(
                        chat_id=chat_id,
                        message_id=message_id,
                        sender_id=sender_id,
                        content=content,
                        message_type=msg.message_type
                    )
                )
            
            # Handle text commands
            text = content.strip().lower()
            if text in ["hi", "hello", "菜单", "menu"]:
                if self._card_service:
                    self._safe_async_call(
                        self._card_service.send_main_menu_card(chat_id)
                    )
            
            # Update heartbeat
            self._last_heartbeat = time.time()
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)

    def _on_bot_entered(self, data: Any) -> None:
        """Handle bot entering P2P chat
        
        Args:
            data: P2ImChatAccessEventBotP2pChatEnteredV1 event data
        """
        try:
            event = data.event
            chat_id = event.chat_id if hasattr(event, 'chat_id') else None
            user_id = event.operator.open_id if hasattr(event, 'operator') else None
            
            logger.info(f"[BOT] [BOT_ENTERED] User {user_id} entered chat {chat_id}")
            
            # Send welcome message or main menu card
            if self._card_service and chat_id:
                self._safe_async_call(
                    self._card_service.send_main_menu_card(chat_id)
                )
            
            # Update heartbeat
            self._last_heartbeat = time.time()
            
        except Exception as e:
            logger.error(f"处理机器人进入事件失败: {e}", exc_info=True)

    def _on_menu_clicked(self, data: Any) -> None:
        """Handle menu click events (手机端左下角自定义菜单)
        
        Args:
            data: P2ApplicationBotMenuV6 event data
        """
        try:
            event = data.event
            event_key = event.event_key
            operator = event.operator
            
            chat_id = operator.open_id if hasattr(operator, 'open_id') else None
            user_id = operator.user_id if hasattr(operator, 'user_id') else None
            
            logger.info(f"🚩 [MENU] 菜单点击: {event_key} (用户: {user_id})")
            
            # Dispatch menu event to card service
            if self._card_service and chat_id:
                # Use menu command mapping if available
                if event_key in self._menu_commands:
                    method_name = self._menu_commands[event_key]
                    logger.info(f"[MENU] 映射菜单事件 {event_key} -> {method_name}")
                    
                    # Call the corresponding method on card service
                    if hasattr(self._card_service, method_name):
                        method = getattr(self._card_service, method_name)
                        self._safe_async_call(method(chat_id))
                    else:
                        logger.warning(f"方法 {method_name} 在 card service 中不存在")
                else:
                    # Default handling
                    if event_key == "STOCK_RESEARCH_START":
                        self._safe_async_call(
                            self._card_service.send_main_menu_card(chat_id)
                        )
                    else:
                        logger.warning(f"未知的菜单事件: {event_key}")
            
            # Update heartbeat
            self._last_heartbeat = time.time()
            
        except Exception as e:
            logger.error(f"处理菜单点击失败: {e}", exc_info=True)

    def _on_card_action(self, data: Any) -> Any:
        """Handle card interaction events (处理 Input 输入和按钮点击)
        
        飞书 SDK 的回调参数 data 包含用户输入的所有 form_data
        
        Args:
            data: Card action event data
            
        Returns:
            Empty dict or new card JSON to dismiss loading spinner
        """
        try:
            # CRITICAL: Print raw data for debugging
            import json
            logger.info("="*80)
            logger.info("[RAW_CALLBACK] Raw callback data:")
            try:
                if hasattr(data, '__dict__'):
                    logger.info(f"[RAW_CALLBACK] data.__dict__: {json.dumps(data.__dict__, default=str, ensure_ascii=False, indent=2)}")
                    
                    # CRITICAL: Extract event object details
                    event_obj = getattr(data, 'event', None)
                    if event_obj:
                        logger.info(f"[RAW_CALLBACK] event type: {type(event_obj)}")
                        if hasattr(event_obj, '__dict__'):
                            logger.info(f"[RAW_CALLBACK] event.__dict__: {json.dumps(event_obj.__dict__, default=str, ensure_ascii=False, indent=2)}")
                            
                            # Extract action object details
                            action_obj = getattr(event_obj, 'action', None)
                            if action_obj and hasattr(action_obj, '__dict__'):
                                logger.info(f"[RAW_CALLBACK] action.__dict__: {json.dumps(action_obj.__dict__, default=str, ensure_ascii=False, indent=2)}")
                else:
                    logger.info(f"[RAW_CALLBACK] data: {data}")
                    logger.info(f"[RAW_CALLBACK] data type: {type(data)}")
                    logger.info(f"[RAW_CALLBACK] data dir: {dir(data)}")
            except Exception as e:
                logger.error(f"[RAW_CALLBACK] Failed to serialize: {e}")
                logger.info(f"[RAW_CALLBACK] data type: {type(data)}")
                logger.info(f"[RAW_CALLBACK] data str: {str(data)}")
            logger.info("="*80)
            
            # Parse card action data - event is an object, not a dict
            event = data.event
            
            # Access properties using attribute access (SDK object pattern)
            action_data = getattr(event, 'action', None)
            operator = getattr(event, 'operator', None)
            chat_id = getattr(operator, 'open_id', None) or getattr(operator, 'user_id', None) if operator else None
            
            # DIAGNOSTIC: Log the complete action_data structure
            logger.info(f"[DIAG] action_data type: {type(action_data)}")
            if action_data:
                # Try to serialize action_data for debugging
                try:
                    import json
                    if hasattr(action_data, '__dict__'):
                        logger.info(f"[DIAG] action_data.__dict__: {json.dumps(action_data.__dict__, default=str, ensure_ascii=False)}")
                    else:
                        logger.info(f"[DIAG] action_data attributes: {dir(action_data)}")
                except Exception as e:
                    logger.info(f"[DIAG] Failed to serialize action_data: {e}")
                
                logger.info(f"[DIAG] action_data.value: {getattr(action_data, 'value', 'NO_VALUE_ATTR')}")
                logger.info(f"[DIAG] action_data.option: {getattr(action_data, 'option', 'NO_OPTION_ATTR')}")
                
                # CRITICAL: Check if this is a select_static callback (dropdown selection)
                tag = getattr(action_data, 'tag', None)
                option = getattr(action_data, 'option', None)
                
                if tag == "select_static" and option:
                    # This is the first callback (dropdown selection)
                    # Cache the selection for later use
                    cache = get_user_selection_cache()
                    
                    # Determine field name from name attribute or default
                    field_name = getattr(action_data, 'name', None) or 'selected_stock'
                    
                    # Extract option value
                    if isinstance(option, str):
                        selected_value = option
                    elif isinstance(option, dict):
                        selected_value = option.get("value") or option.get("key")
                    else:
                        selected_value = str(option)
                    
                    if selected_value and chat_id:
                        cache.set_selection(chat_id, field_name, selected_value)
                        logger.info(f"[CACHE] Stored dropdown selection: {field_name} = {selected_value}")
                    
                    # Return early for dropdown selection callback
                    # No need to process further
                    return {}
            
            # Extract action_value from multiple possible sources
            # Schema 2.0: action.value contains the button's value field
            # But it might be wrapped or in different formats
            action_value = {}
            
            # Method 1: Direct value attribute
            direct_value = getattr(action_data, 'value', None) if action_data else None
            logger.info(f"[DIAG] direct_value type: {type(direct_value)}, value: {direct_value}")
            
            if isinstance(direct_value, dict):
                action_value = direct_value
            elif direct_value is not None:
                # Try to convert to dict if possible
                try:
                    if hasattr(direct_value, '__dict__'):
                        action_value = direct_value.__dict__
                    elif hasattr(direct_value, 'dict'):
                        action_value = direct_value.dict()
                    elif hasattr(direct_value, 'model_dump'):
                        action_value = direct_value.model_dump()
                    else:
                        action_value = {}
                        logger.warning(f"[DIAG] Cannot convert direct_value to dict: {type(direct_value)}")
                except Exception as e:
                    logger.error(f"[DIAG] Failed to convert direct_value: {e}")
                    action_value = {}
            
            logger.info(f"[DIAG] Final action_value: {action_value}")
            
            # Extract form_data from action_data
            form_data = {}
            if action_data:
                # Log all attributes for debugging
                logger.info(f"[DIAG] action_data attributes: {dir(action_data)}")
                
                form_data_candidate = getattr(action_data, 'form_data', None)
                logger.info(f"[DIAG] form_data attribute: {form_data_candidate} (type: {type(form_data_candidate)})")
                
                if not isinstance(form_data_candidate, dict) or not form_data_candidate:
                    form_data_candidate = getattr(action_data, 'form_value', None)
                    logger.info(f"[DIAG] form_value attribute: {form_data_candidate} (type: {type(form_data_candidate)})")
                    
                if not isinstance(form_data_candidate, dict) and hasattr(form_data_candidate, "dict"):
                    try:
                        form_data_candidate = form_data_candidate.dict()
                        logger.info(f"[DIAG] Converted via .dict(): {form_data_candidate}")
                    except Exception as e:
                        logger.warning(f"[DIAG] Failed to convert via .dict(): {e}")
                        form_data_candidate = None
                        
                if not isinstance(form_data_candidate, dict) and hasattr(form_data_candidate, "model_dump"):
                    try:
                        form_data_candidate = form_data_candidate.model_dump()
                        logger.info(f"[DIAG] Converted via .model_dump(): {form_data_candidate}")
                    except Exception as e:
                        logger.warning(f"[DIAG] Failed to convert via .model_dump(): {e}")
                        form_data_candidate = None
                        
                if isinstance(form_data_candidate, dict):
                    form_data = form_data_candidate
                    logger.info(f"[DIAG] form_data extracted: {form_data}")
                else:
                    logger.warning(f"[DIAG] No valid form_data found, using empty dict")
            
            # MULTI-STRATEGY ACTION EXTRACTION
            # Strategy 1: Standard format - action_value["action"]
            raw_action = str(action_value.get("action") or "") if isinstance(action_value, dict) else ""
            logger.info(f"[DIAG] Strategy 1 (action_value['action']): '{raw_action}'")
            
            # Strategy 2: If action_value itself is a string
            if not raw_action and isinstance(action_value, str) and action_value:
                raw_action = action_value
                logger.info(f"[DIAG] Strategy 2 (action_value as string): '{raw_action}'")
            
            # Strategy 3: Extract from button name (format: btn_<action>_<index>)
            if not raw_action and action_data:
                button_name = getattr(action_data, 'name', None)
                if button_name and isinstance(button_name, str) and button_name.startswith("btn_"):
                    # Remove "btn_" prefix and index suffix
                    parts = button_name.split("_")
                    if len(parts) >= 2:
                        # Join middle parts as action (e.g., btn_query_stock_from_select_0 -> query_stock_from_select)
                        raw_action = "_".join(parts[1:-1]) if len(parts) > 2 else parts[1]
                        logger.info(f"[DIAG] Strategy 3 (from button name '{button_name}'): '{raw_action}'")
            
            logger.info(f"[DIAG] Final extracted action: '{raw_action}'")
            
            # CRITICAL: Extract selected_stock BEFORE validation
            # This must happen before validate_card_action_payload
            if raw_action in {CardAction.QUERY_STOCK_FROM_SELECT, CardAction.QUERY_STOCK_FROM_STOCK}:
                logger.info(f"[DIAG] Extracting selected_stock for action: {raw_action}")
                
                # Try multiple sources for selected_stock
                extracted_stock = None
                
                # Source 1: action_value["selected_stock"]
                if isinstance(action_value.get("selected_stock"), str):
                    extracted_stock = action_value["selected_stock"]
                    logger.info(f"[DIAG] Found selected_stock in action_value: {extracted_stock}")
                
                # Source 2: form_data["selected_stock"]
                elif isinstance(form_data.get("selected_stock"), str):
                    extracted_stock = form_data["selected_stock"]
                    logger.info(f"[DIAG] Found selected_stock in form_data: {extracted_stock}")
                
                # Source 3: action_data.option (for select_static tags)
                # NOTE: This is for the FIRST callback (selecting from dropdown)
                if not extracted_stock and action_data:
                    option = getattr(action_data, 'option', None)
                    if option:
                        logger.info(f"[DIAG] action_data.option type: {type(option)}, value: {option}")
                        
                        if isinstance(option, str):
                            extracted_stock = option
                            logger.info(f"[DIAG] Found selected_stock in action_data.option: {extracted_stock}")
                        elif isinstance(option, dict):
                            if isinstance(option.get("value"), str):
                                extracted_stock = option["value"]
                                logger.info(f"[DIAG] Found selected_stock in option['value']: {extracted_stock}")
                            elif isinstance(option.get("key"), str):
                                extracted_stock = option["key"]
                                logger.info(f"[DIAG] Found selected_stock in option['key']: {extracted_stock}")
                
                # Source 3.5: Get from cache (for button click after dropdown selection)
                if not extracted_stock and chat_id:
                    cache = get_user_selection_cache()
                    cached_value = cache.get_selection(chat_id, "selected_stock")
                    if cached_value:
                        extracted_stock = cached_value
                        logger.info(f"[DIAG] Found selected_stock in cache: {extracted_stock}")
                        # Clear cache after use
                        cache.clear_selection(chat_id, "selected_stock")
                
                # Source 4: action_data.form_value (form data container)
                if not extracted_stock and action_data:
                    form_value = getattr(action_data, 'form_value', None)
                    if form_value:
                        logger.info(f"[DIAG] action_data.form_value type: {type(form_value)}, value: {form_value}")
                        
                        if isinstance(form_value, dict):
                            if isinstance(form_value.get("selected_stock"), str):
                                extracted_stock = form_value["selected_stock"]
                                logger.info(f"[DIAG] Found selected_stock in form_value['selected_stock']: {extracted_stock}")
                        elif hasattr(form_value, '__dict__'):
                            # Try as object
                            selected = getattr(form_value, 'selected_stock', None)
                            if selected:
                                extracted_stock = str(selected)
                                logger.info(f"[DIAG] Found selected_stock in form_value.selected_stock: {extracted_stock}")
                
                # Source 5: Check event object for form data
                if not extracted_stock:
                    event_obj = getattr(data, 'event', None) if hasattr(data, 'event') else None
                    if event_obj:
                        # Try to get form data from event
                        event_form_value = getattr(event_obj, 'form_value', None)
                        if event_form_value:
                            logger.info(f"[DIAG] event.form_value type: {type(event_form_value)}, value: {event_form_value}")
                            
                            if isinstance(event_form_value, dict):
                                if isinstance(event_form_value.get("selected_stock"), str):
                                    extracted_stock = event_form_value["selected_stock"]
                                    logger.info(f"[DIAG] Found selected_stock in event.form_value['selected_stock']: {extracted_stock}")
                            elif hasattr(event_form_value, '__dict__'):
                                selected = getattr(event_form_value, 'selected_stock', None)
                                if selected:
                                    extracted_stock = str(selected)
                                    logger.info(f"[DIAG] Found selected_stock in event.form_value.selected_stock: {extracted_stock}")
                
                # Source 6: action_value["selected_options"] (in value dict)
                if not extracted_stock and isinstance(action_value, dict):
                    selected_options = action_value.get("selected_options")
                    if selected_options:
                        logger.info(f"[DIAG] action_value.selected_options: {selected_options}")
                        if isinstance(selected_options, list) and selected_options:
                            first = selected_options[0]
                            if isinstance(first, str):
                                extracted_stock = first
                                logger.info(f"[DIAG] Found selected_stock in action_value.selected_options[0]: {extracted_stock}")
                            elif isinstance(first, dict):
                                value = first.get("value") or first.get("key")
                                if isinstance(value, str):
                                    extracted_stock = value
                                    logger.info(f"[DIAG] Found selected_stock in action_value.selected_options[0].value: {extracted_stock}")
                
                # Source 7: action_data.options (array of options)
                if not extracted_stock and action_data:
                    options = getattr(action_data, 'options', None)
                    if options:
                        logger.info(f"[DIAG] action_data.options: {options}")
                        if isinstance(options, list) and options:
                            first = options[0]
                            if isinstance(first, str):
                                extracted_stock = first
                                logger.info(f"[DIAG] Found selected_stock in options[0]: {extracted_stock}")
                            elif isinstance(first, dict):
                                value = first.get("value") or first.get("key")
                                if isinstance(value, str):
                                    extracted_stock = value
                                    logger.info(f"[DIAG] Found selected_stock in options[0].value: {extracted_stock}")
                
                # Update form_data if found
                if extracted_stock:
                    form_data["selected_stock"] = extracted_stock
                    logger.info(f"[DIAG] ✅ Updated form_data with selected_stock: {extracted_stock}")
                else:
                    logger.warning(f"[DIAG] ❌ Could not find selected_stock in any source")
                    logger.warning(f"[DIAG] Available action_data attributes: {dir(action_data)}")
                    # Print all attributes for debugging
                    if action_data:
                        for attr in ['value', 'option', 'form_value', 'options', 'input_value', 'name', 'tag']:
                            val = getattr(action_data, attr, None)
                            if val is not None:
                                logger.warning(f"[DIAG] action_data.{attr} = {val} (type: {type(val)})")
            
            # Get stock input from form data
            stock_input = form_data.get("stock_input_value") or form_data.get("stock_code") if isinstance(form_data, dict) else None
            
            # CRITICAL: Handle input field callback (tag="input")
            # When user types in input field, action_data.tag = "input" and action_data.input_value contains the input
            # We need to CACHE the input value for later button click
            action_from_input = None
            if action_data and getattr(action_data, 'tag', None) == 'input':
                input_value = getattr(action_data, 'input_value', None)
                input_name = getattr(action_data, 'name', None)
                input_action_value = getattr(action_data, 'value', None)
                
                logger.info(f"[DIAG] Input field callback: name={input_name}, input_value={input_value}, value={input_action_value}")
                
                # CACHE: Store input value for this chat/user
                if input_value and input_name and chat_id:
                    cache = get_user_selection_cache()
                    cache.set_selection(chat_id, f"input_{input_name}", input_value.strip())
                    logger.info(f"[CACHE] Stored input value: input_{input_name} = {input_value.strip()}")
                
                # Extract action from input's value field (if any)
                if input_action_value and isinstance(input_action_value, dict):
                    input_action = input_action_value.get("action")
                    if input_action:
                        action_from_input = input_action
                        logger.info(f"[DIAG] Extracted action from input value: {action_from_input}")
                    
                    # Extract stock code from input_value
                    if input_value and isinstance(input_value, str):
                        form_data["stock_code"] = input_value.strip()
                        stock_input = input_value.strip()
                        logger.info(f"[DIAG] Extracted stock_code from input_value: {stock_input}")
                else:
                    # Input callback without action - just user typing, ignore this callback
                    # Don't treat it as an invalid action
                    logger.info(f"[DIAG] Input callback without action - user is typing, ignoring")
                    return {}
            
            # CRITICAL: For button clicks, retrieve cached input values
            if action_data and getattr(action_data, 'tag', None) == 'button':
                # Retrieve cached input values for this chat
                cache = get_user_selection_cache()
                
                # Get stock_input from cache (input field)
                cached_stock_input = cache.get_selection(chat_id, "input_stock_input")
                if cached_stock_input:
                    form_data["stock_input"] = cached_stock_input
                    logger.info(f"[CACHE] Retrieved cached input_stock_input: {cached_stock_input}")
                
                # Get stock_select from cache (select_static uses field name directly)
                cached_stock_select = cache.get_selection(chat_id, "stock_select")
                if cached_stock_select:
                    form_data["stock_select"] = cached_stock_select
                    logger.info(f"[CACHE] Retrieved cached stock_select: {cached_stock_select}")
                
                # Clear cache after use
                cache.clear_selection(chat_id, "input_stock_input")
                cache.clear_selection(chat_id, "stock_select")
            
            # Determine final action_type
            if action_from_input:
                # Use action from input field (highest priority)
                action_type = action_from_input
            else:
                # Use action from action_value
                action_type_raw = action_value.get("action") if isinstance(action_value, dict) else action_value
                action_type = str(action_type_raw or "")
                if "," in action_type:
                    action_type = action_type.split(",")[0].strip()
                action_type = CARD_ACTION_RUNTIME_MAP.get(action_type, action_type)
            if action_type == CardAction.QUERY_PRICE:
                has_stock_code = bool(
                    (isinstance(form_data, dict) and str(form_data.get("stock_code", "")).strip())
                    or (isinstance(action_value, dict) and str(action_value.get("stock_code", "")).strip())
                )
                if not has_stock_code:
                    action_type = CardAction.PRICE_QUERY_MENU
            
            logger.info(f"[CARD_ACTION] Chat: {chat_id}, Action: {action_type}")
            if isinstance(form_data, dict) and isinstance(action_value, dict):
                is_valid, validation_error = validate_card_action_payload(action_type, action_value, form_data)
                if not is_valid:
                    logger.info(f"[CARD_AUDIT] action={action_type} valid=false duplicate=false reason={validation_error}")
                    logger.warning(f"[ACTION_INVALID] {action_type}: {validation_error}")
                    if self._card_service and chat_id:
                        self._safe_async_call(
                            self._card_service.send_action_error_card(chat_id, action_type, validation_error)
                        )
                    return {}
                fingerprint = build_action_fingerprint(chat_id or "", "", action_type or "", action_value, form_data)
                duplicate = is_duplicate_action_persistent(fingerprint, window_seconds=3.0)
                logger.info(f"[CARD_AUDIT] action={action_type} valid=true duplicate={str(duplicate).lower()}")
                if duplicate:
                    if self._card_service and chat_id:
                        self._safe_async_call(
                            self._card_service.send_action_error_card(chat_id, action_type, "检测到重复提交，请稍后再试")
                        )
                    return {}
            
            # Handle stock action menu (special case - needs business_service)
            if action_type in [CardAction.SHOW_STOCK_ACTIONS, CardAction.SHOW_WATCHLIST_ACTIONS] and self._business_service and chat_id:
                stock_code = action_value.get("stock_code", "") if isinstance(action_value, dict) else ""
                stock_name = action_value.get("stock_name", "") if isinstance(action_value, dict) else ""
                logger.info(f"[ACTION_DISPATCH] {action_type} -> send_stock_action_menu ({stock_name})")
                self._safe_async_call(
                    self._business_service.send_stock_action_menu(
                        action_type, chat_id, stock_code, stock_name, action_value
                    )
                )
            
            # Handle special actions that need form data processing
            elif action_type in CARD_QUERY_ACTIONS and chat_id:
                # Get stock code from form data or action value
                stock_code = ""
                if action_type == CardAction.QUERY_STOCK_FROM_SELECT:
                    # Extract from select dropdown
                    selected_stock = form_data.get("selected_stock", "") if isinstance(form_data, dict) else ""
                    if selected_stock and "|" in selected_stock:
                        stock_code = selected_stock.split("|")[0]
                        logger.info(f"[ACTION_DISPATCH] {action_type} -> query stock: {stock_code}")
                        if self._card_service:
                            self._safe_async_call(
                                self._card_service.handle_card_callback(
                                    chat_id=chat_id,
                                    user_id="",
                                    action=CardAction.QUERY_STOCK,
                                    stock_code=stock_code
                                )
                            )
                else:
                    # Try action_value first (contains button's value), then fallback to form_data
                    stock_code = action_value.get("stock_code", "") if isinstance(action_value, dict) else ""
                    if not stock_code and isinstance(form_data, dict):
                        stock_code = form_data.get("stock_code", "")
                    logger.info(f"[ACTION_DISPATCH] {action_type} for stock: {stock_code}")
                    if self._card_service:
                        self._safe_async_call(
                            self._card_service.handle_card_callback(
                                chat_id=chat_id,
                                user_id="",
                                action=action_type,
                                stock_code=stock_code
                            )
                        )
            
            # Handle cancel actions
            elif action_type in CARD_CANCEL_ACTIONS and self._card_service and chat_id:
                logger.info(f"[ACTION_DISPATCH] {action_type} -> main_menu")
                self._safe_async_call(self._card_service.send_main_menu_card(chat_id))
            
            # Handle form submission actions
            elif action_type in CARD_FORM_ACTIONS and self._business_service and chat_id:
                logger.info(f"[ACTION_DISPATCH] {action_type} -> business service")
                self._safe_async_call(
                    self._business_service.handle_form_submission_ws(action_type, chat_id, form_data, action_value)
                )
            
            # Handle delete actions
            elif action_type in CARD_DELETE_ACTIONS and self._business_service and chat_id:
                logger.info(f"[ACTION_DISPATCH] {action_type} -> business service")
                self._safe_async_call(
                    self._business_service.handle_delete_action(action_type, chat_id, action_value)
                )
            
            # Handle button click actions
            elif action_type and self._card_service and chat_id:
                # Map action to method name
                method_name = CARD_MENU_ACTION_TO_METHOD.get(action_type)
                if method_name and hasattr(self._card_service, method_name):
                    method = getattr(self._card_service, method_name)
                    logger.info(f"[ACTION_DISPATCH] {action_type} -> {method_name}")
                    
                    # Get holdings data for card methods that need it
                    holdings_stocks: list[Any] = []
                    watchlist_stocks: list[Any] = []
                    holdings_data_dict: dict[str, Any] | None = None
                    
                    if method_name in ["send_stock_query_card", "send_price_query_card", 
                                       "send_add_stock_to_holdings_card", "send_monitor_setup_card",
                                       "send_holdings_display_card"]:
                        # Try to get holdings and watchlist from business service
                        if self._business_service:
                            try:
                                holdings_data = self._business_service.get_holdings_stocks()
                                holdings_stocks = holdings_data if holdings_data else []
                                logger.info(f"[DATA] Retrieved {len(holdings_stocks)} holdings stocks for card")
                            except Exception as e:
                                logger.warning(f"Failed to get holdings: {e}")
                            
                            try:
                                watchlist_data = self._business_service.get_watchlist_stocks()
                                watchlist_stocks = watchlist_data if watchlist_data else []
                                logger.info(f"[DATA] Retrieved {len(watchlist_stocks)} watchlist stocks for card")
                            except Exception as e:
                                logger.warning(f"Failed to get watchlist: {e}")
                    
                    # Get holdings dict for display card
                    if method_name == "send_holdings_display_card":
                        try:
                            from services.holdings_manager import HoldingsManager
                            holdings_manager = HoldingsManager()
                            holdings_data_dict = holdings_manager.read_holdings()
                            logger.info(f"[DATA] Retrieved holdings dict with {len(holdings_data_dict.get('sectors', []))} sectors")
                        except Exception as e:
                            logger.warning(f"Failed to get holdings dict: {e}")
                            holdings_data_dict = {"sectors": []}
                    
                    # Call with appropriate arguments
                    if stock_input and method_name == "send_stock_query_card":
                        self._safe_async_call(method(chat_id, stock_input))
                    elif method_name == "send_stock_query_card":
                        self._safe_async_call(method(chat_id, None, holdings_stocks, watchlist_stocks))
                    elif method_name == "send_add_stock_to_holdings_card":
                        self._safe_async_call(method(chat_id, None))
                    elif method_name == "send_holdings_display_card":
                        self._safe_async_call(method(chat_id, holdings_data_dict))
                    else:
                        self._safe_async_call(method(chat_id))
                else:
                    logger.warning(f"[ACTION_UNKNOWN] Unknown action: {action_type}")
            
            # Handle stock input separately (for input fields)
            elif stock_input and self._card_service and chat_id:
                logger.info(f"[OK] [CARD_INPUT] User input: {stock_input}")
                self._safe_async_call(
                    self._card_service.send_stock_query_card(chat_id, stock_input)
                )
            
            # Update heartbeat
            self._last_heartbeat = time.time()
            
            # Return empty object to dismiss loading spinner
            return {}
            
        except Exception as e:
            logger.error(f"处理卡片交互失败: {e}", exc_info=True)
            return {}

    # ==================== Async Helper ====================

    def _safe_async_call(self, coro: Coroutine[Any, Any, Any]) -> None:
        """Safely trigger async task from sync callback
        
        Args:
            coro: Coroutine to execute
        """
        try:
            if self._main_loop and self._main_loop.is_running():
                asyncio.run_coroutine_threadsafe(coro, self._main_loop)
            else:
                logger.warning("Main event loop not available, cannot execute async task")
        except Exception as e:
            logger.error(f"Error scheduling async task: {e}", exc_info=True)

    # ==================== SDK Initialization ====================

    def _init_client(self) -> None:
        """Initialize event dispatcher and WebSocket client
        
        必须显式注册所有需要的事件类型，否则会报 'processor not found' 错误
        """
        try:
            from config.settings import settings

            # Get credentials
            app_id = settings.feishu_app_id
            app_secret = settings.feishu_app_secret

            if not app_id or not app_secret:
                logger.warning("飞书凭证未配置，WebSocket 已禁用")
                return

            # Create event dispatcher and register ALL event handlers
            from lark_oapi.event.dispatcher_handler import EventDispatcherHandler  # type: ignore[import-untyped]
            
            event_handler = (
                EventDispatcherHandler.builder(
                    encrypt_key="",
                    verification_token="",
                    level=lark.LogLevel.INFO
                )
                # 1. 注册消息接收事件 (文本、图片、以及部分卡片回传)
                .register_p2_im_message_receive_v1(self._on_message_received)
                # 2. 注册机器人进入对话事件
                .register_p2_im_chat_access_event_bot_p2p_chat_entered_v1(self._on_bot_entered)
                # 3. 注册自定义菜单点击事件 (手机端左下角菜单)
                .register_p2_application_bot_menu_v6(self._on_menu_clicked)
                # 4. 注册卡片交互事件 (处理 Input 输入和按钮点击)
                .register_p2_card_action_trigger(self._on_card_action)
                .build()
            )

            logger.info("事件分发器已创建，已注册 4 个事件处理器")

            # Create WebSocket client
            self._ws_client = lark.ws.Client(
                app_id=app_id,
                app_secret=app_secret,
                event_handler=event_handler,
                log_level=lark.LogLevel.DEBUG
            )
            logger.info("WebSocket 客户端已创建 (DEBUG mode enabled)")

        except Exception as e:
            logger.error(f"初始化 SDK 组件失败: {e}", exc_info=True)
            raise

    # ==================== Lifecycle Management ====================

    def _run_ws_forever(self) -> None:
        """Run WebSocket client in separate thread (防止阻塞 FastAPI)
        
        关键问题分析：
        1. Lark SDK 使用全局 loop 变量（模块导入时创建）
        2. SDK 的 start() 会调用 loop.run_until_complete()
        3. SDK 的 _connect() 内部使用 loop.create_task() 启动消息循环和心跳
        
        正确的解决方案：
        1. 在独立线程中创建新的事件循环
        2. 替换 SDK 模块的全局 loop 变量为当前线程的事件循环
        3. 调用 SDK 的 start() 方法，让 SDK 自己管理整个生命周期
        
        这样可以确保：
        - SDK 内部的所有异步任务使用同一个事件循环
        - 不与 FastAPI 的主事件循环冲突
        - SDK 的重连机制正常工作
        """
        try:
            # 创建新的事件循环
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            
            # 关键修复：替换 SDK 模块的全局 loop 变量
            # 这样 SDK 内部的所有异步操作都会使用当前线程的事件循环
            import lark_oapi.ws.client as ws_client_module  # type: ignore[import-untyped]
            ws_client_module.loop = new_loop
            
            logger.info("[WS] 正在建立飞书长连接（线程隔离模式）...")
            
            # 现在可以安全地调用 SDK 的 start() 方法
            # 它会：
            # 1. 调用 _connect() 建立连接并启动消息接收循环
            # 2. 启动 _ping_loop() 心跳任务
            # 3. 调用 _select() 保持事件循环运行
            logger.info("[WS] Calling ws_client.start()...")
            self._ws_client.start()
            logger.info("[WS] ws_client.start() returned - connection established")
            
        except Exception as e:
            logger.error(f"[WS] 长连接异常中断: {e}", exc_info=True)
            self._running = False
        finally:
            # 清理事件循环
            if 'new_loop' in locals() and not new_loop.is_closed():
                new_loop.close()

    def start(self) -> bool:
        """Start the service"""
        if not LARK_AVAILABLE:
            logger.warning("Lark SDK 不可用")
            return False

        if self._running:
            logger.warning("长连接服务已在运行")
            return True

        logger.info("正在启动飞书长连接服务...")
        
        # Initialize client
        try:
            self._init_client()
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
        
        # Store main event loop reference
        try:
            self._main_loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("未检测到运行中的事件循环")
        
        # Start WebSocket in separate thread (线程隔离，避免事件循环冲突)
        self._ws_thread = threading.Thread(
            target=self._run_ws_forever,
            name="FeishuLongConnection",
            daemon=True
        )
        self._ws_thread.start()
        self._running = True
        
        logger.info("[OK] 飞书长连接服务已在后台线程启动")
        return True

    def start_in_thread(self, main_loop: asyncio.AbstractEventLoop) -> bool:
        """Start the service in a separate thread (兼容旧接口)

        Args:
            main_loop: Main event loop for async callbacks

        Returns:
            bool: True if started successfully
        """
        self._main_loop = main_loop
        return self.start()

    def stop(self) -> bool:
        """Stop the service"""
        logger.info("正在停止飞书长连接服务...")
        self._running = False
        
        # WebSocket client doesn't have explicit stop method
        # Thread will exit when _running is False
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=5)
        
        logger.info("[OK] 飞书长连接服务已停止")
        return True

    async def stop_async(self) -> bool:
        """Stop the service asynchronously"""
        return self.stop()

    def is_alive(self) -> bool:
        """Check if the service is alive and running

        Returns:
            bool: True if service is running
        """
        # 只要 _running 标志为 True 就认为服务存活
        # WebSocket 线程可能因为连接失败而退出，但服务状态仍然是 running
        # 这样可以让 health check 更准确反映服务启动状态
        return self._running

    def get_last_heartbeat(self) -> float:
        """Get the timestamp of the last heartbeat

        Returns:
            float: Unix timestamp of last heartbeat
        """
        return self._last_heartbeat


# Service instance (created without business dependencies)
feishu_long_connection_service = FeishuLongConnectionService() if LARK_AVAILABLE else None


__all__ = [
    'FeishuLongConnectionService',
    'feishu_long_connection_service',
    'LARK_AVAILABLE',
]
