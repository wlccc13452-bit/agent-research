"""Business Logic Service

负责飞书业务逻辑处理，包括：
- 持仓管理
- 关注列表管理
- 价格预警管理
- 监控任务管理
- 查询和表单处理
"""

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
import asyncio

from database.session import async_session_maker
from database.operations import (
    check_watchlist_exists,
    add_to_watchlist,
    get_watchlist_by_stock,
    get_recent_watchlist_stocks,
    remove_from_watchlist,
    create_price_alert,
    stop_alert_monitoring as stop_alert_monitoring_op,
    get_alert_by_id,
    adjust_alert_threshold,
)
from services.feishu_bot.cards import ActionCardsBuilder
from feishu_sdk.config.protocols import CardServiceProtocol

logger = logging.getLogger(__name__)


class BusinessLogicService:
    """业务逻辑处理服务
    
    职责：
    1. 持仓管理（添加、删除、查询）
    2. 关注列表管理
    3. 价格预警管理
    4. 监控任务管理
    5. 表单提交处理
    """
    
    def __init__(self) -> None:
        self._card_service: Optional[CardServiceProtocol] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
    
    def set_card_service(self, card_service: CardServiceProtocol) -> None:
        """注入卡片服务"""
        self._card_service = card_service
    
    def set_main_loop(self, main_loop: asyncio.AbstractEventLoop) -> None:
        """设置主事件循环"""
        self._main_loop = main_loop
    
    # ===== 快捷查询 =====
    
    async def handle_quick_view(self, action_type: str, chat_id: str) -> None:
        """处理快捷查询（持仓、关注列表）"""
        try:
            if not self._card_service:
                logger.error("Card service not available")
                await self._send_error_card(chat_id, "服务未就绪")
                return
            
            if action_type == 'view_holdings':
                # Get holdings data
                from services.holdings_manager import HoldingsManager
                holdings_manager = HoldingsManager()
                holdings_data = holdings_manager.read_holdings()
                logger.info(f"[DATA] Retrieved holdings with {len(holdings_data.get('sectors', []))} sectors")
                success = await self._card_service.send_holdings_display_card(chat_id, holdings_data)
            elif action_type == 'view_watchlist':
                success = await self._card_service.send_watchlist_display_card(chat_id)
            else:
                logger.warning(f"Unknown quick view action: {action_type}")
                return
            
            if success:
                logger.info(f"[OK] {action_type} card sent successfully")
            else:
                logger.warning(f"[WARN]️ {action_type} card send failed")
                await self._send_error_card(chat_id, "卡片发送失败")
                
        except Exception as e:
            logger.error(f"快捷查询处理失败: {e}", exc_info=True)
            await self._send_error_card(chat_id, f"快捷查询失败: {str(e)}")
    
    # ===== 菜单导航 =====
    
    async def send_menu_card(self, action_type: str, chat_id: str) -> None:
        """发送菜单卡片"""
        try:
            if not self._card_service:
                logger.error("Card service not available")
                return
            
            # 菜单映射表
            menu_map = {
                'main_menu': self._card_service.send_main_menu_card,
                'stock_query_menu': self._card_service.send_stock_query_card,
                'price_query_menu': self._card_service.send_price_query_card,
                'holdings_menu': self._card_service.send_holdings_menu_card,
                'watchlist_menu': self._card_service.send_watchlist_menu_card,
                'price_alert_menu': self._card_service.send_price_alert_menu_card,
                'view_holdings': self._card_service.send_holdings_menu_card,
                'add_stock_to_holdings': self._card_service.send_add_stock_to_holdings_card,
                'add_sector_to_holdings': self._card_service.send_holdings_menu_card,
                'remove_stock_from_holdings': self._card_service.send_holdings_menu_card,
                'remove_sector_from_holdings': self._card_service.send_holdings_menu_card,
                'view_watchlist': self._card_service.send_watchlist_menu_card,
                'add_to_watchlist': self._card_service.send_add_to_watchlist_card,
                'remove_from_watchlist': self._card_service.send_watchlist_display_card,
                'view_price_alerts': self._card_service.send_price_alert_menu_card,
                'create_price_alert': self._card_service.send_price_alert_card,
                'create_monitor': self._card_service.send_monitor_setup_card,
                'monitor_setup': self._card_service.send_monitor_setup_card,
                'create_price_monitor': self._card_service.send_monitor_config_card,
            }
            
            send_method = menu_map.get(action_type)
            if send_method:
                success = await send_method(chat_id)
                if success:
                    logger.info(f"[OK] 菜单卡片已发送: {action_type}")
                else:
                    logger.warning(f"[ERROR] 菜单卡片发送失败: {action_type}")
                    await self._send_error_card(chat_id, f"菜单加载失败")
            else:
                logger.warning(f"未知的菜单类型: {action_type}")
                await self._send_error_card(chat_id, f"未知菜单")
                
        except Exception as e:
            logger.error(f"发送菜单卡片失败: {e}", exc_info=True)
            await self._send_error_card(chat_id, f"菜单加载失败: {str(e)}")
    
    # ===== 操作菜单 =====
    
    async def send_stock_action_menu(
        self,
        action_type: str,
        chat_id: str,
        stock_code: str,
        stock_name: str,
        action_value: dict
    ) -> None:
        """
        发送股票综合分析卡片(直接显示所有分析结果,无需再点击按钮)
        
        优化用户体验:选择股票后直接显示行情+技术+基本面三合一分析
        """
        try:
            if not self._card_service:
                await self._send_error_card(chat_id, "服务未就绪")
                return
            
            is_holdings = action_type == 'show_stock_actions'
            sector_name = action_value.get('sector_name', '')
            watch_date = action_value.get('watch_date', '')
            
            logger.info(f"[COMPREHENSIVE] Starting comprehensive analysis for {stock_name} ({stock_code})")
            
            # 发送加载卡片
            await self._card_service.send_loading_card(chat_id, stock_code, "comprehensive_analysis")
            
            # 导入所需模块
            import asyncio
            from services.stock_service import stock_service
            
            # 定义并行获取函数
            async def fetch_quote():
                """获取实时行情（优先缓存）"""
                try:
                    # ✅ 修复：使用缓存，避免每次网络请求
                    quote = await stock_service.get_quote(stock_code, use_cache=True)
                    if quote:
                        return {
                            "stock_name": stock_name,
                            "price": float(getattr(quote, "price", 0) or 0),
                            "change_pct": float(getattr(quote, "change_pct", 0) or 0),
                            "volume": float(getattr(quote, "volume", 0) or 0),
                            "amount": float(getattr(quote, "amount", 0) or 0),
                            "open": float(getattr(quote, "open", 0) or 0),
                            "high": float(getattr(quote, "high", 0) or 0),
                            "low": float(getattr(quote, "low", 0) or 0),
                            "prev_close": float(getattr(quote, "prev_close", 0) or 0),
                        }
                except Exception as e:
                    logger.warning(f"[COMPREHENSIVE] Failed to get quote: {e}")
                return {"error": "行情获取失败"}
            
            async def fetch_indicators():
                """获取技术指标（优先缓存/数据库）"""
                try:
                    # ✅ 技术指标已有缓存机制，直接调用
                    indicators = await stock_service.get_technical_indicators(stock_code)
                    if indicators:
                        return {
                            "ma": {
                                "ma5": float(getattr(indicators, "ma5", 0) or 0),
                                "ma10": float(getattr(indicators, "ma10", 0) or 0),
                                "ma20": float(getattr(indicators, "ma20", 0) or 0),
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
                except Exception as e:
                    logger.warning(f"[COMPREHENSIVE] Failed to get indicators: {e}")
                return {"error": "技术分析失败"}
            
            async def fetch_fundamentals():
                """获取基本面分析（优先本地数据库，绝不等待网络）"""
                try:
                    # ✅ 优先从本地数据库获取
                    from database.session import async_session_maker
                    from database.operations import get_fundamental_metrics
                    
                    async with async_session_maker() as db:
                        metrics = await get_fundamental_metrics(db, stock_code)
                        
                        if metrics:
                            logger.info(f"[COMPREHENSIVE] Got fundamentals from local DB for {stock_code}")
                            return {
                                "pe_ttm": float(metrics.valuation.get('pe_ttm', 0) or 0),
                                "pb": float(metrics.valuation.get('pb', 0) or 0),
                                "ps": float(metrics.valuation.get('ps_ttm', 0) or 0),
                                "peg": float(metrics.valuation.get('peg', 0) or 0),
                                "roe": float(metrics.financial_health.get('roe', 0) or 0),
                                "roa": float(metrics.financial_health.get('roa', 0) or 0),
                                "market_cap": float(metrics.valuation.get('market_cap', 0) or 0),
                                "score": float(metrics.valuation.get('score', 0) or 0),
                            }
                    
                    # 本地无数据，返回空（不等待网络更新）
                    logger.warning(f"[COMPREHENSIVE] No local fundamentals for {stock_code}, returning empty")
                    return {}
                    
                except Exception as e:
                    logger.warning(f"[COMPREHENSIVE] Failed to get fundamentals from local DB: {e}")
                    return {}
            
            # ✅ 真正并行获取三个分析结果
            quote_data, indicators_data, fundamentals_data = await asyncio.gather(
                fetch_quote(),
                fetch_indicators(),
                fetch_fundamentals(),
                return_exceptions=False
            )
            
            logger.info(f"[COMPREHENSIVE] Data fetched in parallel for {stock_code}")
            
            # 构建综合分析卡片
            comprehensive_card = self._card_service._stock_builder.build(
                card_type="comprehensive",
                stock_code=stock_code,
                stock_name=stock_name,
                quote=quote_data,
                indicators=indicators_data,
                fundamentals=fundamentals_data,
                is_holdings=is_holdings,
                sector_name=sector_name,
                watch_date=watch_date
            )
            
            # 发送卡片
            success = await self._card_service._send_card(chat_id, comprehensive_card)
            
            if success:
                logger.info(f"[OK] Sent comprehensive analysis for {stock_name} ({stock_code})")
            else:
                logger.warning(f"[WARN]️ Failed to send comprehensive analysis for {stock_name}")
                await self._send_error_card(chat_id, "发送综合分析失败")
                
        except Exception as e:
            logger.error(f"[ERROR] Error sending comprehensive analysis: {e}", exc_info=True)
            await self._send_error_card(chat_id, f"发送综合分析失败: {str(e)}")
    
    # ===== 查询输入卡片 =====
    
    async def send_query_input_card(self, action_type: str, chat_id: str) -> None:
        """发送查询输入卡片"""
        try:
            if not self._card_service:
                await self._send_error_card(chat_id, "服务未就绪")
                return
            
            if action_type in ['query_stock', 'technical_analysis', 'fundamental_analysis']:
                await self._card_service.send_stock_query_card(chat_id)
            elif action_type == 'query_price':
                await self._card_service.send_price_query_card(chat_id)
                
        except Exception as e:
            logger.error(f"发送查询输入卡片失败: {e}", exc_info=True)
            await self._send_error_card(chat_id, f"发送查询卡片失败: {str(e)}")
    
    # ===== 表单提交处理 =====
    
    async def handle_form_submission(
        self,
        chat_id: str,
        user_id: str,
        action: str,
        form_data: dict[str, Any],
        message_id: Optional[str] = None
    ) -> None:
        """处理表单提交"""
        try:
            logger.info(f"处理表单提交: {action}")
            logger.info(f"  - form_data: {form_data}")
            
            # TODO: 实现加载状态更新（需要添加 update_to_loading 方法到 CardService）
            
            # 路由到具体的处理方法
            if action == 'confirm_add_stock_holdings':
                title, content, status = await self._handle_holdings_add(chat_id, form_data)
                
            elif action == 'confirm_add_watchlist':
                title, content, status = await self._handle_watchlist_add(chat_id, form_data)
                
            elif action == 'confirm_create_price_alert':
                title, content, status = await self._handle_price_alert_submission(chat_id, form_data)
                
            elif action == 'save_monitor_task':
                title, content, status = await self._handle_monitor_task_submission(chat_id, form_data)
                
            else:
                logger.warning(f"未识别的表单提交动作: {action}")
                title = "未知操作"
                content = f"未识别的操作类型: {action}"
                status = "failed"
            
            # 发送结果卡片
            if title and content:
                await self._send_operation_result_card(
                    chat_id=chat_id,
                    title=title,
                    message=content,
                    status=status,
                    message_id=message_id
                )
            
            logger.info(f"[OK] 表单处理完成: {action}")
            
        except Exception as e:
            logger.error(f"表单处理失败: {e}", exc_info=True)
            await self._send_operation_result_card(
                chat_id=chat_id,
                title="处理失败",
                message=f"处理过程中发生错误:\n{str(e)}",
                status="failed",
                message_id=message_id
            )
    
    async def _handle_holdings_add(
        self,
        chat_id: str,
        form_data: dict[str, Any]
    ) -> tuple[str, str, str]:
        """处理添加持仓"""
        try:
            from services.holdings_manager import HoldingsManager
            
            stock_name = form_data.get('stock_name', '').strip()
            sector_name = form_data.get('sector_name', '').strip()
            
            if not stock_name or not sector_name:
                return "添加失败", "股票名称和板块名称不能为空", "failed"
            
            holdings_manager = HoldingsManager()
            success = holdings_manager.add_stock(stock_name, sector_name)
            
            if success:
                return (
                    "添加成功",
                    f"[OK] 已将 {stock_name} 添加到 {sector_name} 板块\n\n可以发送\"持仓\"查看更新后的持仓列表",
                    "success"
                )
            else:
                return "添加失败", f"股票 {stock_name} 已存在于持仓中或添加失败", "failed"
                
        except Exception as e:
            logger.error(f"Failed to add stock to holdings: {e}", exc_info=True)
            return "添加失败", f"添加过程中发生错误: {str(e)}", "failed"
    
    async def _handle_watchlist_add(
        self,
        chat_id: str,
        form_data: dict[str, Any]
    ) -> tuple[str, str, str]:
        """处理添加关注列表
        
        支持多种输入方式：
        1. 从持仓下拉选择 (stock_select)
        2. 手动输入股票名称或代码 (stock_input)
        
        自动识别股票代码或名称，获取对应信息
        """
        try:
            from services.daily_watchlist_manager import daily_watchlist_manager
            from database.operations import check_watchlist_exists, add_to_watchlist
            from database.session import async_session_maker
            import re
            
            # 获取日期（从action_value或默认今天）
            watch_date = form_data.get('watch_date', '') or date.today().isoformat()
            
            # 尝试从多个来源获取股票信息
            stock_name = ""
            stock_code = ""
            
            # 方式1: 从下拉选择获取
            stock_select = form_data.get('stock_select', '').strip()
            if stock_select:
                # 处理"手动输入"选项
                if stock_select == "manual_input":
                    return "需要输入", "请直接发送股票名称或代码（如：贵州茅台、600519）\n\n系统会自动识别并添加到关注列表", "pending"
                
                # 处理"暂无持仓"选项
                if stock_select == "no_holdings":
                    return "添加失败", "请直接发送股票名称或代码（如：贵州茅台、600519）", "failed"
                
                # 格式: "stock_code|stock_name"
                if "|" in stock_select:
                    parts = stock_select.split("|")
                    stock_code = parts[0].strip()
                    stock_name = parts[1].strip() if len(parts) > 1 else ""
                else:
                    stock_code = stock_select
            
            # 方式2: 从手动输入获取
            if not stock_code:
                user_input = form_data.get('stock_input', '').strip()
                
                # ✅ 如果 form_data 为空，尝试从缓存获取
                if not user_input:
                    from feishu_sdk.core.long_connection_service import input_cache
                    cached_input = input_cache.get(chat_id, {}).get('stock_input', '')
                    if cached_input:
                        user_input = cached_input.strip()
                        logger.info(f"[CACHE] Retrieved stock_input from cache: {user_input}")
                
                if not user_input:
                    return "添加失败", "请输入股票名称或代码，或从持仓列表选择", "failed"
                
                # 判断输入是股票代码还是名称
                # 股票代码格式: 6位数字 (沪深A股)，或以SH/SZ/BK开头
                is_stock_code = bool(re.match(r'^[0-9]{6}$', user_input)) or user_input.startswith(('SH', 'SZ', 'BK'))
                
                if is_stock_code:
                    # 输入的是股票代码
                    stock_code = user_input
                    stock_name = await self._get_stock_name_from_code(stock_code)
                    if not stock_name:
                        stock_name = stock_code
                else:
                    # 输入的是股票名称
                    stock_name = user_input
                    stock_code = await self._get_stock_code_from_mapping(stock_name)
                    if not stock_code:
                        stock_code = await self._search_stock_code_by_name(stock_name)
            
            if not stock_code:
                stock_code = f"UNKNOWN_{stock_name}"
            
            if not stock_name:
                stock_name = stock_code
            
            # 添加到数据库
            async with async_session_maker() as db:
                try:
                    # 检查是否已存在
                    existing = await check_watchlist_exists(db, date.fromisoformat(watch_date), stock_code)
                    
                    if existing:
                        return "添加失败", f"股票 {stock_name} ({stock_code}) 已存在于 {watch_date} 的关注列表中", "failed"
                    
                    # 创建新的关注记录
                    new_watch = await add_to_watchlist(
                        db=db,
                        watch_date=date.fromisoformat(watch_date),
                        stock_code=stock_code,
                        stock_name=stock_name,
                        target_price=None,
                        stop_loss_price=None,
                        reason=None
                    )
                    
                    return (
                        "添加成功",
                        f"已将 {stock_name} ({stock_code}) 添加到关注列表\n\n日期: {watch_date}",
                        "success"
                    )
                    
                except Exception as e:
                    await db.rollback()
                    raise
                    
        except Exception as e:
            logger.error(f"Failed to add stock to watchlist: {e}", exc_info=True)
            return "添加失败", f"添加过程中发生错误: {str(e)}", "failed"
    
    async def _get_stock_name_from_code(self, stock_code: str) -> str:
        """根据股票代码获取股票名称"""
        try:
            from services.stock_service import stock_service
            
            quote = await stock_service.get_quote(stock_code, use_cache=True)
            if quote and hasattr(quote, 'name'):
                return quote.name
        except Exception as e:
            logger.warning(f"Failed to get stock name for {stock_code}: {e}")
        
        return ""
    
    async def _search_stock_code_by_name(self, stock_name: str) -> str:
        """根据股票名称搜索股票代码"""
        try:
            from datasource import get_datasource, DataSourceType
            
            akshare_source = get_datasource().get_source(DataSourceType.AKSHARE)
            if akshare_source:
                # 使用 datasource 的搜索方法
                stock_code = await akshare_source.search_stock_by_name(stock_name)
                if stock_code:
                    return stock_code
        except Exception as e:
            logger.warning(f"Failed to search stock code for {stock_name}: {e}")
        
        return ""
    
    async def _resolve_stock_input(self, user_input: str) -> tuple[str, str]:
        """自动判断输入是股票名称还是代码，解析为 (stock_code, stock_name)

        解析优先级：
        1. 输入匹配股票代码格式（6位数字 / SH.SZ前缀）→ 直接当代码，反查名称
        2. 输入包含中文 → 当名称处理：
           a. 本地映射文件（stock_name_mapping.json）
           b. akshare 模糊搜索
        """
        import re

        raw = user_input.strip()
        if not raw:
            return ("", "")

        # 判断是否是股票代码格式
        is_code = bool(re.match(r'^[0-9]{6}$', raw)) or raw.upper().startswith(('SH', 'SZ', 'BK'))

        if is_code:
            code = raw
            name = await self._get_stock_name_from_code(code)
            if not name:
                name = code
            return (code, name)

        # 输入包含中文字符，当作股票名称处理
        stock_name = raw
        stock_code = ""

        # 1. 本地映射
        stock_code = await self._get_stock_code_from_mapping(stock_name)

        # 2. akshare 搜索
        if not stock_code:
            stock_code = await self._search_stock_code_by_name(stock_name)

        if not stock_code:
            stock_code = f"UNKNOWN_{stock_name}"

        return (stock_code, stock_name)

    async def _handle_price_alert_submission(
        self,
        chat_id: str,
        form_data: dict[str, Any]
    ) -> tuple[str, str, str]:
        """
        处理价格提醒提交

        支持多种输入方式：
        1. 从持仓下拉选择 (stock_select)
        2. 手动输入股票代码或名称 (stock_code_input 或 stock_code)

        自动识别股票代码或名称，获取对应信息
        """
        try:
            from database.operations import create_price_alert
            from services.stock_service import stock_service
            from database.session import async_session_maker

            # 尝试从多个来源获取股票代码
            stock_code = ""
            stock_name = ""

            # 方式1: 从下拉选择获取
            stock_select = form_data.get('stock_select', '').strip()
            if stock_select:
                # 格式: "stock_code" (直接是股票代码)
                stock_code = stock_select

            # 方式2: 从手动输入获取（支持两种字段名）
            user_input = ""
            if not stock_code:
                user_input = form_data.get('stock_code_input', '').strip()
            if not user_input:
                user_input = form_data.get('stock_code', '').strip()

            # 自动识别输入是股票名称还是代码
            if user_input:
                stock_code, stock_name = await self._resolve_stock_input(user_input)
                logger.info(f"[STOCK_RESOLVE] price_alert: input='{user_input}' -> code='{stock_code}', name='{stock_name}'")

            # 获取其他表单字段
            target_price = form_data.get('target_price', '').strip()
            change_up_pct = form_data.get('change_up_pct', '').strip()
            change_down_pct = form_data.get('change_down_pct', '').strip()
            ref_price = form_data.get('ref_price', '').strip()  # 兼容 ref_price
            change_rate = form_data.get('change_rate', '').strip()  # 兼容 change_rate
            notes = form_data.get('notes', '').strip()

            if not stock_code or stock_code.startswith("UNKNOWN_"):
                return ("创建失败", f"无法识别股票: **{user_input}**，请输入正确的股票名称或代码", "failed")
            
            # 获取股票信息
            quote = await stock_service.get_quote(stock_code, use_cache=False)
            if not quote:
                return ("创建失败", f"无法找到股票: **{stock_code}**", "failed")
            
            # 优先使用已解析的名称，fallback 到 quote 返回的名称
            if not stock_name:
                stock_name = getattr(quote, 'name', stock_code)
            base_price = Decimal(str(quote.price))
            
            # 解析预警条件（支持多种字段名）
            target_price_decimal = Decimal(target_price) if target_price else None
            change_up_decimal = Decimal(change_up_pct) if change_up_pct else None
            change_down_decimal = Decimal(change_down_pct) if change_down_pct else None
            
            # 兼容 change_rate 字段（如果有设置，作为上下涨跌幅）
            if change_rate and not change_up_decimal and not change_down_decimal:
                rate_decimal = Decimal(change_rate)
                change_up_decimal = rate_decimal
                change_down_decimal = rate_decimal
            
            # 兼容 ref_price 字段（如果有设置，作为基准价格）
            if ref_price:
                base_price = Decimal(ref_price)
            
            if not any([target_price_decimal, change_up_decimal, change_down_decimal]):
                return ("创建失败", "至少需要设置一个提醒条件", "failed")
            
            # 保存到数据库
            async with async_session_maker() as db:
                try:
                    alert = await create_price_alert(
                        db=db,
                        stock_code=stock_code,
                        stock_name=stock_name,
                        base_price=base_price,
                        current_price=Decimal(str(quote.price)),
                        current_change_pct=Decimal(str(quote.change_pct)),
                        feishu_chat_id=chat_id,
                        target_price=target_price_decimal,
                        change_up_pct=change_up_decimal,
                        change_down_pct=change_down_decimal,
                        notes=notes
                    )
                    await self._broadcast_frontend_update("price_alert_created", stock_code)
                    return ("价格提醒已创建", f"**股票**: {stock_name} ({stock_code})\n**基准价格**: ¥{base_price}", "success")
                    
                except Exception as e:
                    await db.rollback()
                    raise
            
        except Exception as e:
            logger.error(f"价格提醒处理失败: {e}", exc_info=True)
            return ("创建失败", f"处理过程中发生错误:\n{str(e)}", "failed")
    
    async def _handle_monitor_task_submission(
        self,
        chat_id: str,
        form_data: dict[str, Any]
    ) -> tuple[str, str, str]:
        """处理监控任务提交"""
        try:
            from services.price_alert_manager import price_alert_manager
            from database.session import async_session_maker

            user_input = form_data.get('stock_code', '').strip()
            ref_price_str = form_data.get('ref_price', '').strip()
            change_rate_str = form_data.get('change_rate', '').strip()
            up_alert_pct_str = form_data.get('up_alert_pct', '').strip()
            down_alert_pct_str = form_data.get('down_alert_pct', '').strip()
            notes = form_data.get('notes', '').strip()

            if not user_input:
                return ("创建失败", "股票代码不能为空", "failed")

            # 自动识别输入是股票名称还是代码
            stock_code, stock_name = await self._resolve_stock_input(user_input)
            logger.info(f"[STOCK_RESOLVE] monitor_task: input='{user_input}' -> code='{stock_code}', name='{stock_name}'")

            if not stock_code or stock_code.startswith("UNKNOWN_"):
                return ("创建失败", f"无法识别股票: **{user_input}**，请输入正确的股票名称或代码", "failed")
            
            # 解析预警百分比
            up_alert_pct = None
            down_alert_pct = None
            
            if change_rate_str:
                try:
                    change_rate = float(change_rate_str)
                    up_alert_pct = change_rate
                    down_alert_pct = -change_rate
                except ValueError:
                    return ("创建失败", f"无效的变化率: **{change_rate_str}**", "failed")
            else:
                if up_alert_pct_str:
                    up_alert_pct = float(up_alert_pct_str)
                if down_alert_pct_str:
                    down_alert_pct = -float(down_alert_pct_str)
            
            if not up_alert_pct and not down_alert_pct:
                return ("创建失败", "至少需要设置一个预警条件", "failed")
            
            # 解析参考价格
            ref_price = float(ref_price_str) if ref_price_str else None
            
            # 创建监控任务
            async with async_session_maker() as db:
                try:
                    alert = await price_alert_manager.create_alert(
                        db=db,
                        stock_code=stock_code,
                        target_price=ref_price,
                        change_up_pct=up_alert_pct,
                        change_down_pct=down_alert_pct,
                        feishu_chat_id=chat_id,
                        notes=notes
                    )
                    
                    logger.info(f"[OK] 监控任务已创建 (ID: {alert.id})")
                    await self._broadcast_frontend_update("price_monitor_created", stock_code)
                    return ("监控任务已开启", f"**股票**: {alert.stock_name} ({alert.stock_code})\n**基准价格**: ¥{alert.base_price}", "success")
                    
                except Exception as e:
                    await db.rollback()
                    raise
            
        except Exception as e:
            logger.error(f"监控任务处理失败: {e}", exc_info=True)
            return ("创建失败", f"处理过程中发生错误:\n{str(e)}", "failed")

    async def _broadcast_frontend_update(self, event: str, stock_code: str) -> None:
        try:
            from services.websocket_manager import manager
            await manager.broadcast({
                "type": "market_data_updated",
                "data": {
                    "source": "feishu_bot",
                    "event": event,
                    "stock_code": stock_code
                }
            })
        except Exception as e:
            logger.warning(f"前端更新广播失败: {e}")
    
    # ===== 预警管理 =====
    
    async def stop_alert_monitoring(self, chat_id: str, alert_id: int) -> None:
        """停止价格监控"""
        try:
            from database.operations import stop_alert_monitoring
            from database.session import async_session_maker
            
            logger.info(f"停止监控: alert_id={alert_id}")
            
            async with async_session_maker() as db:
                try:
                    success = await stop_alert_monitoring(db, alert_id)
                    
                    if success:
                        await self._send_operation_result_card(
                            chat_id=chat_id,
                            title="监控已停止",
                            message=f"预警任务 (ID: {alert_id}) 已成功停止",
                            status="success"
                        )
                    
                except Exception as e:
                    await db.rollback()
                    raise
                    
        except Exception as e:
            logger.error(f"停止监控失败: {e}", exc_info=True)
            await self._send_operation_result_card(
                chat_id=chat_id,
                title="停止失败",
                message=f"停止监控时发生错误:\n{str(e)}",
                status="failed"
            )
    
    async def modify_alert_threshold(self, chat_id: str, alert_id: int, stock_code: str) -> None:
        """修改预警阈值"""
        try:
            from database.operations import get_alert_by_id
            from database.session import async_session_maker
            
            logger.info(f"修改阈值: alert_id={alert_id}, stock={stock_code}")
            
            async with async_session_maker() as db:
                try:
                    alert = await get_alert_by_id(db, alert_id)
                    
                    if alert:
                        # 发送提示消息
                        await self._send_operation_result_card(
                            chat_id=chat_id,
                            title="修改阈值",
                            message=f"请使用「创建监控」功能重新设置 {stock_code} 的监控参数。\n\n当前基准价格: ¥{alert.base_price}",
                            status="success"
                        )
                    else:
                        await self._send_operation_result_card(
                            chat_id=chat_id,
                            title="修改失败",
                            message=f"未找到预警任务 (ID: {alert_id})",
                            status="failed"
                        )
                        
                except Exception as e:
                    await db.rollback()
                    raise
                    
        except Exception as e:
            logger.error(f"修改阈值失败: {e}", exc_info=True)
            await self._send_operation_result_card(
                chat_id=chat_id,
                title="修改失败",
                message=f"修改阈值时发生错误:\n{str(e)}",
                status="failed"
            )
    
    async def quick_adjust_threshold(
        self,
        chat_id: str,
        alert_id: int,
        stock_code: str,
        adjustment: str
    ) -> None:
        """快捷调整预警阈值"""
        try:
            from database.operations import get_alert_by_id, adjust_alert_threshold
            from database.session import async_session_maker
            
            logger.info(f"快捷调整阈值: alert_id={alert_id}, adjustment={adjustment}")
            
            # 确定调整幅度
            adjustment_pct = Decimal('0')
            if adjustment == 'up_5pct':
                adjustment_pct = Decimal('5.0')
            elif adjustment == 'down_5pct':
                adjustment_pct = Decimal('-5.0')
            elif adjustment == 'up_3pct':
                adjustment_pct = Decimal('3.0')
            elif adjustment == 'down_3pct':
                adjustment_pct = Decimal('-3.0')
            else:
                await self._send_operation_result_card(
                    chat_id=chat_id,
                    title="调整失败",
                    message=f"未知调整类型: {adjustment}",
                    status="failed"
                )
                return
            
            async with async_session_maker() as db:
                try:
                    alert = await get_alert_by_id(db, alert_id)
                    
                    if not alert:
                        await self._send_operation_result_card(
                            chat_id=chat_id,
                            title="调整失败",
                            message=f"预警任务不存在 (ID: {alert_id})",
                            status="failed"
                        )
                        return
                    
                    success, updated_fields = await adjust_alert_threshold(db, alert_id, adjustment_pct)
                    
                    if success:
                        await self._send_operation_result_card(
                            chat_id=chat_id,
                            title="阈值已调整",
                            message=f"**股票**: {stock_code}\n**调整幅度**: {adjustment_pct:+.1f}%",
                            status="success"
                        )
                    
                except Exception as e:
                    await db.rollback()
                    raise
                    
        except Exception as e:
            logger.error(f"快捷调整失败: {e}", exc_info=True)
            await self._send_operation_result_card(
                chat_id=chat_id,
                title="调整失败",
                message=f"快捷调整时发生错误:\n{str(e)}",
                status="failed"
            )
    
    # ===== 删除操作 =====
    
    async def delete_stock(
        self,
        action_type: str,
        chat_id: str,
        stock_code: str,
        stock_name: str,
        action_value: dict
    ) -> None:
        """删除股票"""
        try:
            if action_type == 'delete_stock_from_holdings':
                await self._delete_from_holdings(chat_id, stock_name, action_value)
            elif action_type == 'delete_stock_from_watchlist':
                await self._delete_from_watchlist(chat_id, stock_code, stock_name)
                
        except Exception as e:
            logger.error(f"删除操作失败: {e}", exc_info=True)
            await self._send_error_card(chat_id, f"删除失败: {str(e)}")
    
    async def _delete_from_holdings(
        self,
        chat_id: str,
        stock_name: str,
        action_value: dict
    ) -> None:
        """从持仓删除"""
        from services.holdings_manager import HoldingsManager
        
        holdings_manager = HoldingsManager()
        sector_name = action_value.get('sector_name')
        success = holdings_manager.remove_stock(stock_name, sector_name)
        
        if success:
            await self._send_operation_result_card(
                chat_id=chat_id,
                title="删除成功",
                message=f"已从持仓中删除: {stock_name}",
                status="success"
            )
            
            # 刷新持仓显示
            if self._card_service:
                from services.holdings_manager import HoldingsManager
                holdings_manager = HoldingsManager()
                holdings_data = holdings_manager.read_holdings()
                await self._card_service.send_holdings_display_card(chat_id, holdings_data)
        else:
            await self._send_operation_result_card(
                chat_id=chat_id,
                title="删除失败",
                message=f"未找到该股票: {stock_name}",
                status="failed"
            )
    
    async def _delete_from_watchlist(
        self,
        chat_id: str,
        stock_code: str,
        stock_name: str
    ) -> None:
        """从关注列表删除"""
        from database.session import async_session_maker
        from database.operations import get_watchlist_by_stock, remove_from_watchlist
        
        async with async_session_maker() as db:
            try:
                # 使用 ops 函数查询关注列表
                stocks = await get_watchlist_by_stock(db, stock_code, stock_name)
                
                if stocks:
                    stock_ids = [stock.id for stock in stocks]
                    deleted_count = await remove_from_watchlist(db, stock_ids=stock_ids)
                    
                    await self._send_operation_result_card(
                        chat_id=chat_id,
                        title="删除成功",
                        message=f"已从关注列表删除: {stock_name} (共{deleted_count}条记录)",
                        status="success"
                    )
                    
                    # 刷新关注列表显示
                    if self._card_service:
                        await self._card_service.send_watchlist_display_card(chat_id)
                else:
                    await self._send_operation_result_card(
                        chat_id=chat_id,
                        title="删除失败",
                        message=f"未找到该股票: {stock_name}",
                        status="failed"
                    )
                    
            except Exception as e:
                await db.rollback()
                raise
    
    # ===== 工具方法 =====
    
    async def _get_stock_code_from_mapping(self, stock_name: str) -> str:
        """从映射文件获取股票代码"""
        try:
            from config.settings import settings
            
            mapping_file = settings.data_dir / "stock_name_mapping.json"
            if mapping_file.exists():
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    mapping = data.get('mapping', data) if isinstance(data, dict) else {}
                    return mapping.get(stock_name, '')
        except Exception:
            pass
        
        return ''
    
    async def _send_error_card(self, chat_id: str, error_message: str) -> None:
        """发送错误卡片"""
        try:
            if not self._card_service:
                return
            
            builder = ActionCardsBuilder()
            error_card = builder.create_error_card(
                error_msg=error_message,
                title="[ERROR] 系统错误",
                show_menu_button=True
            )
            
            await self._card_service._send_card(chat_id, error_card)
            
        except Exception as e:
            logger.error(f"发送错误卡片失败: {e}", exc_info=True)
    
    async def _send_operation_result_card(
        self,
        chat_id: str,
        title: str,
        message: str,
        status: str = "success",
        message_id: Optional[str] = None
    ) -> None:
        """发送操作结果卡片"""
        try:
            if not self._card_service:
                logger.warning("Cannot send result card: card service not available")
                return
            
            # 创建结果卡片
            builder = ActionCardsBuilder()
            color = "green" if status == "success" else "red"
            icon = "✅" if status == "success" else "❌"
            
            card = {
                "schema": "2.0",
                "header": {
                    "template": color,
                    "title": {"tag": "plain_text", "content": f"{icon} {title}"}
                },
                "body": {
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": message
                            }
                        },
                        {"tag": "hr"},
                        {
                            "tag": "column_set",
                            "flex_mode": "stretch",
                            "columns": [
                                {
                                    "tag": "column",
                                    "width": "weighted",
                                    "weight": 1,
                                    "elements": [
                                        {
                                            "tag": "button",
                                            "text": {"tag": "plain_text", "content": "返回主菜单"},
                                            "type": "default",
                                            "size": "medium",
                                            "value": {"action": "main_menu"}
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
            
            # 如果有 message_id，尝试原位更新
            if message_id:
                logger.info(f"🔄 尝试原位更新卡片: message_id={message_id}")
                success = await self._card_service.update_card(message_id, card)
                
                if success:
                    logger.info(f"[OK] 卡片已原位更新: {title}")
                    return
                else:
                    logger.warning(f"[WARN]️ 原位更新失败，降级为发送新卡片: {title}")
            
            # 发送新卡片
            success = await self._card_service._send_card(chat_id, card)
            
            if success:
                logger.info(f"[OK] 结果卡片已发送: {title}")
            else:
                logger.warning(f"[WARN]️ 结果卡片发送失败: {title}")
            
        except Exception as e:
            logger.error(f"Failed to send operation result card: {e}", exc_info=True)
    
    # ===== 数据获取方法 (供卡片构建器使用) =====
    
    def get_holdings_stocks(self) -> list[dict[str, str]]:
        """获取持仓股票列表
        
        Returns:
            list[dict]: 股票列表，格式为 [{'name': '股票名', 'code': '股票代码'}, ...]
        """
        try:
            from services.holdings_manager import HoldingsManager
            from config.settings import settings
            
            holdings_manager = HoldingsManager()
            holdings_data = holdings_manager.read_holdings()
            
            stocks = []
            for sector in holdings_data.get('sectors', []):
                for stock_name in sector.get('stocks', []):
                    # 尝试从映射获取股票代码
                    stock_code = self._get_stock_code_from_mapping_sync(stock_name)
                    stocks.append({
                        'name': stock_name,
                        'code': stock_code,
                        'sector': sector.get('name', '')
                    })
            
            logger.info(f"[OK] Retrieved {len(stocks)} holdings stocks")
            return stocks
            
        except Exception as e:
            logger.error(f"Failed to get holdings stocks: {e}", exc_info=True)
            return []
    
    async def get_watchlist_stocks_async(self) -> list[dict[str, str]]:
        """异步获取关注列表股票
        
        Returns:
            list[dict]: 股票列表，格式为 [{'name': '股票名', 'code': '股票代码'}, ...]
        """
        try:
            from database.session import async_session_maker
            from database.operations import get_recent_watchlist_stocks
            
            async with async_session_maker() as db:
                try:
                    # 使用 ops 函数获取最近7天的关注股票
                    watchlist_items = await get_recent_watchlist_stocks(db, days=7, limit=20)
                    
                    stocks = []
                    seen_codes = set()
                    
                    for item in watchlist_items:
                        if item.stock_code not in seen_codes:
                            stocks.append({
                                'name': item.stock_name,
                                'code': item.stock_code,
                                'watch_date': str(item.watch_date)
                            })
                            seen_codes.add(item.stock_code)
                    
                    logger.info(f"[OK] Retrieved {len(stocks)} watchlist stocks")
                    return stocks
                    
                except Exception as e:
                    await db.rollback()
                    raise
                    
        except Exception as e:
            logger.error(f"Failed to get watchlist stocks: {e}", exc_info=True)
            return []
    
    def get_watchlist_stocks(self) -> list[dict[str, str]]:
        """同步获取关注列表股票（向后兼容）
        
        Returns:
            list[dict]: 股票列表
        """
        try:
            import asyncio
            
            # 尝试在运行中的事件循环中执行
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，创建一个新的任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.get_watchlist_stocks_async()
                    )
                    return future.result(timeout=5)
            except RuntimeError:
                # 没有运行中的事件循环，直接运行
                return asyncio.run(self.get_watchlist_stocks_async())
                
        except Exception as e:
            logger.error(f"Failed to get watchlist stocks (sync): {e}", exc_info=True)
            return []
    
    def _get_stock_code_from_mapping_sync(self, stock_name: str) -> str:
        """同步获取股票代码"""
        try:
            from config.settings import settings
            
            mapping_file = settings.data_dir / "stock_name_mapping.json"
            if mapping_file.exists():
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    mapping = data.get('mapping', data) if isinstance(data, dict) else {}
                    return mapping.get(stock_name, '')
        except Exception:
            pass
        
        return ''
    
    # ===== WebSocket长连接专用方法 =====
    
    async def handle_stock_query(
        self,
        action_type: str,
        chat_id: str,
        stock_code: str
    ) -> None:
        """处理股票查询操作(WebSocket长连接调用)"""
        try:
            logger.info(f"[QUERY] Handling stock query: {action_type} for {stock_code}")
            
            if not self._card_service:
                logger.error("Card service not available")
                return
            
            # 发送查询卡片
            if action_type in ["query_stock", "technical_analysis", "fundamental_analysis"]:
                await self._card_service.send_stock_query_card(chat_id, stock_code)
            else:
                logger.warning(f"Unknown query action: {action_type}")
                
        except Exception as e:
            logger.error(f"Failed to handle stock query: {e}", exc_info=True)
    
    async def handle_form_submission_ws(
        self,
        action_type: str,
        chat_id: str,
        form_data: dict[str, Any],
        action_value: dict[str, Any]
    ) -> None:
        """处理表单提交(WebSocket长连接调用)"""
        try:
            logger.info(f"[FORM] Processing form submission: {action_type}")
            
            # 调用现有的表单处理方法
            await self.handle_form_submission(
                chat_id=chat_id,
                user_id="",  # WebSocket不传递user_id
                action=action_type,
                form_data=form_data,
                message_id=None
            )
            
        except Exception as e:
            logger.error(f"Failed to handle form submission: {e}", exc_info=True)
    
    async def handle_delete_action(
        self,
        action_type: str,
        chat_id: str,
        action_value: dict[str, Any]
    ) -> None:
        """处理删除操作(WebSocket长连接调用)"""
        try:
            logger.info(f"[DELETE] Processing delete action: {action_type}")
            
            stock_code = action_value.get("stock_code", "")
            stock_name = action_value.get("stock_name", "")
            
            # 调用现有的删除方法
            await self.delete_stock(
                action_type=action_type,
                chat_id=chat_id,
                stock_code=stock_code,
                stock_name=stock_name,
                action_value=action_value
            )
            
        except Exception as e:
            logger.error(f"Failed to handle delete action: {e}", exc_info=True)


# 单例实例
business_logic_service = BusinessLogicService()
