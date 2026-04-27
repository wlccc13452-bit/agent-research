"""
LLM智能评估报告测试脚本（分步测试版本）

测试目标：
1. 数据收集：K线、技术指标、指数、财务、新闻
2. 数据组织：JSON格式
3. LLM调用：智谱AI
4. 报告生成：Markdown格式
5. 文件保存
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta

# 设置UTF-8编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

print(f"项目根目录: {project_root}")
print(f"Python 路径: {sys.path[0]}")

# 导入必要的服务
try:
    from services.stock_service import StockService
    from services.fundamental_analyzer import FundamentalAnalyzer
    from services.llm_service import LLMService
    from services.news_aggregator import NewsAggregator
    from config.settings import settings
    print("[OK] 成功导入所有服务")
    
    # 调试：检查环境变量
    import os
    print(f"\n[DEBUG] 环境变量检查:")
    print(f"  ZHIPU_API_KEY: {'已设置' if os.getenv('ZHIPU_API_KEY') else '未设置'}")
    print(f"  ZHIPUAI_API_KEY: {'已设置' if os.getenv('ZHIPUAI_API_KEY') else '未设置'}")
    print(f"  settings.zhipu_api_key: {'已设置' if settings.zhipu_api_key else '未设置'}")
    
except ImportError as e:
    print(f"[ERROR] 导入服务失败: {e}")
    sys.exit(1)


class LLMReportTester:
    """LLM报告测试器"""
    
    def __init__(self):
        self.stock_service = StockService()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.llm_service = LLMService()
        self.news_aggregator = NewsAggregator()
        
    async def test_data_collection(self, stock_code: str, stock_name: str = "", days: int = 20) -> dict:
        """
        测试数据收集
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            days: 天数（默认20天）
            
        Returns:
            股票数据字典
        """
        print(f"\n[TEST] 测试数据收集 - 股票 {stock_code}")
        print("="*60)
        
        data = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "collection_time": datetime.now().isoformat(),
            "kline_data": [],
            "technical_indicators": {},
            "indices": {},
            "fundamental": {},
            "news": []
        }
        
        success_count = 0
        total_tests = 5
        
        try:
            # 1. 获取K线数据（最近20天）
            print(f"\n[1/{total_tests}] 获取K线数据（最近 {days} 天）...")
            try:
                klines = await self.stock_service.get_kline(stock_code, "day", days)
                if klines:
                    data["kline_data"] = [
                        {
                            "date": k.date,
                            "open": float(k.open) if k.open else None,
                            "close": float(k.close) if k.close else None,
                            "high": float(k.high) if k.high else None,
                            "low": float(k.low) if k.low else None,
                            "volume": float(k.volume) if k.volume else None,
                            "amount": float(k.amount) if k.amount else None
                        }
                        for k in klines
                    ]
                    print(f"     [OK] 成功获取 {len(data['kline_data'])} 条K线数据")
                    success_count += 1
                else:
                    print("     [WARN] 未获取到K线数据")
            except Exception as e:
                print(f"     [ERROR] 获取K线失败: {e}")
                
            # 2. 获取技术指标
            print(f"\n[2/{total_tests}] 获取技术指标...")
            try:
                indicators = await self.stock_service.get_technical_indicators(stock_code)
                if indicators:
                    data["technical_indicators"] = {
                        "ma5": float(indicators.ma5) if indicators.ma5 else None,
                        "ma10": float(indicators.ma10) if indicators.ma10 else None,
                        "ma20": float(indicators.ma20) if indicators.ma20 else None,
                        "ma30": float(indicators.ma30) if hasattr(indicators, 'ma30') and indicators.ma30 else None,
                        "ma60": float(indicators.ma60) if hasattr(indicators, 'ma60') and indicators.ma60 else None,
                        "ma120": float(indicators.ma120) if hasattr(indicators, 'ma120') and indicators.ma120 else None,
                        "ema20": float(indicators.ema20) if hasattr(indicators, 'ema20') and indicators.ema20 else None,
                        "ema60": float(indicators.ema60) if hasattr(indicators, 'ema60') and indicators.ema60 else None,
                        "ema120": float(indicators.ema120) if hasattr(indicators, 'ema120') and indicators.ema120 else None,
                        "macd": float(indicators.macd) if indicators.macd else None,
                        "macd_signal": float(indicators.macd_signal) if indicators.macd_signal else None,
                        "macd_hist": float(indicators.macd_hist) if indicators.macd_hist else None,
                        "rsi": float(indicators.rsi) if indicators.rsi else None,
                        "kdj_k": float(indicators.kdj_k) if indicators.kdj_k else None,
                        "kdj_d": float(indicators.kdj_d) if indicators.kdj_d else None,
                        "kdj_j": float(indicators.kdj_j) if indicators.kdj_j else None
                    }
                    print("     [OK] 成功获取技术指标")
                    print(f"         MA5: {data['technical_indicators']['ma5']}")
                    print(f"         MA10: {data['technical_indicators']['ma10']}")
                    print(f"         MA20: {data['technical_indicators']['ma20']}")
                    print(f"         MACD: {data['technical_indicators']['macd']}")
                    success_count += 1
                else:
                    print("     [WARN] 未获取到技术指标")
            except Exception as e:
                print(f"     [ERROR] 获取技术指标失败: {e}")
                
            # 3. 获取指数数据（上证指数、深证指数）
            print(f"\n[3/{total_tests}] 获取指数数据...")
            try:
                # 获取上证指数
                sh_index = await self.stock_service.get_quote("000001")
                # 获取深证指数
                sz_index = await self.stock_service.get_quote("399001")
                
                if sh_index:
                    data["indices"]["上证指数"] = {
                        "code": "000001",
                        "price": float(sh_index.price) if sh_index.price else None,
                        "change_pct": float(sh_index.change_pct) if sh_index.change_pct else None
                    }
                if sz_index:
                    data["indices"]["深证指数"] = {
                        "code": "399001", 
                        "price": float(sz_index.price) if sz_index.price else None,
                        "change_pct": float(sz_index.change_pct) if sz_index.change_pct else None
                    }
                
                if data["indices"]:
                    print("     [OK] 成功获取指数数据")
                    for name, idx in data["indices"].items():
                        print(f"         {name}: {idx['price']} ({idx['change_pct']}%)")
                    success_count += 1
                else:
                    print("     [WARN] 未获取到指数数据")
            except Exception as e:
                print(f"     [ERROR] 获取指数数据失败: {e}")
                
            # 4. 获取财务数据
            print(f"\n[4/{total_tests}] 获取财务数据...")
            try:
                fundamental = await self.fundamental_analyzer.analyze_fundamental(stock_code)
                if fundamental:
                    data["fundamental"] = fundamental
                    print("     [OK] 成功获取财务数据")
                    if fundamental.get('valuation'):
                        print(f"         PE: {fundamental['valuation'].get('pe_ttm')}")
                        print(f"         PB: {fundamental['valuation'].get('pb')}")
                    success_count += 1
                else:
                    print("     [WARN] 未获取到财务数据")
            except Exception as e:
                print(f"     [ERROR] 获取财务数据失败: {e}")
                
            # 5. 获取新闻数据
            print(f"\n[5/{total_tests}] 获取新闻数据...")
            try:
                news_list = await self.news_aggregator.get_stock_news(stock_code, stock_name, count=5)
                if news_list:
                    data["news"] = [
                        {
                            "title": n.get('title', ''),
                            "source": n.get('source', ''),
                            "date": n.get('date', ''),
                            "url": n.get('url', '')
                        }
                        for n in news_list
                    ]
                    print(f"     [OK] 成功获取 {len(data['news'])} 条新闻")
                    for i, news in enumerate(data['news'][:3], 1):
                        print(f"         {i}. {news['title'][:50]}...")
                    success_count += 1
                else:
                    print("     [WARN] 未获取到新闻数据")
            except Exception as e:
                print(f"     [ERROR] 获取新闻数据失败: {e}")
                
            # 输出测试结果
            print("\n" + "="*60)
            print(f"数据收集测试完成: {success_count}/{total_tests} 项成功")
            print("="*60)
            
            return data, success_count, total_tests
            
        except Exception as e:
            print(f"[ERROR] 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return data, success_count, total_tests
    
    async def test_llm_call(self, stock_data: dict, stock_name: str) -> dict:
        """
        测试LLM调用
        
        Args:
            stock_data: 股票数据
            stock_name: 股票名称
            
        Returns:
            测试结果
        """
        print(f"\n[TEST] 测试LLM调用")
        print("="*60)
        
        # 检查API Key配置
        if not self.llm_service.zhipu_api_key:
            print("[WARN] 智谱AI API Key未配置")
            print("       请在 backend/.env 文件中配置 ZHIPUAI_API_KEY")
            print("       或设置环境变量 ZHIPUAI_API_KEY")
            return {
                "success": False,
                "error": "API Key未配置"
            }
        
        print(f"[OK] 智谱AI API Key已配置")
        print(f"[INFO] 开始调用LLM...")
        
        try:
            # 构建提示词
            prompt = self.build_llm_prompt(stock_data, stock_name)
            
            # 调用LLM
            result = await self.llm_service._call_zhipuai(prompt)
            
            if result:
                print("[OK] LLM调用成功")
                
                # 解析JSON结果
                try:
                    # 提取JSON部分
                    start_idx = result.find('{')
                    end_idx = result.rfind('}')
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = result[start_idx:end_idx+1]
                        llm_result = json.loads(json_str)
                        
                        print("[OK] 成功解析LLM返回结果")
                        return {
                            "success": True,
                            "llm_result": llm_result
                        }
                    else:
                        print("[ERROR] 未找到有效的JSON结果")
                        return {
                            "success": False,
                            "error": "未找到有效的JSON结果",
                            "raw_response": result[:500]
                        }
                        
                except json.JSONDecodeError as e:
                    print(f"[ERROR] JSON解析失败: {e}")
                    return {
                        "success": False,
                        "error": f"JSON解析失败: {e}",
                        "raw_response": result[:500]
                    }
            else:
                print("[ERROR] LLM调用失败")
                return {
                    "success": False,
                    "error": "LLM调用失败"
                }
                
        except Exception as e:
            print(f"[ERROR] LLM测试失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def build_llm_prompt(self, stock_data: dict, stock_name: str) -> str:
        """构建LLM提示词"""
        # 将数据转换为JSON字符串，处理datetime对象
        def json_serial(obj):
            """JSON序列化辅助函数"""
            if isinstance(obj, (datetime,)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        data_json = json.dumps(stock_data, ensure_ascii=False, indent=2, default=json_serial)
        
        prompt = f"""# 股票智能评估任务

你是一位专业的股票分析师，请根据以下数据对股票进行全面评估。

## 股票信息
- 代码: {stock_data['stock_code']}
- 名称: {stock_name}
- 分析时间: {stock_data['collection_time']}

## 数据详情

```json
{data_json}
```

## 评估要求

请从以下几个维度进行评估，并以JSON格式返回结果：

### 1. 技术面分析
- 分析K线走势、成交量变化
- 分析技术指标（MA、EMA、MACD、RSI、KDJ）
- 判断当前趋势（上涨/下跌/震荡）

### 2. 基本面分析
- 分析财务数据（PE、PB、ROE等）
- 评估公司盈利能力、成长性

### 3. 市场环境分析
- 分析大盘指数走势
- 评估市场整体氛围

### 4. 消息面分析
- 分析相关新闻对股价的影响
- 评估消息面正负面

### 5. 买卖点评估
- 给出当前是否为买点或卖点
- 建议买入价格区间
- 建议卖出价格区间
- 设置止损止盈位

### 6. 风险评估
- 评估投资风险等级（低/中/高）
- 列出主要风险因素

## 返回格式

请严格按照以下JSON格式返回，不要添加任何其他文字：

```json
{{
  "stock_code": "{stock_data['stock_code']}",
  "stock_name": "{stock_name}",
  "analysis_date": "{stock_data['collection_time']}",
  "technical_analysis": {{
    "trend": "上涨/下跌/震荡",
    "trend_strength": "强/中/弱",
    "support_level": 支撑位价格,
    "resistance_level": 压力位价格,
    "volume_trend": "放量/缩量/平稳",
    "indicators_summary": "技术指标综合评价"
  }},
  "fundamental_analysis": {{
    "valuation": "高估/合理/低估",
    "profitability": "优秀/良好/一般/较差",
    "growth_potential": "高/中/低",
    "financial_health": "健康/一般/风险",
    "pe_ratio_analysis": "PE比率分析",
    "pb_ratio_analysis": "PB比率分析"
  }},
  "market_environment": {{
    "overall_trend": "牛市/熊市/震荡市",
    "market_sentiment": "乐观/中性/悲观",
    "index_analysis": "大盘指数分析"
  }},
  "news_analysis": {{
    "sentiment": "正面/中性/负面",
    "impact_level": "高/中/低",
    "key_news": ["关键新闻1", "关键新闻2"]
  }},
  "trading_suggestion": {{
    "action": "买入/卖出/持有/观望",
    "buy_price_range": [下限, 上限],
    "sell_price_range": [下限, 上限],
    "stop_loss_price": 止损价位,
    "take_profit_price": 止盈价位,
    "position_suggestion": "仓位建议（百分比）",
    "holding_period": "短期/中期/长期"
  }},
  "risk_assessment": {{
    "risk_level": "低/中/高",
    "risk_factors": ["风险因素1", "风险因素2"],
    "risk_warning": "风险提示"
  }},
  "overall_rating": "强烈推荐/推荐/中性/不推荐/强烈不推荐",
  "confidence_score": 置信度分数(0-100),
  "summary": "综合评估总结"
}}
```

请开始评估。
"""
        return prompt
    
    def format_markdown_report(self, llm_result: dict) -> str:
        """将LLM结果格式化为Markdown报告"""
        md = f"""# LLM智能评估报告

**股票代码**: {llm_result.get('stock_code', 'N/A')}  
**股票名称**: {llm_result.get('stock_name', 'N/A')}  
**分析日期**: {llm_result.get('analysis_date', 'N/A')}  
**综合评级**: {llm_result.get('overall_rating', 'N/A')}  
**置信度**: {llm_result.get('confidence_score', 'N/A')}%

---

## 技术面分析

**趋势判断**: {llm_result.get('technical_analysis', {}).get('trend', 'N/A')}  
**趋势强度**: {llm_result.get('technical_analysis', {}).get('trend_strength', 'N/A')}  
**支撑位**: {llm_result.get('technical_analysis', {}).get('support_level', 'N/A')}  
**压力位**: {llm_result.get('technical_analysis', {}).get('resistance_level', 'N/A')}  
**成交量趋势**: {llm_result.get('technical_analysis', {}).get('volume_trend', 'N/A')}

**技术指标总结**:
{llm_result.get('technical_analysis', {}).get('indicators_summary', 'N/A')}

---

## 基本面分析

**估值水平**: {llm_result.get('fundamental_analysis', {}).get('valuation', 'N/A')}  
**盈利能力**: {llm_result.get('fundamental_analysis', {}).get('profitability', 'N/A')}  
**成长潜力**: {llm_result.get('fundamental_analysis', {}).get('growth_potential', 'N/A')}  
**财务健康**: {llm_result.get('fundamental_analysis', {}).get('financial_health', 'N/A')}

**PE分析**: {llm_result.get('fundamental_analysis', {}).get('pe_ratio_analysis', 'N/A')}

**PB分析**: {llm_result.get('fundamental_analysis', {}).get('pb_ratio_analysis', 'N/A')}

---

## 市场环境分析

**整体趋势**: {llm_result.get('market_environment', {}).get('overall_trend', 'N/A')}  
**市场情绪**: {llm_result.get('market_environment', {}).get('market_sentiment', 'N/A')}

**指数分析**:
{llm_result.get('market_environment', {}).get('index_analysis', 'N/A')}

---

## 消息面分析

**情绪倾向**: {llm_result.get('news_analysis', {}).get('sentiment', 'N/A')}  
**影响程度**: {llm_result.get('news_analysis', {}).get('impact_level', 'N/A')}

**关键新闻**:
"""
        
        key_news = llm_result.get('news_analysis', {}).get('key_news', [])
        for i, news in enumerate(key_news, 1):
            md += f"\n{i}. {news}"
        
        md += f"""

---

## 交易建议

**操作建议**: **{llm_result.get('trading_suggestion', {}).get('action', 'N/A')}**

**买入价格区间**: {llm_result.get('trading_suggestion', {}).get('buy_price_range', 'N/A')}  
**卖出价格区间**: {llm_result.get('trading_suggestion', {}).get('sell_price_range', 'N/A')}  
**止损价位**: {llm_result.get('trading_suggestion', {}).get('stop_loss_price', 'N/A')}  
**止盈价位**: {llm_result.get('trading_suggestion', {}).get('take_profit_price', 'N/A')}  
**建议仓位**: {llm_result.get('trading_suggestion', {}).get('position_suggestion', 'N/A')}  
**持仓周期**: {llm_result.get('trading_suggestion', {}).get('holding_period', 'N/A')}

---

## 风险评估

**风险等级**: {llm_result.get('risk_assessment', {}).get('risk_level', 'N/A')}

**风险因素**:
"""
        
        risk_factors = llm_result.get('risk_assessment', {}).get('risk_factors', [])
        for i, factor in enumerate(risk_factors, 1):
            md += f"\n{i}. {factor}"
        
        md += f"""

**风险提示**: {llm_result.get('risk_assessment', {}).get('risk_warning', 'N/A')}

---

## 综合总结

{llm_result.get('summary', 'N/A')}

---

**免责声明**: 本报告由AI生成，仅供参考，不构成投资建议。投资有风险，决策需谨慎。
"""
        return md


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("LLM智能评估报告功能测试")
    print("="*60)
    
    # 创建测试器
    tester = LLMReportTester()
    
    # 测试股票：南山铝业（600219）
    stock_code = "600219"
    stock_name = "南山铝业"
    
    # 第一步：测试数据收集
    stock_data, success_count, total_tests = await tester.test_data_collection(stock_code, stock_name, days=20)
    
    # 如果数据收集成功，继续测试LLM调用
    if success_count >= 3:  # 至少成功3项数据收集
        print(f"\n[INFO] 数据收集基本成功，准备测试LLM调用...")
        
        # 保存收集的数据到文件（用于调试）
        data_file = Path(__file__).parent / "test_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(stock_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"[INFO] 数据已保存到: {data_file}")
        
        # 第二步：测试LLM调用
        llm_result = await tester.test_llm_call(stock_data, stock_name)
        
        if llm_result.get("success"):
            print("\n[SUCCESS] LLM测试成功！")
            
            # 第三步：生成并保存报告
            md_report = tester.format_markdown_report(llm_result['llm_result'])
            
            report_dir = Path(__file__).parent.parent.parent / "backend" / "data" / "llm_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stock_code}_{stock_name}_{date_str}.md"
            report_path = report_dir / filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(md_report)
            
            print(f"[INFO] 报告已保存: {report_path}")
            
            # 打印报告预览
            print("\n" + "="*60)
            print("报告预览（前500字符）:")
            print("="*60)
            print(md_report[:500])
        else:
            print("\n[FAILED] LLM测试失败！")
            print(f"错误: {llm_result.get('error')}")
            
            # 如果数据收集成功但LLM调用失败，给出提示
            print("\n[提示] 数据收集功能已验证，可以集成到项目中。")
            print("       请配置智谱AI API Key后重新测试LLM功能。")
    else:
        print(f"\n[FAILED] 数据收集测试失败（{success_count}/{total_tests}），请检查数据源配置。")


if __name__ == "__main__":
    asyncio.run(main())
