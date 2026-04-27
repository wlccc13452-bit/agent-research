"""持仓管理服务"""
import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import aiofiles
import logging

from models import Holdings, SectorInfo, StockInfo

logger = logging.getLogger(__name__)


class HoldingsFileWatcher:
    """文件变更监控器"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.last_modified = 0.0
        self.callbacks = []
        self._running = False
        
        if self.file_path.exists():
            self.last_modified = os.path.getmtime(self.file_path)
    
    def on_file_changed(self, callback):
        """注册文件变更回调"""
        self.callbacks.append(callback)
    
    async def watch(self):
        """监控文件变更（优化版：降低检查频率）"""
        self._running = True
        logger.info(f"开始监控文件: {self.file_path}")
        
        while self._running:
            try:
                exists = await asyncio.to_thread(self.file_path.exists)
                if exists:
                    current_modified = await asyncio.to_thread(os.path.getmtime, self.file_path)
                    if current_modified != self.last_modified:
                        self.last_modified = current_modified
                        logger.info(f"[OK] 检测到 {self.file_path.name} 文件变更")
                        for callback in self.callbacks:
                            try:
                                await callback()
                            except Exception as e:
                                logger.error(f"执行回调失败: {str(e)}")
            except Exception as e:
                logger.error(f"监控文件变更失败: {str(e)}")
            
            await asyncio.sleep(2)  # 优化：每2秒检查一次（降低CPU占用）
    
    def stop(self):
        """停止监控"""
        self._running = False
        logger.info("文件监控已停止")


class HoldingManager:
    """持仓管理服务（单例模式）"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, file_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, file_path: str = None):
        # 避免重复初始化
        if HoldingManager._initialized:
            return
        
        if file_path is None:
            from config.settings import settings
            file_path = str(settings.holdings_file_path)
            
        self.file_path = Path(file_path).absolute()
        self.holdings: Optional[Holdings] = None
        self.watcher: Optional[HoldingsFileWatcher] = None
        self.last_modified: float = 0.0  # 记录文件最后修改时间
        logger.info(f"[START] HoldingManager 初始化，文件路径: {self.file_path}")
        HoldingManager._initialized = True
    
    async def _ensure_file_exists(self):
        """确保文件存在 (异步执行避免阻塞)"""
        exists = await asyncio.to_thread(self.file_path.exists)
        if not exists:
            logger.info(f"创建持仓文件: {self.file_path}")
            def _create():
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                self.file_path.write_text("# 自持股票\n", encoding='utf-8')
            await asyncio.to_thread(_create)
    
    async def load_holdings(self) -> Holdings:
        """从文件加载持仓数据（Non-Blocking版本）
        
        核心原则：
        1. 立即返回现有数据（不等待加载）
        2. 首次加载立即返回本地数据，后台异步解析真实代码
        3. 文件变更时返回旧缓存，后台异步更新
        """
        # 优化1：如果已有缓存且文件未修改，直接返回缓存
        if self.holdings:
            try:
                current_modified = await asyncio.to_thread(os.path.getmtime, self.file_path)
                if current_modified == self.last_modified:
                    logger.debug("持仓数据未变化，使用缓存")
                    return self.holdings
                else:
                    # 文件已修改，返回旧缓存，后台异步更新
                    logger.info("持仓文件已变更，返回旧缓存，后台异步更新...")
                    asyncio.create_task(self._reload_holdings_background())
                    return self.holdings
            except Exception as e:
                logger.warning(f"检查文件修改时间失败: {str(e)}，返回现有缓存")
                return self.holdings
        
        # 优化2：首次加载，立即读取文件并返回（使用临时代码）
        try:
            await self._ensure_file_exists()
            
            # 记录文件修改时间
            self.last_modified = await asyncio.to_thread(os.path.getmtime, self.file_path)
            
            async with aiofiles.open(self.file_path, 'r', encoding='utf-8-sig') as f:
                content = await f.read()
            
            # 解析Markdown格式
            sectors = []
            current_sector = None
            
            logger.info(f"开始从 {self.file_path} 解析自持股票数据，文件大小: {len(content)} 字符")
            
            lines = content.split('\n')
            
            # 收集所有需要解析代码的股票
            stock_tasks = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 跳过空行和主标题
                if not line or line.startswith('# '):
                    continue
                    
                if line.startswith('## '):
                    # 板块标题
                    sector_name = line[3:].strip()
                    current_sector = SectorInfo(name=sector_name, stocks=[])
                    sectors.append(current_sector)
                elif current_sector:
                    # 股票名称（可能包含额外信息）
                    stock_line = line
                    if stock_line.startswith('- ') or stock_line.startswith('* '):
                        stock_line = stock_line[2:].strip()
                    
                    # 解析额外信息（目标价等）
                    stock_name = stock_line
                    target_price = None
                    change_up_pct = None
                    change_down_pct = None
                    
                    # 检查是否有 HTML 注释格式的额外信息
                    if '<!--' in stock_line and '-->' in stock_line:
                        import re
                        match = re.search(r'(.+?)\s*<!--\s*(.+?)\s*-->', stock_line)
                        if match:
                            stock_name = match.group(1).strip()
                            extra_info = match.group(2)
                            
                            # 解析额外信息字段
                            for field in extra_info.split(','):
                                field = field.strip()
                                if ':' in field:
                                    key, value = field.split(':', 1)
                                    key = key.strip()
                                    try:
                                        if key == 'target_price':
                                            target_price = float(value.strip())
                                        elif key == 'change_up_pct':
                                            change_up_pct = float(value.strip())
                                        elif key == 'change_down_pct':
                                            change_down_pct = float(value.strip())
                                    except ValueError:
                                        logger.warning(f"[WARN] 无法解析字段值: {field}")
                    
                    # ✅ 关键优化：立即添加股票（使用临时代码）
                    temp_code = f"TEMP_{stock_name}"
                    stock_info = StockInfo(
                        code=temp_code,
                        name=stock_name,
                        sector=current_sector.name,
                        target_price=target_price,
                        change_up_pct=change_up_pct,
                        change_down_pct=change_down_pct
                    )
                    current_sector.stocks.append(stock_info)
                    
                    # 记录需要解析真实代码的任务
                    stock_tasks.append({
                        'name': stock_name,
                        'temp_code': temp_code,
                        'sector': current_sector,
                        'line_no': i + 1
                    })
            
            # 立即返回数据（包含临时代码）
            self.holdings = Holdings(
                sectors=sectors,
                last_updated=datetime.now()
            )
            
            total_stocks = sum(len(s.stocks) for s in sectors)
            logger.info(f"[OK] Holdings loaded immediately: {len(sectors)} sectors, {total_stocks} stocks (使用临时代码)")
            
            # 后台异步解析真实代码
            if stock_tasks:
                logger.info(f"启动后台解析 {len(stock_tasks)} 只股票的真实代码...")
                asyncio.create_task(self._resolve_stock_codes_background(stock_tasks))
            
            return self.holdings
            
        except Exception as e:
            logger.error(f"加载持仓数据失败: {str(e)}")
            return Holdings(sectors=[], last_updated=datetime.now())
    
    async def _resolve_stock_codes_background(self, stock_tasks: List[Dict]):
        """后台解析股票真实代码"""
        try:
            logger.info(f"[BACKGROUND] 开始解析 {len(stock_tasks)} 只股票的真实代码...")
            
            for task in stock_tasks:
                try:
                    # 解析真实代码
                    real_code = await self._get_stock_code_by_name(task['name'])
                    
                    if real_code and not real_code.startswith('TEMP_'):
                        # 更新 holdings 中的代码
                        for stock in task['sector'].stocks:
                            if stock.code == task['temp_code']:
                                stock.code = real_code
                                logger.info(f"[BACKGROUND] 更新代码: {task['name']} {task['temp_code']} → {real_code}")
                                break
                    
                    # 让出控制权，避免阻塞
                    await asyncio.sleep(0)
                    
                except Exception as e:
                    logger.error(f"[BACKGROUND] 解析 {task['name']} 失败: {str(e)}")
            
            # 更新最后修改时间
            self.holdings.last_updated = datetime.now()
            
            # 广播更新通知
            try:
                from services.websocket_manager import manager as websocket_manager
                await websocket_manager.broadcast({
                    'type': 'holdings_updated',
                    'message': '股票代码已更新',
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"[BACKGROUND] 已广播持仓更新通知")
            except Exception as e:
                logger.warning(f"广播持仓更新失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"后台解析股票代码失败: {str(e)}")
    
    async def _reload_holdings_background(self):
        """后台重新加载持仓数据（异步，不阻塞）"""
        try:
            # 保存旧的 holdings，以便加载失败时恢复
            old_holdings = self.holdings
            
            # 强制清除缓存，重新加载
            self.holdings = None
            self.last_modified = 0.0
            
            # 重新加载
            new_holdings = await self.load_holdings()
            
            if new_holdings and new_holdings.sectors:
                total_stocks = sum(len(s.stocks) for s in new_holdings.sectors)
                logger.info(f"[OK] 后台重新加载成功: {len(new_holdings.sectors)} 个板块, {total_stocks} 只股票")
                
                # 广播更新通知给前端
                try:
                    from services.websocket_manager import manager as websocket_manager
                    await websocket_manager.broadcast({
                        'type': 'holdings_updated',
                        'message': '持仓数据已更新',
                        'timestamp': datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"广播持仓更新失败: {str(e)}")
            else:
                # 加载失败，恢复旧数据
                logger.warning("后台重新加载失败，恢复旧数据")
                self.holdings = old_holdings
                
        except Exception as e:
            logger.error(f"后台重新加载持仓数据失败: {str(e)}")
            # 恢复旧数据
            if 'old_holdings' in locals():
                self.holdings = old_holdings
    
    async def save_holdings(self, holdings: Holdings) -> bool:
        """保存持仓数据到文件"""
        try:
            content = "# 自持股票\n\n"
            for sector in holdings.sectors:
                content += f"## {sector.name}\n"
                for stock in sector.stocks:
                    # 保存股票名称和额外信息（如果有）
                    extras = []
                    if stock.target_price:
                        extras.append(f"target_price:{stock.target_price}")
                    if stock.change_up_pct:
                        extras.append(f"change_up_pct:{stock.change_up_pct}")
                    if stock.change_down_pct:
                        extras.append(f"change_down_pct:{stock.change_down_pct}")
                    
                    if extras:
                        content += f"- {stock.name} <!-- {', '.join(extras)} -->\n"
                    else:
                        content += f"- {stock.name}\n"
                content += "\n"
            
            def _write():
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                self.file_path.write_text(content, encoding='utf-8')
            
            await asyncio.to_thread(_write)
            
            # 更新文件修改时间缓存
            self.last_modified = await asyncio.to_thread(os.path.getmtime, self.file_path)
            
            logger.info(f"成功保存持仓数据到 {self.file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存持仓数据失败: {str(e)}")
            return False
    
    async def add_stock(self, sector_name: str, stock_name: str, 
                       stock_code: Optional[str] = None) -> bool:
        """添加股票"""
        if not self.holdings:
            await self.load_holdings()
        
        # 查找或创建板块
        sector = next((s for s in self.holdings.sectors if s.name == sector_name), None)
        if not sector:
            sector = SectorInfo(name=sector_name, stocks=[])
            self.holdings.sectors.append(sector)
        
        # 检查股票是否已存在
        if any(s.name == stock_name for s in sector.stocks):
            logger.warning(f"股票 {stock_name} 已存在于板块 {sector_name}")
            return False
        
        # 获取股票代码 (强制通过 API)
        if not stock_code:
            stock_code = await self._get_stock_code_by_name(stock_name)
        
        if not stock_code:
            logger.error(f"无法为股票 {stock_name} 获取有效的股票代码，添加失败")
            return False
        
        # 添加股票
        sector.stocks.append(StockInfo(
            code=stock_code,
            name=stock_name,
            sector=sector_name
        ))
        
        # 保存到文件
        self.holdings.last_updated = datetime.now()
        return await self.save_holdings(self.holdings)
    
    async def remove_stock(self, sector_name: str, stock_name: str) -> bool:
        """删除股票"""
        if not self.holdings:
            await self.load_holdings()
        
        sector = next((s for s in self.holdings.sectors if s.name == sector_name), None)
        if not sector:
            logger.warning(f"板块 {sector_name} 不存在")
            return False
        
        # 删除股票
        original_count = len(sector.stocks)
        sector.stocks = [s for s in sector.stocks if s.name != stock_name]
        
        if len(sector.stocks) == original_count:
            logger.warning(f"股票 {stock_name} 不存在于板块 {sector_name}")
            return False
        
        self.holdings.last_updated = datetime.now()
        return await self.save_holdings(self.holdings)
    
    async def update_stock(self, sector_name: str, old_name: str, 
                          new_name: Optional[str] = None, 
                          new_code: Optional[str] = None,
                          new_sector: Optional[str] = None) -> bool:
        """更新股票信息"""
        if not self.holdings:
            await self.load_holdings()
        
        sector = next((s for s in self.holdings.sectors if s.name == sector_name), None)
        if not sector:
            logger.warning(f"板块 {sector_name} 不存在")
            return False
        
        stock = next((s for s in sector.stocks if s.name == old_name), None)
        if not stock:
            logger.warning(f"股票 {old_name} 不存在于板块 {sector_name}")
            return False
        
        # 更新股票信息
        if new_name:
            stock.name = new_name
        if new_code:
            stock.code = new_code
        if new_sector:
            # 移动到其他板块
            new_sector_obj = next((s for s in self.holdings.sectors if s.name == new_sector), None)
            if not new_sector_obj:
                logger.warning(f"目标板块 {new_sector} 不存在")
                return False
            
            sector.stocks.remove(stock)
            stock.sector = new_sector
            new_sector_obj.stocks.append(stock)
        
        self.holdings.last_updated = datetime.now()
        return await self.save_holdings(self.holdings)
    
    async def add_sector(self, sector_name: str) -> bool:
        """添加板块"""
        if not self.holdings:
            await self.load_holdings()
        
        if any(s.name == sector_name for s in self.holdings.sectors):
            logger.warning(f"板块 {sector_name} 已存在")
            return False
        
        self.holdings.sectors.append(SectorInfo(name=sector_name, stocks=[]))
        self.holdings.last_updated = datetime.now()
        return await self.save_holdings(self.holdings)
    
    async def remove_sector(self, sector_name: str) -> bool:
        """删除板块"""
        if not self.holdings:
            await self.load_holdings()
        
        sector = next((s for s in self.holdings.sectors if s.name == sector_name), None)
        if not sector:
            logger.warning(f"板块 {sector_name} 不存在")
            return False
        
        if sector.stocks:
            logger.warning(f"板块 {sector_name} 下还有股票，无法删除")
            return False
        
        self.holdings.sectors = [s for s in self.holdings.sectors if s.name != sector_name]
        self.holdings.last_updated = datetime.now()
        return await self.save_holdings(self.holdings)
    
    async def rename_sector(self, old_name: str, new_name: str) -> bool:
        """重命名板块"""
        if not self.holdings:
            await self.load_holdings()
        
        sector = next((s for s in self.holdings.sectors if s.name == old_name), None)
        if not sector:
            logger.warning(f"板块 {old_name} 不存在")
            return False
        
        if any(s.name == new_name for s in self.holdings.sectors):
            logger.warning(f"板块 {new_name} 已存在")
            return False
        
        sector.name = new_name
        # 更新板块下股票的sector字段
        for stock in sector.stocks:
            stock.sector = new_name
        
        self.holdings.last_updated = datetime.now()
        return await self.save_holdings(self.holdings)
    
    async def update_stock_target(self, sector_name: str, stock_name: str,
                                   target_price: Optional[float] = None,
                                   change_up_pct: Optional[float] = None,
                                   change_down_pct: Optional[float] = None) -> bool:
        """更新股票目标价和涨跌控制比例"""
        if not self.holdings:
            await self.load_holdings()
        
        sector = next((s for s in self.holdings.sectors if s.name == sector_name), None)
        if not sector:
            logger.warning(f"板块 {sector_name} 不存在")
            return False
        
        stock = next((s for s in sector.stocks if s.name == stock_name), None)
        if not stock:
            logger.warning(f"股票 {stock_name} 不存在于板块 {sector_name}")
            return False
        
        # 更新目标价信息
        stock.target_price = target_price
        stock.change_up_pct = change_up_pct
        stock.change_down_pct = change_down_pct
        
        self.holdings.last_updated = datetime.now()
        return await self.save_holdings(self.holdings)
    
    async def _get_stock_code_by_name(self, stock_name: str) -> Optional[str]:
        """根据股票名称获取股票代码 (必须通过 API 获取)"""
        start_time = datetime.now()
        code = None
        
        # 0. 常用股票静态映射 (作为 API 失败时的备选)
        static_mapping = {
            "南山铝业": "600219",
            "中国神华": "601088",
            "隆基绿能": "601012",
            "中国中钨高新": "000657",
            "雅化集团": "002497",
            "赣锋锂业": "002460",
        }
        
        if stock_name in static_mapping:
            code = static_mapping[stock_name]
            logger.info(f"[STATIC] 使用静态映射: {stock_name} → {code}")
            return code
        
        # 1. 调用 datasource API 动态搜索
        try:
            from datasource import get_datasource, DataSourceType
            
            akshare_source = get_datasource().get_source(DataSourceType.AKSHARE)
            if akshare_source and await akshare_source.is_available():
                code = await akshare_source.search_stock_by_name(stock_name)
                if code:
                    logger.info(f"[API] 动态搜索成功: {stock_name} → {code}")
                    return code
        except Exception as e:
            logger.warning(f"[API] 动态搜索失败: {str(e)}")
        
        # 2. 失败时返回 UNKNOWN_前缀代码
        duration = (datetime.now() - start_time).total_seconds()
        if duration > 1.0:
            logger.warning(f"[WARN] 解析股票 {stock_name} 代码耗时较长: {duration:.2f}秒")
            
        if not code:
            code = f"UNKNOWN_{stock_name}"
            logger.warning(f"无法通过 API 解析股票 {stock_name} 的代码，使用临时代码: {code}")
            
        return code
    
    def start_watching(self):
        """启动文件监控"""
        if not self.watcher:
            self.watcher = HoldingsFileWatcher(str(self.file_path))
            self.watcher.on_file_changed(self._on_file_changed)
            asyncio.create_task(self.watcher.watch())
            logger.info("持仓文件监控已启动")
    
    def stop_watching(self):
        """停止文件监控"""
        if self.watcher:
            self.watcher.stop()
            logger.info("持仓文件监控已停止")
    
    async def _on_file_changed(self):
        """文件变更回调"""
        logger.info("持仓文件已变更，重新加载")
        try:
            await self.load_holdings()
            logger.info("[OK] 持仓数据重新加载成功")
            
            # 广播更新通知给所有WebSocket客户端
            try:
                from services.realtime_pusher import realtime_pusher
                await realtime_pusher.broadcast({
                    "type": "holdings_updated",
                    "message": "持仓数据已更新",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"广播持仓更新失败: {str(e)}")
                
        except Exception as e:
            logger.error(f"重新加载持仓数据失败: {str(e)}")
