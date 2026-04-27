"""AI分析服务"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import time

from config.settings import settings
from models.prediction import PredictionResult, ComprehensivePrediction
from services.log_service import log_service

logger = logging.getLogger(__name__)

class AIService:
    """AI分析服务，支持多种AI模型"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.provider = settings.ai_default_provider
        self.model = settings.ai_default_model
        
        # 初始化不同平台的SDK
        self._init_zhipu()
        self._init_openai()
        self._init_anthropic()
        
        self._initialized = True
    
    def _init_zhipu(self):
        """初始化智谱AI"""
        if settings.zhipu_api_key:
            try:
                from zhipuai import ZhipuAI
                self.zhipu_client = ZhipuAI(api_key=settings.zhipu_api_key)
                logger.info("智谱AI已初始化")
            except ImportError:
                logger.error("未安装 zhipuai 库，请运行: pip install zhipuai")
                self.zhipu_client = None
        else:
            self.zhipu_client = None
    
    def _init_openai(self):
        """初始化OpenAI"""
        if settings.openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI已初始化")
            except ImportError:
                self.openai_client = None
        else:
            self.openai_client = None

    def _init_anthropic(self):
        """初始化Anthropic (Claude)"""
        if settings.anthropic_api_key:
            try:
                from anthropic import Anthropic
                self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
                logger.info("Anthropic已初始化")
            except ImportError:
                self.anthropic_client = None
        else:
            self.anthropic_client = None

    async def analyze(self, prompt: str) -> Optional[str]:
        """通用的AI分析接口"""
        if self.provider == "zhipu" and self.zhipu_client:
            return await self._call_zhipu(prompt)
        elif self.provider == "openai" and self.openai_client:
            return await self._call_openai(prompt)
        elif self.provider == "anthropic" and self.anthropic_client:
            return await self._call_anthropic(prompt)
        else:
            logger.error(f"未配置或不支持的AI提供商: {self.provider}")
            return None
    
    async def analyze_stock(self, stock_info: Dict[str, Any]) -> Optional[str]:
        """使用AI分析股票"""
        prompt = self._build_stock_prompt(stock_info)
        return await self.analyze(prompt)

    def _build_stock_prompt(self, stock_info: Dict[str, Any]) -> str:
        """构建股票分析Prompt"""
        return f"""
        请作为一名资深的股票分析师，分析以下股票数据并给出预测：
        股票代码: {stock_info.get('code')}
        股票名称: {stock_info.get('name')}
        当前价格: {stock_info.get('price')}
        涨跌幅: {stock_info.get('change_pct')}%
        成交额: {stock_info.get('amount')}
        
        技术指标:
        MA5: {stock_info.get('ma5')}
        MA10: {stock_info.get('ma10')}
        MACD: {stock_info.get('macd')}
        RSI: {stock_info.get('rsi')}
        
        请分析其走势并给出以下格式的JSON预测结果：
        {{
            "direction": "上涨/下跌/震荡",
            "probability": 0.0-1.0,
            "target_price_range": [最低, 最高],
            "confidence": "低/中/高",
            "risk_level": "低/中/高",
            "key_factors": [{{ "factor": "权重" }}]
        }}
        """

    async def _call_zhipu(self, prompt: str) -> Optional[str]:
        """调用智谱AI接口"""
        if not self.zhipu_client:
            return None
        
        start_time = time.time()
        error = None
        response_text = None
        
        import asyncio
        try:
            # 智谱SDK目前主要是同步调用，使用 asyncio.to_thread 包装
            def _call():
                return self.zhipu_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    top_p=0.9
                )
            
            response = await asyncio.to_thread(_call)
            response_text = response.choices[0].message.content
            return response_text
        except Exception as e:
            error = str(e)
            logger.error(f"智谱AI调用失败: {str(e)}")
            return None
        finally:
            # 记录LLM调用日志
            duration_ms = (time.time() - start_time) * 1000
            log_service.log_llm_call(
                provider="zhipu",
                model=self.model,
                prompt=prompt,
                response=response_text,
                error=error,
                duration_ms=duration_ms
            )

    async def _call_openai(self, prompt: str) -> Optional[str]:
        """调用OpenAI接口"""
        if not self.openai_client:
            return None
        
        start_time = time.time()
        error = None
        response_text = None
        
        import asyncio
        try:
            def _call():
                return self.openai_client.chat.completions.create(
                    model=self.model or "gpt-4",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
            
            response = await asyncio.to_thread(_call)
            response_text = response.choices[0].message.content
            return response_text
        except Exception as e:
            error = str(e)
            logger.error(f"OpenAI调用失败: {str(e)}")
            return None
        finally:
            # 记录LLM调用日志
            duration_ms = (time.time() - start_time) * 1000
            log_service.log_llm_call(
                provider="openai",
                model=self.model or "gpt-4",
                prompt=prompt,
                response=response_text,
                error=error,
                duration_ms=duration_ms
            )

    async def _call_anthropic(self, prompt: str) -> Optional[str]:
        """调用Anthropic接口"""
        if not self.anthropic_client:
            return None
        
        start_time = time.time()
        error = None
        response_text = None
        
        import asyncio
        try:
            def _call():
                return self.anthropic_client.messages.create(
                    model=self.model or "claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
            
            response = await asyncio.to_thread(_call)
            response_text = response.content[0].text
            return response_text
        except Exception as e:
            error = str(e)
            logger.error(f"Anthropic调用失败: {str(e)}")
            return None
        finally:
            # 记录LLM调用日志
            duration_ms = (time.time() - start_time) * 1000
            log_service.log_llm_call(
                provider="anthropic",
                model=self.model or "claude-3-opus-20240229",
                prompt=prompt,
                response=response_text,
                error=error,
                duration_ms=duration_ms
            )
