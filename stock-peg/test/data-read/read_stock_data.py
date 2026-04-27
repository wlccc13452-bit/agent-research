"""
股票数据读取测试工具
直接从数据库读取股票数据，使用server端相同的服务和流程
"""
import sys
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

# 添加backend路径到sys.path，以便导入server端模块
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# 导入server端模块
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import async_session_maker
from services.quote_data_service import QuoteDataService
from services.stock_data_service import StockDataService
from database.models import (
    StockRealtimeQuote, 
    StockKLineData, 
    DailyReport,
    FundamentalMetrics,
    DataSourceTrack
)
from sqlalchemy import select, func


class StockDataTestApp:
    """股票数据测试应用"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("股票数据读取测试工具 (Server端服务)")
        self.root.geometry("1200x800")
        
        # 初始化服务
        self.quote_service = QuoteDataService()
        self.stock_data_service = StockDataService()
        
        # 创建GUI
        self._create_widgets()
        
        # 加载股票列表
        self.root.after(100, self._load_stock_list)
    
    def _create_widgets(self):
        """创建界面组件"""
        # 顶部：股票选择区
        top_frame = ttk.LabelFrame(self.root, text="股票选择", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(top_frame, text="股票代码:").grid(row=0, column=0, padx=5, pady=5)
        
        self.stock_combo = ttk.Combobox(top_frame, width=20, state='normal')
        self.stock_combo.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(top_frame, text="加载数据", command=self._load_data).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(top_frame, text="刷新列表", command=self._load_stock_list).grid(row=0, column=3, padx=5, pady=5)
        
        # 数据类型选择
        ttk.Label(top_frame, text="数据类型:").grid(row=0, column=4, padx=5, pady=5)
        self.data_type_var = tk.StringVar(value="realtime_quote")
        data_types = [
            ("实时行情", "realtime_quote"),
            ("K线数据", "kline"),
            ("每日报告", "daily_report"),
            ("基本面指标", "fundamental"),
            ("数据来源追踪", "data_source")
        ]
        
        col = 5
        for text, value in data_types:
            ttk.Radiobutton(
                top_frame, text=text, value=value, 
                variable=self.data_type_var,
                command=self._on_data_type_change
            ).grid(row=0, column=col, padx=5, pady=5)
            col += 1
        
        # K线周期选择
        self.period_frame = ttk.Frame(top_frame)
        self.period_frame.grid(row=1, column=0, columnspan=10, pady=5)
        ttk.Label(self.period_frame, text="K线周期:").pack(side=tk.LEFT, padx=5)
        self.period_var = tk.StringVar(value="day")
        for text, value in [("日K", "day"), ("周K", "week"), ("月K", "month")]:
            ttk.Radiobutton(
                self.period_frame, text=text, value=value,
                variable=self.period_var
            ).pack(side=tk.LEFT, padx=5)
        self.period_frame.grid_remove()  # 默认隐藏
        
        # 中部：数据显示区
        middle_frame = ttk.LabelFrame(self.root, text="数据内容", padding=10)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.data_text = scrolledtext.ScrolledText(
            middle_frame, 
            wrap=tk.WORD,
            font=("Consolas", 10)
        )
        self.data_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部：状态栏
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(bottom_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT)
        
        ttk.Button(
            bottom_frame, 
            text="复制到剪贴板",
            command=self._copy_to_clipboard
        ).pack(side=tk.RIGHT, padx=5)
    
    def _on_data_type_change(self):
        """数据类型改变时更新界面"""
        if self.data_type_var.get() == "kline":
            self.period_frame.grid()
        else:
            self.period_frame.grid_remove()
    
    def _load_stock_list(self):
        """加载股票列表"""
        async def _async_load():
            async with async_session_maker() as db:
                # 从多个表获取股票代码
                stocks = set()
                
                # 1. 从实时行情表
                result = await db.execute(
                    select(StockRealtimeQuote.stock_code, StockRealtimeQuote.stock_name)
                )
                for row in result:
                    stocks.add(f"{row.stock_code} - {row.stock_name or ''}")
                
                # 2. 从K线表
                result = await db.execute(
                    select(StockKLineData.stock_code).distinct()
                )
                for row in result:
                    stocks.add(f"{row.stock_code}")
                
                # 3. 从每日报告表
                result = await db.execute(
                    select(DailyReport.stock_code, DailyReport.stock_name).distinct()
                )
                for row in result:
                    stocks.add(f"{row.stock_code} - {row.stock_name or ''}")
                
                return sorted(list(stocks))
        
        try:
            stocks = asyncio.run(_async_load())
            self.stock_combo['values'] = stocks
            if stocks:
                self.stock_combo.current(0)
            self.status_label.config(text=f"已加载 {len(stocks)} 个股票")
        except Exception as e:
            messagebox.showerror("错误", f"加载股票列表失败: {e}")
            self.status_label.config(text="加载失败")
    
    def _load_data(self):
        """加载选中股票的数据"""
        selected = self.stock_combo.get()
        if not selected:
            messagebox.showwarning("提示", "请选择股票代码")
            return
        
        # 提取股票代码（去除名称部分）
        stock_code = selected.split(" - ")[0].strip()
        data_type = self.data_type_var.get()
        
        self.status_label.config(text="加载中...")
        self.data_text.delete(1.0, tk.END)
        
        try:
            if data_type == "realtime_quote":
                data = asyncio.run(self._get_realtime_quote(stock_code))
            elif data_type == "kline":
                period = self.period_var.get()
                data = asyncio.run(self._get_kline_data(stock_code, period))
            elif data_type == "daily_report":
                data = asyncio.run(self._get_daily_reports(stock_code))
            elif data_type == "fundamental":
                data = asyncio.run(self._get_fundamental_metrics(stock_code))
            elif data_type == "data_source":
                data = asyncio.run(self._get_data_source_track(stock_code))
            else:
                data = None
            
            if data:
                self._display_data(data, data_type)
                self.status_label.config(text=f"已加载 {len(data) if isinstance(data, list) else 1} 条记录")
            else:
                self.data_text.insert(tk.END, "未找到数据")
                self.status_label.config(text="无数据")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")
            self.status_label.config(text="加载失败")
    
    async def _get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """获取实时行情（使用server端服务）"""
        async with async_session_maker() as db:
            # 使用server端的QuoteDataService
            quote = await self.quote_service.get_quote_from_db(db, stock_code)
            
            if quote:
                return {
                    "code": quote.code,
                    "name": quote.name,
                    "price": quote.price,
                    "change": quote.change,
                    "change_pct": quote.change_pct,
                    "open": quote.open,
                    "high": quote.high,
                    "low": quote.low,
                    "volume": quote.volume,
                    "amount": quote.amount,
                    "timestamp": quote.timestamp.isoformat() if quote.timestamp else None
                }
            return None
    
    async def _get_kline_data(self, stock_code: str, period: str) -> List[Dict]:
        """获取K线数据"""
        async with async_session_maker() as db:
            result = await db.execute(
                select(StockKLineData)
                .where(StockKLineData.stock_code == stock_code)
                .where(StockKLineData.period == period)
                .order_by(StockKLineData.trade_date.desc())
                .limit(100)
            )
            rows = result.scalars().all()
            
            return [
                {
                    "trade_date": str(row.trade_date),
                    "open": float(row.open),
                    "close": float(row.close),
                    "high": float(row.high),
                    "low": float(row.low),
                    "volume": int(row.volume) if row.volume else 0,
                    "amount": float(row.amount) if row.amount else 0.0
                }
                for row in rows
            ]
    
    async def _get_daily_reports(self, stock_code: str) -> List[Dict]:
        """获取每日报告"""
        async with async_session_maker() as db:
            result = await db.execute(
                select(DailyReport)
                .where(DailyReport.stock_code == stock_code)
                .order_by(DailyReport.report_date.desc())
                .limit(10)
            )
            rows = result.scalars().all()
            
            data = []
            for row in rows:
                item = {
                    "report_date": str(row.report_date),
                    "open_price": float(row.open_price) if row.open_price else None,
                    "close_price": float(row.close_price) if row.close_price else None,
                    "high_price": float(row.high_price) if row.high_price else None,
                    "low_price": float(row.low_price) if row.low_price else None,
                    "change_pct": float(row.change_pct) if row.change_pct else None,
                    "volume": int(row.volume) if row.volume else None,
                }
                
                # 添加技术指标
                if row.ma5:
                    item["ma5"] = float(row.ma5)
                if row.ma10:
                    item["ma10"] = float(row.ma10)
                if row.ma20:
                    item["ma20"] = float(row.ma20)
                if row.macd:
                    item["macd"] = float(row.macd)
                
                # 添加基本面数据
                if row.pe_ratio:
                    item["pe_ratio"] = float(row.pe_ratio)
                if row.pb_ratio:
                    item["pb_ratio"] = float(row.pb_ratio)
                
                # 添加评分和建议
                if row.overall_score:
                    item["overall_score"] = row.overall_score
                if row.action:
                    item["action"] = row.action
                if row.summary:
                    item["summary"] = row.summary[:200]  # 截断摘要
                
                # 智能分析
                if row.smart_analysis:
                    try:
                        item["smart_analysis"] = json.loads(row.smart_analysis)
                    except:
                        pass
                
                data.append(item)
            
            return data
    
    async def _get_fundamental_metrics(self, stock_code: str) -> List[Dict]:
        """获取基本面指标"""
        async with async_session_maker() as db:
            result = await db.execute(
                select(FundamentalMetrics)
                .where(FundamentalMetrics.stock_code == stock_code)
                .order_by(FundamentalMetrics.report_date.desc())
                .limit(10)
            )
            rows = result.scalars().all()
            
            return [
                {
                    "report_date": str(row.report_date),
                    "pe_ttm": float(row.pe_ttm) if row.pe_ttm else None,
                    "pe_lyr": float(row.pe_lyr) if row.pe_lyr else None,
                    "pb": float(row.pb) if row.pb else None,
                    "peg": float(row.peg) if row.peg else None,
                    "roe": float(row.roe) if row.roe else None,
                    "roa": float(row.roa) if row.roa else None,
                    "revenue_cagr_3y": float(row.revenue_cagr_3y) if row.revenue_cagr_3y else None,
                    "debt_ratio": float(row.debt_ratio) if row.debt_ratio else None,
                    "overall_score": float(row.overall_score) if row.overall_score else None,
                }
                for row in rows
            ]
    
    async def _get_data_source_track(self, stock_code: str) -> List[Dict]:
        """获取数据来源追踪"""
        async with async_session_maker() as db:
            result = await db.execute(
                select(DataSourceTrack)
                .where(DataSourceTrack.stock_code == stock_code)
                .order_by(DataSourceTrack.read_time.desc())
                .limit(50)
            )
            rows = result.scalars().all()
            
            return [
                {
                    "read_time": str(row.read_time),
                    "data_type": row.data_type,
                    "data_source": row.data_source,
                    "source_location": row.source_location,
                    "is_updating": row.is_updating,
                    "last_update_time": str(row.last_update_time) if row.last_update_time else None,
                }
                for row in rows
            ]
    
    def _display_data(self, data: Any, data_type: str):
        """显示数据"""
        self.data_text.delete(1.0, tk.END)
        
        # 标题
        title_map = {
            "realtime_quote": "实时行情数据",
            "kline": "K线数据",
            "daily_report": "每日分析报告",
            "fundamental": "基本面指标",
            "data_source": "数据来源追踪"
        }
        
        self.data_text.insert(tk.END, f"=== {title_map.get(data_type, '数据')} ===\n\n")
        
        # 格式化JSON输出
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        self.data_text.insert(tk.END, formatted)
    
    def _copy_to_clipboard(self):
        """复制数据到剪贴板"""
        data = self.data_text.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(data)
        messagebox.showinfo("提示", "已复制到剪贴板")


def main():
    """主函数"""
    root = tk.Tk()
    app = StockDataTestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
