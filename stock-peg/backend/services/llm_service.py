"""LLM 服务

统一的 LLM 调用服务，支持智谱 AI、OpenAI 等
"""
import logging
import json
import os
import asyncio
import aiofiles
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._load_config()
        self._prompt_template_cache = None
    
    def _load_config(self):
        """加载配置"""
        # 从settings对象读取配置（优先级最高）
        from config.settings import settings
        
        # 支持多种方式读取配置：
        # 1. 从settings对象读取（推荐）
        # 2. 从环境变量读取（备用）
        self.zhipu_api_key = (
            settings.zhipu_api_key or 
            os.getenv('ZHIPUAI_API_KEY', '') or 
            os.getenv('ZHIPU_API_KEY', '')
        )
        self.openai_api_key = (
            settings.openai_api_key or
            os.getenv('OPENAI_API_KEY', '')
        )
        
        # 默认使用智谱 AI
        self.default_provider = settings.ai_default_provider or 'zhipuai'
        self.default_model = settings.ai_default_model or 'glm-4'
        
        # Prompt 模板路径
        self.prompt_template_path = Path(__file__).parent.parent / 'agent' / 'stock-pmr-v2.md'
    
    async def analyze_stock(self, stock_data: Dict, pmr_data: Dict,
                          provider: Optional[str] = None) -> Optional[Dict]:
        """
        使用 LLM 分析股票
        
        Args:
            stock_data: 股票数据（JSON 格式）
            pmr_data: PMR 数据（JSON 格式）
            provider: LLM 提供商 (zhipuai/openai)，默认使用智谱 AI
            
        Returns:
            LLM 分析结果（JSON 格式）
        """
        try:
            # 选择提供商
            provider = provider or self.default_provider
            
            logger.info(f"开始 LLM 分析: provider={provider}")
            
            # 读取 Prompt 模板 (带缓存)
            if self._prompt_template_cache is None:
                self._prompt_template_cache = await self._load_prompt_template()
            
            if not self._prompt_template_cache:
                logger.error("加载 Prompt 模板失败")
                return None
            
            # 构建 Prompt
            prompt = self._build_prompt(self._prompt_template_cache, stock_data, pmr_data)
            
            # 调用 LLM
            if provider == 'zhipuai':
                result = await self._call_zhipuai(prompt)
            elif provider == 'openai':
                result = await self._call_openai(prompt)
            else:
                logger.error(f"不支持的 LLM 提供商: {provider}")
                return None
            
            if not result:
                logger.error("LLM 调用失败")
                return None
            
            # 解析结果
            parsed_result = self._parse_result(result)
            
            logger.info("LLM 分析完成")
            return parsed_result
            
        except Exception as e:
            logger.error(f"LLM 分析失败: {str(e)}")
            return None
    
    async def _load_prompt_template(self) -> Optional[str]:
        """加载 Prompt 模板 (异步)"""
        try:
            async with aiofiles.open(self.prompt_template_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            logger.error(f"读取 Prompt 模板失败: {str(e)}")
            return None
    
    def _build_prompt(self, template: str, stock_data: Dict, pmr_data: Dict) -> str:
        """构建完整的 Prompt"""
        # 将数据转换为 JSON 字符串
        stock_json = json.dumps(stock_data, ensure_ascii=False, indent=2)
        pmr_json = json.dumps(pmr_data, ensure_ascii=False, indent=2)
        
        # 构建 Prompt
        prompt = f"""# PMR 分析指导文档

{template}

---

# 待分析股票数据

## 股票基本信息

```json
{stock_json}
```

## PMR 数据

```json
{pmr_json}
```

---

请根据以上数据，严格按照文档中"十二、LLM 分析输出要求"的 JSON 格式进行回复。
注意：
1. 必须严格按照 JSON 格式回复，不要添加任何其他文字
2. PMR 评级必须基于文档中的评级表
3. 操作建议需明确且可执行
4. 风险提示需具体
"""
        return prompt
    
    async def _call_zhipuai(self, prompt: str) -> Optional[str]:
        """调用智谱 AI"""
        try:
            # 检查 API Key
            if not self.zhipu_api_key:
                logger.error("智谱 AI API Key 未配置")
                return None
            
            # 动态导入智谱 AI SDK
            try:
                from zhipuai import ZhipuAI
            except ImportError:
                logger.error("未安装 zhipuai SDK，请运行: pip install zhipuai")
                return None
            
            # 初始化客户端
            client = ZhipuAI(api_key=self.zhipu_api_key)
            
            # 使用 asyncio.to_thread 包装同步调用
            def _call():
                return client.chat.completions.create(
                    model="glm-4",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    top_p=0.9,
                    max_tokens=2000
                )
            
            response = await asyncio.to_thread(_call)
            
            # 提取结果
            result = response.choices[0].message.content
            
            logger.info(f"智谱 AI 调用成功，token 使用: {response.usage.total_tokens}")
            return result
            
        except Exception as e:
            logger.error(f"调用智谱 AI 失败: {str(e)}")
            return None
    
    async def _call_openai(self, prompt: str) -> Optional[str]:
        """调用 OpenAI"""
        try:
            # 检查 API Key
            if not self.openai_api_key:
                logger.error("OpenAI API Key 未配置")
                return None
            
            # 动态导入 OpenAI SDK
            try:
                import openai
            except ImportError:
                logger.error("未安装 openai SDK，请运行: pip install openai")
                return None
            
            # 初始化客户端
            client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            
            # 调用 API
            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                top_p=0.9,
                max_tokens=2000
            )
            
            # 提取结果
            result = response.choices[0].message.content
            
            logger.info(f"OpenAI 调用成功，token 使用: {response.usage.total_tokens}")
            return result
            
        except Exception as e:
            logger.error(f"调用 OpenAI 失败: {str(e)}")
            return None
    
    def _parse_result(self, result: str) -> Optional[Dict]:
        """解析 LLM 返回的结果"""
        try:
            # 尝试提取 JSON 内容
            # LLM 可能在 JSON 前后添加文字，需要提取纯 JSON 部分
            
            # 方法1：查找第一个 { 和最后一个 }
            start_idx = result.find('{')
            end_idx = result.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = result[start_idx:end_idx+1]
                
                # 解析 JSON
                parsed = json.loads(json_str)
                
                # 验证必要字段
                required_fields = ['stock_code', 'market_environment', 'pmr_summary', 
                                 'overall_rating', 'analysis', 'operation_suggestion']
                
                for field in required_fields:
                    if field not in parsed:
                        logger.warning(f"LLM 回复缺少必要字段: {field}")
                
                return parsed
            else:
                logger.error("LLM 回复中未找到有效的 JSON")
                return None
            
        except json.JSONDecodeError as e:
            logger.error(f"解析 LLM 回复失败: {str(e)}")
            logger.debug(f"原始回复: {result}")
            return None
    
    async def generate_smart_analysis(self, stock_code: str, stock_name: str,
                                     report_date: str, stock_data: Dict,
                                     pmr_data: Dict) -> Optional[Dict]:
        """
        生成智能分析报告
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            report_date: 报告日期
            stock_data: 股票数据
            pmr_data: PMR 数据
            
        Returns:
            智能分析结果
        """
        try:
            # 构建输入数据
            input_data = {
                'stock_data': {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'report_date': report_date,
                    **stock_data
                },
                'pmr_data': pmr_data
            }
            
            # 调用 LLM
            result = await self.analyze_stock(
                stock_data=input_data['stock_data'],
                pmr_data=input_data['pmr_data']
            )
            
            if not result:
                return None
            
            # 添加元数据
            result['llm_provider'] = self.default_provider
            result['llm_model'] = self.default_model
            result['generated_at'] = report_date
            
            return result
            
        except Exception as e:
            logger.error(f"生成智能分析失败: {str(e)}")
            return None
