"""
Application Layer Card Service - 应用层卡片服务

Provides business-friendly interfaces for sending cards.
Wraps SDK layer FeishuCardService and uses card builders to generate content.
"""

import logging
from typing import Any, Optional
from datetime import datetime
import uuid

from feishu_sdk.core.card_service import FeishuCardService
from services.feishu_bot.cards import (
    MenuCardBuilder,
    StockCardBuilder,
    HoldingsCardBuilder,
    WatchlistCardBuilder,
    PriceAlertCardBuilder,
    ActionCardsBuilder,
)
from database.session import async_session_maker
from database.models import FeishuChatMessage

logger = logging.getLogger(__name__)


class CardService:
    """
    Application layer card service.
    
    Provides simplified business interfaces by:
    1. Using card builders to generate card content
    2. Calling SDK layer FeishuCardService to send cards
    3. Adding business logging
    """
    
    def __init__(self) -> None:
        """Initialize card service with card builders"""
        self._sdk_card_service: Optional[FeishuCardService] = None
        
        # Initialize card builders
        self._menu_builder = MenuCardBuilder()
        self._stock_builder = StockCardBuilder()
        self._holdings_builder = HoldingsCardBuilder()
        self._watchlist_builder = WatchlistCardBuilder()
        self._price_alert_builder = PriceAlertCardBuilder()
        self._action_builder = ActionCardsBuilder()
    
    def set_sdk_card_service(self, sdk_service: FeishuCardService) -> None:
        """
        Inject SDK layer card service.
        
        Args:
            sdk_service: FeishuCardService instance from SDK layer
        """
        self._sdk_card_service = sdk_service
        logger.info("SDK card service injected into CardService")
    
    # ==================== Menu Cards ====================
    
    async def send_main_menu_card(self, chat_id: str) -> bool:
        """
        Send main menu card.
        
        Args:
            chat_id: Target chat ID
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending main menu card to chat: {chat_id}")
        
        card = self._menu_builder.build(card_type="main_menu")
        
        result = await self._send_card(chat_id, card)
        
        if result:
            logger.info(f"Main menu card sent successfully to {chat_id}")
        else:
            logger.error(f"Failed to send main menu card to {chat_id}")
        
        return result
    
    async def send_monitor_setup_card(self, chat_id: str) -> bool:
        """
        Send monitor setup card.
        
        Args:
            chat_id: Target chat ID
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending monitor setup card to chat: {chat_id}")
        
        card = self._price_alert_builder.build(card_type="monitor_setup")
        
        return await self._send_card(chat_id, card)

    async def send_monitor_config_card(self, chat_id: str) -> bool:
        logger.info(f"Sending monitor config card to chat: {chat_id}")
        card = self._price_alert_builder.build(card_type="monitor_config")
        return await self._send_card(chat_id, card)
    
    # ==================== Stock Cards ====================
    
    async def send_stock_query_card(
        self, 
        chat_id: str,
        stock_code: str | None = None,
        holdings_stocks: list[dict[str, Any]] | None = None,
        watchlist_stocks: list[dict[str, Any]] | None = None
    ) -> bool:
        """
        Send stock query card with stock selection dropdown.
        
        Args:
            chat_id: Target chat ID
            stock_code: Optional stock code for direct query (bypass dropdown)
            holdings_stocks: List of holdings stocks for dropdown
            watchlist_stocks: List of watchlist stocks for dropdown
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending stock query card to chat: {chat_id}")
        
        # If stock_code is provided, create a pre-filled card for direct query
        if stock_code:
            logger.info(f"Pre-filling stock code: {stock_code}")
            # Could send a quote card directly here in the future
            # For now, still show the query card
        
        card = self._stock_builder.build(
            card_type="query",
            holdings_stocks=holdings_stocks,
            watchlist_stocks=watchlist_stocks
        )
        
        return await self._send_card(chat_id, card)
    
    async def send_stock_research_start_card(self, chat_id: str) -> bool:
        """
        Send stock research start card (navigation hub).
        
        Args:
            chat_id: Target chat ID
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending stock research start card to chat: {chat_id}")
        
        card = self._stock_builder.build(card_type="research_start")
        
        return await self._send_card(chat_id, card)
    
    async def send_quote_result_card(
        self,
        chat_id: str,
        stock_code: str,
        quote: dict[str, Any]
    ) -> bool:
        """
        Send quote result card.
        
        Args:
            chat_id: Target chat ID
            stock_code: Stock code
            quote: Quote data dict
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending quote result card for {stock_code} to chat: {chat_id}")
        
        card = self._stock_builder.build(
            card_type="quote",
            stock_code=stock_code,
            quote=quote
        )
        
        return await self._send_card(chat_id, card)
    
    async def send_loading_card(
        self,
        chat_id: str,
        stock_code: str,
        analysis_type: str = "query"
    ) -> bool:
        """
        Send loading card during analysis.
        
        Args:
            chat_id: Target chat ID
            stock_code: Stock code being analyzed
            analysis_type: Type of analysis (query, technical, fundamental)
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending loading card for {stock_code} ({analysis_type}) to chat: {chat_id}")
        
        card = self._stock_builder.build(
            card_type="loading",
            stock_code=stock_code,
            analysis_type=analysis_type
        )
        
        return await self._send_card(chat_id, card)
    
    # ==================== Holdings Cards ====================
    
    async def send_holdings_display_card(
        self,
        chat_id: str,
        holdings_data: list[dict[str, Any]] | None = None
    ) -> bool:
        """
        Send holdings display card.
        
        Args:
            chat_id: Target chat ID
            holdings_data: Holdings data for display
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending holdings display card to chat: {chat_id}")
        
        card = self._holdings_builder.build(
            card_type="display",
            holdings=holdings_data
        )
        
        return await self._send_card(chat_id, card)
    
    async def send_holdings_menu_card(self, chat_id: str) -> bool:
        """
        Send holdings management menu card.
        
        Args:
            chat_id: Target chat ID
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending holdings menu card to chat: {chat_id}")
        
        card = self._holdings_builder.build(card_type="menu")
        
        return await self._send_card(chat_id, card)
    
    async def send_add_stock_to_holdings_card(
        self,
        chat_id: str,
        stock_code: str | None = None
    ) -> bool:
        """
        Send add stock to holdings card.
        
        Args:
            chat_id: Target chat ID
            stock_code: Optional pre-filled stock code
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending add to holdings card to chat: {chat_id}")
        
        card = self._holdings_builder.build(
            card_type="add",
            stock_code=stock_code
        )
        
        return await self._send_card(chat_id, card)
    
    # ==================== Watchlist Cards ====================
    
    async def send_watchlist_display_card(
        self,
        chat_id: str,
        watchlist_data: list[dict[str, Any]] | None = None
    ) -> bool:
        """
        Send watchlist display card.
        
        Args:
            chat_id: Target chat ID
            watchlist_data: Watchlist data for display (optional, will fetch if not provided)
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"[WATCHLIST_CARD] Sending watchlist display card to chat: {chat_id[:20]}...")
        
        # If watchlist_data not provided, fetch from database
        if watchlist_data is None:
            logger.info("[WATCHLIST_CARD] No data provided, fetching from database...")
            try:
                from services.daily_watchlist_manager import daily_watchlist_manager
                from database.session import async_session_maker
                
                async with async_session_maker() as db:
                    try:
                        # First check: get all dates
                        logger.info("[WATCHLIST_CARD] Step 1: Getting all dates...")
                        dates = await daily_watchlist_manager.get_all_dates(db, include_archived=False)
                        logger.info(f"[WATCHLIST_CARD] Found {len(dates)} dates in database: {dates[:5] if dates else 'none'}")
                        
                        # Get summary (grouped by date)
                        logger.info("[WATCHLIST_CARD] Step 2: Getting summary...")
                        summary = await daily_watchlist_manager.get_summary(db, include_archived=False, limit=30)
                        logger.info(f"[WATCHLIST_CARD] Summary: {summary.total_dates} dates, {summary.total_stocks} stocks")
                        
                        # Convert to flat list format for card builder
                        watchlist_data = []
                        for date_group in summary.dates:
                            logger.info(f"[WATCHLIST_CARD] Processing date {date_group.watch_date} with {date_group.total_count} stocks")
                            for stock in date_group.stocks:
                                watchlist_data.append({
                                    "date": str(stock.watch_date),
                                    "stock_name": stock.stock_name,
                                    "stock_code": stock.stock_code,
                                    "target_price": stock.target_price,
                                    "stop_loss_price": stock.stop_loss_price,
                                    "reason": stock.reason
                                })
                        
                        logger.info(f"[WATCHLIST_CARD] Step 3: Converted to {len(watchlist_data)} stock records")
                        
                    except Exception as e:
                        logger.error(f"[WATCHLIST_CARD] Database query failed: {e}", exc_info=True)
                        await db.rollback()
                        raise
                        
            except Exception as e:
                logger.error(f"[WATCHLIST_CARD] Failed to fetch watchlist data: {e}", exc_info=True)
                watchlist_data = []
        else:
            logger.info(f"[WATCHLIST_CARD] Using provided data: {len(watchlist_data)} stocks")
        
        # Build card with fetched or provided data
        logger.info(f"[WATCHLIST_CARD] Building card with {len(watchlist_data)} stocks...")
        card = self._watchlist_builder.build(
            card_type="display",
            stocks=watchlist_data,
            date_count=len(set(stock.get("date", "") for stock in watchlist_data))
        )
        
        logger.info(f"[WATCHLIST_CARD] Sending card to {chat_id[:20]}...")
        result = await self._send_card(chat_id, card)
        
        if result:
            logger.info("[WATCHLIST_CARD] ✅ Card sent successfully")
        else:
            logger.error("[WATCHLIST_CARD] ❌ Card send failed")
        
        return result
    
    async def send_watchlist_menu_card(self, chat_id: str) -> bool:
        """
        Send watchlist management menu card.
        
        Args:
            chat_id: Target chat ID
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending watchlist menu card to chat: {chat_id}")
        
        card = self._watchlist_builder.build(card_type="menu")
        
        return await self._send_card(chat_id, card)
    
    async def send_add_to_watchlist_card(
        self,
        chat_id: str,
        stock_code: str | None = None
    ) -> bool:
        """
        Send add to watchlist card.
        
        Args:
            chat_id: Target chat ID
            stock_code: Optional pre-filled stock code (currently not used)
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending add to watchlist card to chat: {chat_id}")
        
        # Get holdings stocks for selection dropdown
        holdings_stocks = []
        try:
            from services.holding_manager import HoldingManager
            from config.settings import settings
            
            holding_manager = HoldingManager(settings.holdings_file_path)
            holdings = await holding_manager.load_holdings()
            
            if holdings and holdings.sectors:
                # Extract all stocks from all sectors
                for sector in holdings.sectors:
                    for stock in sector.stocks:
                        holdings_stocks.append({
                            'name': stock.name,
                            'code': stock.code or ''
                        })
                
                logger.info(f"Loaded {len(holdings_stocks)} holdings stocks for selection")
        except Exception as e:
            logger.warning(f"Failed to load holdings stocks: {e}, continuing without them")
        
        card = self._watchlist_builder.build(
            card_type="add",
            holdings_stocks=holdings_stocks
        )
        
        return await self._send_card(chat_id, card)
    
    # ==================== Price Alert Cards ====================
    
    async def send_price_alert_menu_card(self, chat_id: str) -> bool:
        """
        Send price alert menu card.
        
        Args:
            chat_id: Target chat ID
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending price alert menu card to chat: {chat_id}")
        
        card = self._price_alert_builder.build(card_type="menu")
        
        return await self._send_card(chat_id, card)
    
    async def send_price_alert_card(self, chat_id: str) -> bool:
        logger.info(f"Sending price alert create card to chat: {chat_id}")
        card = self._price_alert_builder.build(card_type="alert")
        return await self._send_card(chat_id, card)
    
    async def send_price_query_card(
        self,
        chat_id: str,
        stock_code: str | None = None
    ) -> bool:
        """
        Send price query card.
        
        Args:
            chat_id: Target chat ID
            stock_code: Optional pre-filled stock code
            
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"Sending price query card to chat: {chat_id}")
        
        card = self._price_alert_builder.build(
            card_type="query",
            stock_code=stock_code
        )
        
        return await self._send_card(chat_id, card)
    
    async def handle_card_callback(
        self,
        chat_id: str,
        user_id: str,
        action: str,
        stock_code: str
    ) -> bool:
        if not stock_code:
            return False
        
        normalized_code = stock_code.strip()
        
        # Try to resolve stock name to code if input contains Chinese characters
        if any('\u4e00' <= char <= '\u9fff' for char in normalized_code):
            logger.info(f"[STOCK_RESOLVE] Input contains Chinese, trying to resolve stock code for: {normalized_code}")
            try:
                resolved_code = ""
                # 1. 本地映射（不依赖网络，始终可用）
                try:
                    from config.settings import settings
                    mapping_file = settings.data_dir / "stock_name_mapping.json"
                    if mapping_file.exists():
                        import json
                        with open(mapping_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            mapping = data.get('mapping', data) if isinstance(data, dict) else {}
                            resolved_code = mapping.get(normalized_code, '')
                            if resolved_code:
                                logger.info(f"[STOCK_RESOLVE] ✅ Resolved '{normalized_code}' from local mapping: {resolved_code}")
                except Exception as e:
                    logger.warning(f"[STOCK_RESOLVE] Local mapping lookup failed: {e}")

                # 2. datasource 网络搜索（后备）
                if not resolved_code:
                    try:
                        from datasource import get_datasource, DataSourceType
                        akshare_source = get_datasource().get_source(DataSourceType.AKSHARE)
                        if akshare_source and await akshare_source.is_available():
                            resolved_code = await akshare_source.search_stock_by_name(normalized_code)
                            if resolved_code:
                                logger.info(f"[STOCK_RESOLVE] ✅ Resolved '{normalized_code}' via datasource: {resolved_code}")
                    except Exception as e:
                        logger.warning(f"[STOCK_RESOLVE] Datasource search failed: {e}")

                if resolved_code:
                    normalized_code = resolved_code
                else:
                    logger.warning(f"[STOCK_RESOLVE] ⚠️ Could not resolve stock code for: {normalized_code}")
                    return await self.send_quote_result_card(
                        chat_id,
                        normalized_code,
                        {"error": f"未找到股票: {normalized_code}，请检查股票名称或直接输入股票代码"}
                    )
            except Exception as e:
                logger.error(f"[STOCK_RESOLVE] ❌ Failed to resolve stock code for {normalized_code}: {e}", exc_info=True)
                return await self.send_quote_result_card(
                    chat_id,
                    normalized_code,
                    {"error": f"股票名称解析失败: {str(e)}，请直接输入股票代码"}
                )
        
        if action == "query_price":
            action = "query_stock"
        
        await self.send_loading_card(chat_id, normalized_code, action)
        
        try:
            from services.stock_service import stock_service
            quote = await stock_service.get_quote(normalized_code, use_cache=False)
            if not quote:
                return await self.send_quote_result_card(
                    chat_id,
                    normalized_code,
                    {"error": f"未找到股票: {normalized_code}"}
                )
            
            stock_name = getattr(quote, "name", normalized_code)
            
            if action == "query_stock":
                # Get target price info from watchlist or holdings
                target_price_data = None
                
                # Strategy 1: Try to get from watchlist (daily_watchlist table)
                try:
                    from database.session import async_session_maker
                    from database.operations.watchlist_ops import get_watchlist_by_stock
                    
                    logger.info(f"[TARGET_PRICE] Strategy 1: Fetching from watchlist for {normalized_code}")
                    async with async_session_maker() as db:
                        watchlist_records = await get_watchlist_by_stock(db, normalized_code)
                        logger.info(f"[TARGET_PRICE] Found {len(watchlist_records)} watchlist records for {normalized_code}")
                        
                        if watchlist_records:
                            # Get the most recent record
                            latest_record = watchlist_records[0]
                            logger.info(f"[TARGET_PRICE] Latest record - target_price: {latest_record.target_price}, change_up_pct: {latest_record.change_up_pct}, change_down_pct: {latest_record.change_down_pct}")
                            
                            if latest_record.target_price:
                                target_price_data = {
                                    "target_price": float(latest_record.target_price),
                                    "change_up_pct": float(latest_record.change_up_pct) if latest_record.change_up_pct else None,
                                    "change_down_pct": float(latest_record.change_down_pct) if latest_record.change_down_pct else None,
                                    "stop_loss_price": float(latest_record.stop_loss_price) if latest_record.stop_loss_price else None,
                                    "notes": latest_record.notes,
                                }
                                logger.info(f"[TARGET_PRICE] ✅ Found in watchlist: {target_price_data}")
                except Exception as e:
                    logger.warning(f"[TARGET_PRICE] ❌ Failed to get from watchlist for {normalized_code}: {e}", exc_info=True)
                
                # Strategy 2: If not found in watchlist, try holdings (自持股票.md)
                if not target_price_data:
                    try:
                        from services.holdings_manager import HoldingsManager
                        
                        logger.info(f"[TARGET_PRICE] Strategy 2: Fetching from holdings for {stock_name}")
                        holdings_manager = HoldingsManager()
                        holdings_target_price = holdings_manager.get_holdings_target_price(stock_name)
                        
                        if holdings_target_price:
                            target_price_data = holdings_target_price
                            logger.info(f"[TARGET_PRICE] ✅ Found in holdings: {target_price_data}")
                        else:
                            logger.info(f"[TARGET_PRICE] ⚠️ Not found in holdings for {stock_name}")
                    except Exception as e:
                        logger.warning(f"[TARGET_PRICE] ❌ Failed to get from holdings for {stock_name}: {e}", exc_info=True)
                
                if not target_price_data:
                    logger.info(f"[TARGET_PRICE] ⚠️ No target price data found for {normalized_code} (checked both watchlist and holdings)")
                
                quote_data = {
                    "stock_name": stock_name,
                    "price": float(getattr(quote, "price", 0) or 0),
                    "change_pct": float(getattr(quote, "change_pct", 0) or 0),
                    "volume": float(getattr(quote, "volume", 0) or 0),
                    "amount": float(getattr(quote, "amount", 0) or 0),
                    "open": float(getattr(quote, "open", 0) or 0),
                    "high": float(getattr(quote, "high", 0) or 0),
                    "low": float(getattr(quote, "low", 0) or 0),
                    "prev_close": float(getattr(quote, "prev_close", 0) or 0),
                    "timestamp": str(getattr(quote, "timestamp", "")),
                    "target_price_data": target_price_data,
                }
                return await self.send_quote_result_card(chat_id, normalized_code, quote_data)
            
            if action == "technical_analysis":
                indicators = await stock_service.get_technical_indicators(normalized_code)
                if not indicators:
                    return await self._send_card(chat_id, self._stock_builder.build(
                        card_type="technical",
                        stock_code=normalized_code,
                        indicators={"error": f"技术分析失败: {normalized_code}"}
                    ))
                
                technical_data = {
                    "stock_name": stock_name,
                    "ma": {
                        "ma5": float(getattr(indicators, "ma5", 0) or 0),
                        "ma10": float(getattr(indicators, "ma10", 0) or 0),
                        "ma20": float(getattr(indicators, "ma20", 0) or 0),
                        "ma60": float(getattr(indicators, "ma20", 0) or 0),
                    },
                    "macd": {
                        "dif": float(getattr(indicators, "macd", 0) or 0),
                        "dea": float(getattr(indicators, "macd_signal", 0) or 0),
                        "macd": float(getattr(indicators, "macd_hist", 0) or 0),
                    },
                    "rsi": {
                        "rsi_14": float(getattr(indicators, "rsi", 0) or 0),
                    },
                    "kdj": {
                        "k": float(getattr(indicators, "kdj_k", 0) or 0),
                        "d": float(getattr(indicators, "kdj_d", 0) or 0),
                        "j": float(getattr(indicators, "kdj_j", 0) or 0),
                    }
                }
                return await self._send_card(chat_id, self._stock_builder.build(
                    card_type="technical",
                    stock_code=normalized_code,
                    indicators=technical_data
                ))
            
            if action == "fundamental_analysis":
                from services.fundamental_analyzer import FundamentalAnalyzer
                analyzer = FundamentalAnalyzer()
                result = await analyzer.analyze_fundamental(normalized_code)
                if not result:
                    return await self._send_card(chat_id, self._stock_builder.build(
                        card_type="fundamental",
                        stock_code=normalized_code,
                        fundamentals={"error": f"基本面分析失败: {normalized_code}"}
                    ))
                
                valuation = result.get("valuation", {}) if isinstance(result, dict) else {}
                financial_health = result.get("financial_health", {}) if isinstance(result, dict) else {}
                overall_score = result.get("overall_score", 0) if isinstance(result, dict) else 0
                fundamentals = {
                    "stock_name": stock_name,
                    "pe_ttm": float(valuation.get("pe_ttm", 0) or 0),
                    "pb": float(valuation.get("pb", 0) or 0),
                    "ps": float(valuation.get("ps", 0) or 0),
                    "peg": float(valuation.get("peg", 0) or 0),
                    "roe": float(financial_health.get("roe", 0) or 0),
                    "roa": float(financial_health.get("roa", 0) or 0),
                    "market_cap": float(valuation.get("market_cap", 0) or 0),
                    "score": float(overall_score or 0),
                }
                return await self._send_card(chat_id, self._stock_builder.build(
                    card_type="fundamental",
                    stock_code=normalized_code,
                    fundamentals=fundamentals
                ))
            
            return False
        except Exception as e:
            logger.error(f"Error handling card callback: {e}", exc_info=True)
            return await self.send_quote_result_card(
                chat_id,
                normalized_code,
                {"error": f"处理失败: {str(e)}"}
            )
    
    async def send_action_error_card(self, chat_id: str, action: str, reason: str) -> bool:
        title = f"[ERROR] 动作无效: {action}"
        card = self._action_builder.create_error_card(
            error_msg=reason,
            title=title,
            show_menu_button=True
        )
        return await self._send_card(chat_id, card)
    
    # ==================== Card Update Methods ====================
    
    async def update_card(
        self,
        message_id: str,
        card: dict[str, Any]
    ) -> bool:
        """
        Update an existing card in place.
        
        Args:
            message_id: Message ID to update
            card: New card content
            
        Returns:
            bool: True if updated successfully
        """
        if not self._sdk_card_service:
            logger.error("SDK card service not injected")
            return False
        
        logger.info(f"Updating card: {message_id}")
        
        try:
            # Delegate to SDK layer - use "success" status for generic update
            success = self._sdk_card_service.update_card_status(
                message_id=message_id,
                status="success",  # Generic status for custom content update
                card_content=card,
                update_strategy="replace"
            )
            
            if success:
                logger.info(f"[OK] Card updated successfully via SDK: {message_id}")
            else:
                logger.warning(f"[WARN] Card update failed via SDK: {message_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating card: {e}", exc_info=True)
            return False
    
    # ==================== Internal Methods ====================
    
    async def _send_card(self, chat_id: str, card: dict[str, Any]) -> bool:
        """
        Internal method to send card via SDK layer.
        
        Args:
            chat_id: Target chat ID
            card: Card content dict
            
        Returns:
            bool: True if sent successfully
        """
        if not self._sdk_card_service:
            logger.error("SDK card service not injected")
            return False
        
        logger.info(f"[APP_LAYER] Sending card via SDK to: {chat_id[:20]}...")
        
        try:
            # Determine receive_id_type based on ID prefix
            # ou_ = open_id, on_ = union_id, oc_ = chat_id
            if chat_id.startswith("ou_"):
                receive_id_type = "open_id"
            elif chat_id.startswith("on_"):
                receive_id_type = "union_id"
            elif chat_id.startswith("oc_"):
                receive_id_type = "chat_id"
            else:
                receive_id_type = "chat_id"  # Default
            
            logger.debug(f"[APP_LAYER] Detected receive_id_type: {receive_id_type}")
            
            # Delegate to SDK layer
            success, message_id = self._sdk_card_service.send_card(
                receive_id=chat_id,
                card_content=card,
                receive_id_type=receive_id_type
            )
            
            if success:
                logger.info(f"[OK] Card sent successfully via SDK to {chat_id[:20]}... (message_id: {message_id})")
                
                # Broadcast card content to frontend WebSocket
                await self._broadcast_card_to_frontend(chat_id, message_id, card)
            else:
                logger.warning("[WARN] Card send failed via SDK")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending card via SDK: {e}", exc_info=True)
            return False
    
    async def _broadcast_card_to_frontend(
        self, 
        chat_id: str, 
        message_id: str, 
        card: dict[str, Any]
    ) -> None:
        """
        Broadcast card content to frontend via WebSocket.
        
        Args:
            chat_id: Target chat ID
            message_id: Feishu message ID
            card: Card content dict
        """
        try:
            from services.websocket_manager import manager
            
            # Extract summary text from card
            summary = self._extract_card_summary(card)
            event_message_id = message_id or f"card_{uuid.uuid4().hex[:12]}"
            await self._save_card_message(
                chat_id=chat_id,
                message_id=event_message_id,
                sender_name="PegBot",
                sender_type="bot",
                content=summary
            )
            
            if summary:
                # Broadcast to all connected frontends
                await manager.broadcast({
                    "type": "feishu-chat-message",
                    "data": {
                        "chat_id": chat_id,
                        "message_id": event_message_id,
                        "sender_id": "pegbot",
                        "sender_name": "PegBot",
                        "sender_type": "bot",
                        "message_type": "card",
                        "content": summary,
                        "card_type": card.get("header", {}).get("template", "default"),
                        "send_time": datetime.now().isoformat(),
                    }
                })
                await manager.broadcast({
                    "type": "feishu-card-message",
                    "data": {
                        "chat_id": chat_id,
                        "message_id": event_message_id,
                        "sender_id": "pegbot",
                        "sender_name": "PegBot",
                        "sender_type": "bot",
                        "message_type": "card",
                        "content": summary,
                        "card_type": card.get("header", {}).get("template", "default"),
                        "send_time": datetime.now().isoformat(),
                    }
                })
                await manager.broadcast({
                    "type": "market_data_updated",
                    "data": {
                        "source": "feishu_card",
                        "chat_id": chat_id
                    }
                })
                logger.info(f"[WEBSOCKET] Card broadcasted to frontend: {chat_id[:20]}...")
            
        except Exception as e:
            logger.warning(f"Failed to broadcast card to frontend: {e}")

    async def _save_card_message(
        self,
        chat_id: str,
        message_id: str,
        sender_name: str,
        sender_type: str,
        content: str
    ) -> None:
        try:
            async with async_session_maker() as session:
                session.add(FeishuChatMessage(
                    chat_id=chat_id,
                    message_id=message_id,
                    sender_id="pegbot",
                    sender_name=sender_name,
                    sender_type=sender_type,
                    message_type="card",
                    content=content or "PegBot 卡片消息",
                    send_time=datetime.now()
                ))
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to persist card summary: {e}")
    
    def _extract_card_summary(self, card: dict[str, Any]) -> str:
        """
        Extract summary text from card for frontend display.
        
        Args:
            card: Card content dict
            
        Returns:
            str: Summary text
        """
        try:
            parts = []
            
            # Extract title from header
            header = card.get("header", {})
            title = header.get("title", {})
            if isinstance(title, dict):
                title_text = title.get("content", "")
                if title_text:
                    parts.append(f"**{title_text}**")
            
            # Extract text from body elements (limit to first 3 text elements)
            body = card.get("body", {})
            elements = body.get("elements", [])
            
            for elem in elements[:5]:  # Check first 5 elements
                if isinstance(elem, dict):
                    text = elem.get("text", {})
                    if isinstance(text, dict):
                        content = text.get("content", "")
                        if content and len(parts) < 4:  # Max 4 lines
                            # Clean up markdown for summary
                            clean_content = content.replace("**", "").replace("\n", " ")
                            if len(clean_content) > 50:
                                clean_content = clean_content[:50] + "..."
                            parts.append(clean_content)
            
            return "\n".join(parts) if parts else "卡片消息"
            
        except Exception as e:
            logger.warning(f"Failed to extract card summary: {e}")
            return "卡片消息"


__all__ = ['CardService']
