"""
Markdown股票资料加载器

优先从本地Markdown文件读取股票资料，支持手动维护和自动更新。
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


class MarkdownProfileLoader:
    """股票资料Markdown文件加载器"""
    
    def __init__(self, profile_dir: str = None):
        """
        初始化加载器
        
        Args:
            profile_dir: 资料文件目录路径，默认为 backend/data/stock_profiles
        """
        if profile_dir is None:
            # 默认目录
            backend_dir = Path(__file__).parent.parent
            profile_dir = backend_dir / "data" / "stock_profiles"
        
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"MarkdownProfileLoader initialized with dir: {self.profile_dir}")
    
    def get_profile_path(self, stock_code: str) -> Path:
        """获取股票资料文件路径"""
        return self.profile_dir / f"{stock_code}.md"
    
    def exists(self, stock_code: str) -> bool:
        """检查股票资料文件是否存在"""
        return self.get_profile_path(stock_code).exists()
    
    async def async_exists(self, stock_code: str) -> bool:
        """异步检查股票资料文件是否存在"""
        return await asyncio.to_thread(self.exists, stock_code)
    
    def parse_markdown(self, content: str, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        解析Markdown内容为结构化数据
        
        Args:
            content: Markdown文本内容
            stock_code: 股票代码
            
        Returns:
            解析后的字典数据
        """
        try:
            result = {
                "stock_code": stock_code,
                "source": "markdown",
                "raw_content": content
            }
            
            # 提取报告类型
            report_type_match = re.search(r'\*\*报告类型\*\*:\s*(年报|季报)', content)
            if report_type_match:
                result['report_type'] = report_type_match.group(1)
            
            # 提取报告期
            report_date_match = re.search(r'\*\*报告期\*\*:\s*(\d{4}-\d{2}-\d{2})', content)
            if report_date_match:
                result['report_date'] = report_date_match.group(1)
            
            # 提取公告日期
            ann_date_match = re.search(r'\*\*公告日期\*\*:\s*(\d{4}-\d{2}-\d{2})', content)
            if ann_date_match:
                result['ann_date'] = ann_date_match.group(1)
            
            # 提取财务数据
            revenue_match = re.search(r'营业收入:\s*([\d.]+)亿元', content)
            if revenue_match:
                result['revenue'] = float(revenue_match.group(1)) * 100000000  # 亿元转为元
            
            net_profit_match = re.search(r'净利润:\s*([\d.]+)亿元', content)
            if net_profit_match:
                result['net_profit'] = float(net_profit_match.group(1)) * 100000000
            
            eps_match = re.search(r'基本每股收益:\s*([\d.]+)元', content)
            if eps_match:
                result['basic_eps'] = float(eps_match.group(1))
            
            cashflow_match = re.search(r'经营现金流:\s*([\d.]+)亿元', content)
            if cashflow_match:
                result['operating_cashflow'] = float(cashflow_match.group(1)) * 100000000
            
            # 提取更新时间
            update_time_match = re.search(r'\*最后更新:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\*', content)
            if update_time_match:
                result['last_updated'] = update_time_match.group(1)
            
            # 提取数据来源
            source_match = re.search(r'\*数据来源:\s*([^*]+)\*', content)
            if source_match:
                result['data_source'] = source_match.group(1).strip()
            
            # 提取股票名称（从一级标题）
            title_match = re.search(r'^#\s+(.+?)\s+\(' + stock_code + r'\)', content, re.MULTILINE)
            if title_match:
                result['stock_name'] = title_match.group(1)
            
            logger.info(f"Parsed markdown profile for {stock_code}: {list(result.keys())}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing markdown for {stock_code}: {e}", exc_info=True)
            return None
    
    def load(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        从Markdown文件加载股票资料
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票资料字典，文件不存在返回None
        """
        try:
            profile_path = self.get_profile_path(stock_code)
            
            if not profile_path.exists():
                logger.info(f"Profile file not found for {stock_code}: {profile_path}")
                return None
            
            with open(profile_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Loaded markdown profile for {stock_code} from {profile_path}")
            return self.parse_markdown(content, stock_code)
            
        except Exception as e:
            logger.error(f"Error loading markdown profile for {stock_code}: {e}", exc_info=True)
            return None

    async def async_load(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        异步从Markdown文件加载股票资料
        """
        return await asyncio.to_thread(self.load, stock_code)
    
    def generate_markdown(self, data: Dict[str, Any], stock_name: str = "") -> str:
        """
        从结构化数据生成Markdown内容
        
        Args:
            data: 结构化数据字典
            stock_name: 股票名称
            
        Returns:
            Markdown格式文本
        """
        # 获取股票名称
        if not stock_name:
            stock_name = data.get('stock_name', f"股票{data['stock_code']}")
        
        # 报告类型
        report_type = data.get('report_type', '年报')
        
        # 格式化财务数据（元转亿元）
        revenue = data.get('revenue')
        revenue_str = f"{revenue / 100000000:.2f}亿元" if revenue else "未披露"
        
        net_profit = data.get('net_profit')
        net_profit_str = f"{net_profit / 100000000:.2f}亿元" if net_profit else "未披露"
        
        basic_eps = data.get('basic_eps')
        basic_eps_str = f"{basic_eps:.2f}元" if basic_eps else "未披露"
        
        operating_cashflow = data.get('operating_cashflow')
        cashflow_str = f"{operating_cashflow / 100000000:.2f}亿元" if operating_cashflow else "未披露"
        
        # 更新时间
        update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        markdown = f"""# {stock_name} ({data['stock_code']})

## 最新年报或季报

**报告类型**: {report_type}
**报告期**: {data.get('report_date', '未披露')}
**公告日期**: {data.get('ann_date', '未披露')}

### 财务摘要
- 营业收入: {revenue_str}
- 净利润: {net_profit_str}
- 基本每股收益: {basic_eps_str}
- 经营现金流: {cashflow_str}

### 经营分析
（暂无详细分析，请手动补充）

## 公司概况

### 基本信息
- 上市日期: （请补充）
- 所属行业: （请补充）
- 主营业务: （请补充）

### 业务亮点
（请手动补充）

## 投资要点

### 优势
（请手动补充）

### 机会
（请手动补充）

## 风险提示

1. （请手动补充）

---
*最后更新: {update_time}*
*数据来源: 自动生成*
"""
        
        return markdown
    
    def save(self, stock_code: str, data: Dict[str, Any], stock_name: str = "") -> bool:
        """
        保存股票资料到Markdown文件
        
        Args:
            stock_code: 股票代码
            data: 结构化数据字典
            stock_name: 股票名称
            
        Returns:
            是否保存成功
        """
        try:
            profile_path = self.get_profile_path(stock_code)
            
            # 如果文件已存在，读取原内容（保留手动维护的部分）
            if profile_path.exists():
                with open(profile_path, 'r', encoding='utf-8') as f:
                    old_content = f.read()
                
                # 更新财务数据部分
                # 这里可以添加更智能的合并逻辑
                # 目前简单覆盖
            
            markdown = self.generate_markdown(data, stock_name)
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            logger.info(f"Saved markdown profile for {stock_code} to {profile_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving markdown profile for {stock_code}: {e}", exc_info=True)
            return False

    async def async_save(self, stock_code: str, data: Dict[str, Any], stock_name: str = "") -> bool:
        """
        异步保存股票资料到Markdown文件
        """
        return await asyncio.to_thread(self.save, stock_code, data, stock_name)
    
    def update_from_api(self, stock_code: str, api_data: Dict[str, Any], stock_name: str = "") -> bool:
        """
        从API数据更新Markdown文件
        
        Args:
            stock_code: 股票代码
            api_data: API返回的数据
            stock_name: 股票名称
            
        Returns:
            是否更新成功
        """
        # 检查文件是否已存在
        profile_path = self.get_profile_path(stock_code)
        
        if profile_path.exists():
            # 读取现有内容
            existing_data = self.load(stock_code)
            
            # 检查是否需要更新（比较报告日期）
            if existing_data and existing_data.get('report_date'):
                existing_date = existing_data['report_date']
                new_date = api_data.get('report_date', '')
                
                if existing_date >= new_date:
                    logger.info(f"Profile {stock_code} is up to date (existing: {existing_date}, new: {new_date})")
                    return False
        
        # 保存/更新文件
        return self.save(stock_code, api_data, stock_name)

    async def async_update_from_api(self, stock_code: str, api_data: Dict[str, Any], stock_name: str = "") -> bool:
        """
        异步从API数据更新Markdown文件
        """
        # 检查文件是否已存在
        profile_path = self.get_profile_path(stock_code)
        
        if await self.async_exists(stock_code):
            # 读取现有内容
            existing_data = await self.async_load(stock_code)
            
            # 检查是否需要更新（比较报告日期）
            if existing_data and existing_data.get('report_date'):
                existing_date = existing_data['report_date']
                new_date = api_data.get('report_date', '')
                
                if existing_date >= new_date:
                    logger.info(f"Profile {stock_code} is up to date (existing: {existing_date}, new: {new_date})")
                    return False
        
        # 保存/更新文件
        return await self.async_save(stock_code, api_data, stock_name)

    
    def list_profiles(self) -> list:
        """列出所有已有的股票资料文件"""
        profiles = []
        for file_path in self.profile_dir.glob("*.md"):
            if file_path.name != "README.md":
                stock_code = file_path.stem
                profiles.append({
                    "stock_code": stock_code,
                    "file_path": str(file_path),
                    "exists": True
                })
        return profiles


# 全局单例实例
_loader_instance = None


def get_profile_loader() -> MarkdownProfileLoader:
    """获取全局MarkdownProfileLoader实例"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = MarkdownProfileLoader()
    return _loader_instance
