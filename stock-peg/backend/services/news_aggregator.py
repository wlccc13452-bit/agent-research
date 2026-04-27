"""新闻聚合服务"""
import logging
import httpx
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import time

from config.settings import settings
from services.log_service import log_service

logger = logging.getLogger(__name__)


class NewsAggregator:
    """新闻聚合器"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.sina_api = "https://feed.mix.sina.com.cn/api/roll/get"
        self.eastmoney_api = "https://searchapi.eastmoney.com/bussiness/web/QuotationLabelSearch"
    
    async def get_stock_news(self, stock_code: str, stock_name: str, count: int = 20) -> List[Dict]:
        """
        获取股票相关新闻
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            count: 新闻数量
        
        Returns:
            新闻列表
        """
        try:
            # 从多个数据源获取新闻
            sina_news = await self._get_sina_news(stock_name, count // 2)
            eastmoney_news = await self._get_eastmoney_news(stock_code, stock_name, count // 2)
            
            # 合并并排序
            all_news = sina_news + eastmoney_news
            all_news.sort(key=lambda x: x['publish_time'], reverse=True)
            
            return all_news[:count]
            
        except Exception as e:
            logger.error(f"获取股票新闻失败 {stock_code}: {str(e)}")
            return []
    
    async def _log_and_request(self, api_name: str, url: str, params: Optional[Dict] = None):
        """记录并执行HTTP请求"""
        start_time = time.time()
        error = None
        response_status = None
        response_data = None
        
        try:
            response = await self.client.get(url, params=params)
            response_status = response.status_code
            response.raise_for_status()
            response_data = response.text
            return response
        except Exception as e:
            error = str(e)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            log_service.log_external_api_call(
                api_name=api_name,
                url=url,
                method="GET",
                request_params=params,
                response_status=response_status,
                response_data=response_data[:500] if response_data else None,
                error=error,
                duration_ms=duration_ms
            )
    
    async def _get_sina_news(self, stock_name: str, count: int) -> List[Dict]:
        """从新浪财经获取新闻"""
        try:
            # 新浪财经新闻搜索API
            params = {
                'pageid': '153',
                'lid': '2516',
                'k': stock_name,
                'num': count,
                'page': 1,
                'r': str(datetime.now().timestamp())
            }
            
            response = await self._log_and_request("sina_news", self.sina_api, params)
            
            data = response.json()
            
            news_list = []
            if data.get('result', {}).get('data'):
                for item in data['result']['data']:
                    try:
                        news_item = {
                            'title': item.get('title', ''),
                            'summary': item.get('intro', '') or item.get('title', ''),
                            'url': item.get('url', ''),
                            'source': '新浪财经',
                            'publish_time': datetime.fromtimestamp(int(item.get('ctime', 0))),
                            'category': item.get('channel', {}).get('cname', '财经')
                        }
                        news_list.append(news_item)
                    except Exception as e:
                        logger.error(f"解析新浪新闻失败: {str(e)}")
                        continue
            
            logger.info(f"从新浪财经获取到 {len(news_list)} 条新闻")
            return news_list
            
        except Exception as e:
            logger.error(f"获取新浪新闻失败: {str(e)}")
            return []
    
    async def _get_eastmoney_news(self, stock_code: str, stock_name: str, count: int) -> List[Dict]:
        """从东方财富获取新闻"""
        try:
            # 东方财富新闻搜索API
            params = {
                'keyword': stock_name,
                'type': 'news',
                'pi': 1,
                'ps': count,
                'client': 'web'
            }
            
            response = await self._log_and_request("eastmoney_news", self.eastmoney_api, params)
            
            data = response.json()
            
            news_list = []
            if data.get('Data'):
                for item in data['Data']:
                    try:
                        # 解析时间
                        time_str = item.get('ShowTime', '')
                        try:
                            publish_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                        except:
                            publish_time = datetime.now()
                        
                        news_item = {
                            'title': item.get('Title', ''),
                            'summary': item.get('Digest', '') or item.get('Title', ''),
                            'url': item.get('Url', ''),
                            'source': '东方财富',
                            'publish_time': publish_time,
                            'category': item.get('ChannelName', '财经')
                        }
                        news_list.append(news_item)
                    except Exception as e:
                        logger.error(f"解析东方财富新闻失败: {str(e)}")
                        continue
            
            logger.info(f"从东方财富获取到 {len(news_list)} 条新闻")
            return news_list
            
        except Exception as e:
            logger.error(f"获取东方财富新闻失败: {str(e)}")
            return []
    
    async def get_sector_news(self, sector_name: str, count: int = 20) -> List[Dict]:
        """
        获取板块相关新闻
        
        Args:
            sector_name: 板块名称
            count: 新闻数量
        
        Returns:
            新闻列表
        """
        try:
            # 使用板块名称搜索新闻
            news = await self._get_sina_news(sector_name, count)
            return news
            
        except Exception as e:
            logger.error(f"获取板块新闻失败 {sector_name}: {str(e)}")
            return []
    
    async def analyze_news_sentiment(self, news_list: List[Dict]) -> Dict:
        """
        分析新闻情感
        
        Args:
            news_list: 新闻列表
        
        Returns:
            情感分析结果
        """
        try:
            # 简化的情感分析（基于关键词）
            positive_keywords = [
                '上涨', '增长', '盈利', '利好', '突破', '创新高', '增持',
                '业绩', '盈利', '增长', '大涨', '利好', '反弹', '走强'
            ]
            
            negative_keywords = [
                '下跌', '亏损', '利空', '减持', '暴跌', '跌停', '风险',
                '下滑', '下降', '亏损', '利空', '暴跌', '大跌', '走弱'
            ]
            
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for news in news_list:
                title = news.get('title', '')
                summary = news.get('summary', '')
                text = f"{title} {summary}"
                
                positive_score = sum(1 for keyword in positive_keywords if keyword in text)
                negative_score = sum(1 for keyword in negative_keywords if keyword in text)
                
                if positive_score > negative_score:
                    positive_count += 1
                elif negative_score > positive_score:
                    negative_count += 1
                else:
                    neutral_count += 1
            
            total = len(news_list) if news_list else 1
            
            sentiment = {
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'positive_ratio': positive_count / total,
                'negative_ratio': negative_count / total,
                'sentiment_score': (positive_count - negative_count) / total,
                'sentiment': 'positive' if positive_count > negative_count else 
                            'negative' if negative_count > positive_count else 'neutral'
            }
            
            return sentiment
            
        except Exception as e:
            logger.error(f"分析新闻情感失败: {str(e)}")
            return {
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'positive_ratio': 0,
                'negative_ratio': 0,
                'sentiment_score': 0,
                'sentiment': 'neutral'
            }
    
    async def get_hot_news(self, count: int = 20) -> List[Dict]:
        """
        获取热门财经新闻
        
        Args:
            count: 新闻数量
        
        Returns:
            新闻列表
        """
        try:
            # 获取热门财经新闻
            params = {
                'pageid': '153',
                'lid': '2516',
                'num': count,
                'page': 1,
                'r': str(datetime.now().timestamp())
            }
            
            response = await self._log_and_request("sina_hot_news", self.sina_api, params)
            
            data = response.json()
            
            news_list = []
            if data.get('result', {}).get('data'):
                for item in data['result']['data']:
                    try:
                        news_item = {
                            'title': item.get('title', ''),
                            'summary': item.get('intro', '') or item.get('title', ''),
                            'url': item.get('url', ''),
                            'source': '新浪财经',
                            'publish_time': datetime.fromtimestamp(int(item.get('ctime', 0))),
                            'category': item.get('channel', {}).get('cname', '财经')
                        }
                        news_list.append(news_item)
                    except Exception as e:
                        logger.error(f"解析热门新闻失败: {str(e)}")
                        continue
            
            return news_list
            
        except Exception as e:
            logger.error(f"获取热门新闻失败: {str(e)}")
            return []
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 全局新闻聚合器实例
news_aggregator = NewsAggregator()
