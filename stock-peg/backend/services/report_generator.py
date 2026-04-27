"""每日分析报告生成服务"""
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta, date
import json

from config.settings import settings
from database.session import async_session_maker
from database.operations import (
    get_daily_report,
    get_daily_reports,
    update_prediction_verification,
    save_daily_report,
)
from database.models import DailyReport
from services.stock_service import StockService
from services.fundamental_analyzer import FundamentalAnalyzer
from services.prediction_engine import PredictionEngine
from services.us_market_analyzer import USMarketAnalyzer
from services.pmr_calculator import PMRCalculator
from services.llm_service import LLMService
from services.debug_log_manager import debug_log_manager

logger = logging.getLogger(__name__)


class ReportGenerator:
    """每日分析报告生成器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ReportGenerator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.stock_service = StockService()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.prediction_engine = PredictionEngine()
        self.us_market_analyzer = USMarketAnalyzer()
        self.pmr_calculator = PMRCalculator()
        self.llm_service = LLMService()
        self._initialized = True
    
    async def generate_daily_report(self, stock_code: str, stock_name: str,
                                   sector: str, report_date: date,
                                   progress_callback=None) -> Optional[Dict]:
        """
        生成每日分析报告
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            sector: 所属板块
            report_date: 报告日期
            progress_callback: 进度回调函数 (stage: str, progress: int, message: str)
            
        Returns:
            报告数据
        """
        # 创建任务日志
        task_id = debug_log_manager.start_task(
            'report_generation',
            f'生成报告 {stock_code}',
            {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'sector': sector,
                'report_date': str(report_date)
            }
        )
        
        try:
            debug_log_manager.log_debug(task_id, '开始生成报告')
            
            # 辅助函数：发送进度
            async def send_progress(stage: str, progress: int, message: str):
                debug_log_manager.log_debug(task_id, message, {
                    'stage': stage,
                    'progress': progress
                })
                if progress_callback:
                    await progress_callback(stage, progress, message)
            
            # 1. 获取当日行情数据
            await send_progress('fetch_data', 10, '正在获取行情数据...')
            quote = await self.stock_service.get_quote(stock_code)
            klines = await self.stock_service.get_kline(stock_code, "day", 1)
            
            if not quote:
                debug_log_manager.log_warning(task_id, f'未获取到 {stock_code} 行情数据')
                debug_log_manager.end_task(task_id, success=False, error='未获取到行情数据')
                return None
            
            # 2. 获取技术指标
            await send_progress('technical', 20, '正在分析技术指标...')
            technical_indicators = await self.stock_service.get_technical_indicators(stock_code)
            
            # 3. 基本面分析
            await send_progress('fundamental', 35, '正在进行基本面分析...')
            fundamental_data = await self.fundamental_analyzer.analyze_fundamental(stock_code)
            
            # 4. 生成预测
            await send_progress('prediction', 50, '正在生成预测模型...')
            prediction = await self.prediction_engine.predict(stock_code, stock_name, sector)
            
            # 5. 资金面分析 (简化版,需要调用东财API)
            await send_progress('money', 60, '正在分析资金流向...')
            money_analysis = await self._analyze_money_flow(stock_code)
            
            # 6. 消息面分析 (简化版,需要调用新闻API)
            await send_progress('news', 70, '正在分析消息面...')
            news_analysis = await self._analyze_news(stock_code, stock_name)
            
            # 7. 国际面分析
            await send_progress('international', 75, '正在分析国际市场...')
            international_analysis = await self._analyze_international(stock_code, stock_name, sector)
            
            # 8. 综合评分
            technical_score = self._score_technical(technical_indicators)
            fundamental_score = fundamental_data.get('overall_score', 3.0) if fundamental_data else 3.0
            money_score = money_analysis.get('score', 3.0)
            news_score = news_analysis.get('score', 3.0)
            international_score = international_analysis.get('score', 3.0)
            
            overall_score = (technical_score + fundamental_score + money_score + 
                           news_score + international_score) / 5
            
            # 9. 生成操作建议
            action = self._generate_action(overall_score, prediction)
            
            # 10. 智能分析（PMR + LLM）
            await send_progress('smart_analysis', 85, '正在进行智能分析（LLM）...')
            smart_analysis_data = await self._generate_smart_analysis(
                stock_code, stock_name, report_date, quote, technical_indicators
            )
            
            # 11. 构建报告数据
            report_data = {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'report_date': report_date,
                'create_time': datetime.now(),
                
                # 行情回顾
                'open_price': quote.open,
                'close_price': quote.price,
                'high_price': quote.high,
                'low_price': quote.low,
                'change_pct': quote.change_pct,
                'change_amount': quote.change,
                'volume': quote.volume,
                'turnover_rate': quote.turnover_rate,
                
                # 技术面分析
                'ma5': technical_indicators.ma5 if technical_indicators else None,
                'ma10': technical_indicators.ma10 if technical_indicators else None,
                'ma20': technical_indicators.ma20 if technical_indicators else None,
                'macd': technical_indicators.macd if technical_indicators else None,
                'macd_signal': technical_indicators.macd_signal if technical_indicators else None,
                'macd_hist': technical_indicators.macd_hist if technical_indicators else None,
                'rsi': technical_indicators.rsi if technical_indicators else None,
                'kdj_k': technical_indicators.kdj_k if technical_indicators else None,
                'kdj_d': technical_indicators.kdj_d if technical_indicators else None,
                'kdj_j': technical_indicators.kdj_j if technical_indicators else None,
                'technical_score': technical_score,
                
                # 基本面分析
                'pe_ratio': fundamental_data.get('valuation', {}).get('pe_ttm') if fundamental_data else None,
                'pb_ratio': fundamental_data.get('valuation', {}).get('pb') if fundamental_data else None,
                'market_cap': fundamental_data.get('valuation', {}).get('market_cap') if fundamental_data else None,
                'north_money': None,  # 需要调用API
                'institution_money': None,  # 需要调用API
                'fundamental_score': fundamental_score,
                
                # 资金面分析
                'main_money': money_analysis.get('main_money'),
                'big_order_money': money_analysis.get('big_order_money'),
                'money_score': money_score,
                
                # 消息面分析
                'news_score': news_score,
                'news_summary': news_analysis.get('summary'),
                
                # 国际面分析
                'international_score': international_score,
                'international_summary': international_analysis.get('summary'),
                
                # 预测结果
                'predict_direction': prediction.prediction.direction if prediction else None,
                'predict_probability': prediction.prediction.probability if prediction else None,
                'target_price_low': prediction.prediction.target_price_range[0] if prediction else None,
                'target_price_high': prediction.prediction.target_price_range[1] if prediction else None,
                'risk_level': prediction.prediction.risk_level if prediction else None,
                'confidence': prediction.prediction.confidence if prediction else None,
                'key_factors': json.dumps(prediction.prediction.key_factors) if prediction else None,
                
                # 操作建议
                'action': action['action'],
                'position': action['position'],
                'stop_loss': action['stop_loss'],
                'take_profit': action['take_profit'],
                'action_summary': action['summary'],
                
                # 报告总结
                'overall_score': overall_score,
                'summary': self._generate_summary(overall_score, prediction),
                
                # 智能分析（新增）
                'smart_analysis': smart_analysis_data.get('smart_analysis') if smart_analysis_data else None,
                'smart_analysis_formatted': smart_analysis_data.get('formatted') if smart_analysis_data else None,
                'pmr_data': smart_analysis_data.get('pmr_data') if smart_analysis_data else None,
                'llm_model': smart_analysis_data.get('llm_model') if smart_analysis_data else None,
                'llm_provider': smart_analysis_data.get('llm_provider') if smart_analysis_data else None
            }
            
            # 11. 保存到数据库
            await send_progress('saving', 95, '正在保存报告...')
            await self._save_report(report_data)
            
            await send_progress('completed', 100, '报告生成完成！')
            logger.info(f"报告生成完成: {stock_code} {stock_name}")
            
            return report_data
            
        except Exception as e:
            logger.error(f"生成报告失败 {stock_code}: {str(e)}")
            return None
    
    async def generate_all_reports(self, holdings: Dict, report_date: date, max_concurrency: int = 5):
        """为所有持仓股票并行生成报告"""
        import asyncio
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def _generate_with_semaphore(stock_code, stock_name, sector):
            async with semaphore:
                try:
                    await self.generate_daily_report(
                        stock_code,
                        stock_name,
                        sector,
                        report_date
                    )
                except Exception as e:
                    logger.error(f"生成报告失败 {stock_code}: {str(e)}")

        tasks = []
        for sector_info in holdings.get('sectors', []):
            sector = sector_info['name']
            for stock in sector_info.get('stocks', []):
                tasks.append(_generate_with_semaphore(
                    stock['code'],
                    stock['name'],
                    sector
                ))
        
        if tasks:
            logger.info(f"正在并行生成 {len(tasks)} 份报告 (并发数: {max_concurrency})...")
            await asyncio.gather(*tasks)
            logger.info("所有报告生成任务已完成")
    
    async def get_report(self, stock_code: str, report_date: date):
        """获取报告"""
        try:
            async with async_session_maker() as session:
                return await get_daily_report(session, stock_code, report_date)
        except Exception as e:
            logger.error(f"获取报告失败: {str(e)}")
            return None
    
    async def get_reports_list(self, start_date: date, end_date: date,
                               stock_code: Optional[str] = None) -> List:
        """获取报告列表"""
        try:
            async with async_session_maker() as session:
                return await get_daily_reports(session, start_date, end_date, stock_code)
        except Exception as e:
            logger.error(f"获取报告列表失败: {str(e)}")
            return []
    
    async def verify_prediction(self, stock_code: str, report_date: date):
        """验证预测准确性"""
        try:
            # 获取报告
            report = await self.get_report(stock_code, report_date)
            if not report:
                return
            
            # 获取次日实际行情
            next_date = report_date + timedelta(days=1)
            # 这里需要跳过周末,简化处理
            actual_quote = await self.stock_service.get_quote(stock_code)
            
            if not actual_quote:
                return
            
            # 判断实际方向
            actual_change_pct = actual_quote.change_pct
            if actual_change_pct > 0.5:
                actual_direction = '上涨'
            elif actual_change_pct < -0.5:
                actual_direction = '下跌'
            else:
                actual_direction = '震荡'
            
            # 更新报告
            async with async_session_maker() as session:
                is_correct = 1 if report.predict_direction == actual_direction else 0
                await update_prediction_verification(
                    session,
                    stock_code,
                    report_date,
                    actual_direction,
                    actual_change_pct,
                    is_correct
                )
            
        except Exception as e:
            logger.error(f"验证预测失败: {str(e)}")
    
    async def _analyze_money_flow(self, stock_code: str) -> Dict:
        """分析资金流向 (简化版)"""
        # 实际应该调用东财API获取资金流向数据
        # 这里返回模拟数据
        import random
        
        return {
            'main_money': random.uniform(-10000, 10000),
            'big_order_money': random.uniform(-5000, 5000),
            'score': random.uniform(2.5, 4.5)
        }
    
    async def _analyze_news(self, stock_code: str, stock_name: str) -> Dict:
        """分析消息面 (简化版)"""
        # 实际应该调用新闻API获取相关新闻
        # 这里返回模拟数据
        return {
            'summary': f'{stock_name}近期无重大消息',
            'score': 3.0
        }
    
    async def _analyze_international(self, stock_code: str, stock_name: str,
                                    sector: str) -> Dict:
        """分析国际市场影响"""
        try:
            # 获取美股指数数据
            us_market = await self.us_market_analyzer.data_service.get_us_market_indices()
            
            # 分析影响
            sp500_change = us_market.get('标普500', {}).get('change_pct', 0)
            nasdaq_change = us_market.get('纳斯达克', {}).get('change_pct', 0)
            
            avg_change = (sp500_change + nasdaq_change) / 2
            
            if avg_change > 1:
                score = 4.0
                summary = f"美股市场上涨,对A股形成正面影响"
            elif avg_change < -1:
                score = 2.0
                summary = f"美股市场下跌,对A股形成负面影响"
            else:
                score = 3.0
                summary = f"美股市场震荡,对A股影响有限"
            
            return {
                'score': score,
                'summary': summary,
                'us_market': us_market
            }
            
        except Exception as e:
            logger.error(f"分析国际市场失败: {str(e)}")
            return {
                'score': 3.0,
                'summary': '国际市场数据获取失败'
            }
    
    def _score_technical(self, indicators) -> float:
        """技术面评分"""
        if not indicators:
            return 3.0
        
        score = 3.0
        
        # MA评分
        if indicators.ma5 and indicators.ma10 and indicators.ma20:
            if indicators.ma5 > indicators.ma10 > indicators.ma20:
                score += 0.5
            elif indicators.ma5 < indicators.ma10 < indicators.ma20:
                score -= 0.5
        
        # MACD评分
        if indicators.macd_hist and indicators.macd_hist > 0:
            score += 0.3
        elif indicators.macd_hist and indicators.macd_hist < 0:
            score -= 0.3
        
        # RSI评分
        if indicators.rsi:
            if indicators.rsi < 30:
                score += 0.2  # 超卖
            elif indicators.rsi > 70:
                score -= 0.2  # 超买
        
        return max(1.0, min(5.0, score))
    
    def _generate_action(self, overall_score: float, prediction) -> Dict:
        """生成操作建议"""
        if not prediction:
            return {
                'action': '观望',
                'position': 0,
                'stop_loss': None,
                'take_profit': None,
                'summary': '数据不足,建议观望'
            }
        
        pred = prediction.prediction
        
        if overall_score >= 4.0 and pred.direction == '上涨' and pred.probability > 0.6:
            action = '买入'
            position = 80
            summary = f"技术面和基本面均较好,预测{pred.direction}概率{pred.probability:.1%},建议买入"
        elif overall_score >= 3.5 and pred.direction == '上涨':
            action = '持有'
            position = 50
            summary = f"整体情况尚可,预测{pred.direction},建议持有"
        elif overall_score < 2.5 or (pred.direction == '下跌' and pred.probability > 0.6):
            action = '卖出'
            position = 0
            summary = f"风险较高,预测{pred.direction}概率{pred.probability:.1%},建议减仓或卖出"
        else:
            action = '观望'
            position = 30
            summary = f"趋势不明确,建议观望"
        
        # 计算止损止盈位
        current_price = prediction.prediction.target_price_range[0] if pred.direction == '上涨' else prediction.prediction.target_price_range[1]
        stop_loss = current_price * 0.95 if current_price else None
        take_profit = current_price * 1.10 if current_price else None
        
        return {
            'action': action,
            'position': position,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'summary': summary
        }
    
    def _generate_summary(self, overall_score: float, prediction) -> str:
        """生成报告总结"""
        if overall_score >= 4.0:
            rating = "优秀"
        elif overall_score >= 3.5:
            rating = "良好"
        elif overall_score >= 3.0:
            rating = "一般"
        elif overall_score >= 2.5:
            rating = "较差"
        else:
            rating = "很差"
        
        if prediction:
            pred = prediction.prediction
            summary = f"""
综合评分: {overall_score:.1f}/5.0 ({rating})
预测方向: {pred.direction}
预测概率: {pred.probability:.1%}
置信度: {pred.confidence}
风险等级: {pred.risk_level}

核心观点:
该股票技术面和基本面综合评分为{overall_score:.1f}分,属于{rating}水平。
预测明日{pred.direction}的概率为{pred.probability:.1%},置信度{pred.confidence}。
建议投资者根据自身风险承受能力做出决策。
"""
        else:
            summary = f"""
综合评分: {overall_score:.1f}/5.0 ({rating})

核心观点:
该股票综合评分为{overall_score:.1f}分,属于{rating}水平。
由于数据不足,无法生成预测结果,建议谨慎操作。
"""
        
        return summary
    
    async def _save_report(self, report_data: Dict):
        """保存报告到数据库"""
        try:
            async with async_session_maker() as session:
                await save_daily_report(session, report_data)
        except Exception as e:
            logger.error(f"保存报告失败: {str(e)}")
    
    async def _generate_smart_analysis(self, stock_code: str, stock_name: str,
                                       report_date: date, quote, technical_indicators) -> Optional[Dict]:
        """
        生成智能分析（PMR + LLM）
        
        Returns:
            {
                'smart_analysis': str,  # LLM 原始回复 JSON
                'formatted': str,       # 格式化后的分析
                'pmr_data': str,        # PMR 数据 JSON
                'llm_model': str,
                'llm_provider': str
            }
        """
        try:
            logger.info(f"开始生成智能分析: {stock_code}")
            
            # 1. 计算 PMR 数据
            pmr_data = await self.pmr_calculator.calculate_pmr(stock_code, report_date)
            
            if not pmr_data:
                logger.warning(f"PMR 计算失败: {stock_code}")
                return None
            
            # 2. 准备股票数据
            stock_data = {
                'market': {
                    'open': float(quote.open) if quote.open else None,
                    'close': float(quote.price) if quote.price else None,
                    'high': float(quote.high) if quote.high else None,
                    'low': float(quote.low) if quote.low else None,
                    'volume': float(quote.volume) if quote.volume else None,
                    'turnover_rate': float(quote.turnover_rate) if quote.turnover_rate else None,
                    'change_pct': float(quote.change_pct) if quote.change_pct else None
                },
                'technical': {
                    'ma5': float(technical_indicators.ma5) if technical_indicators and technical_indicators.ma5 else None,
                    'ma10': float(technical_indicators.ma10) if technical_indicators and technical_indicators.ma10 else None,
                    'ma20': float(technical_indicators.ma20) if technical_indicators and technical_indicators.ma20 else None,
                    'ma30': None,  # 需要额外计算
                    'ma60': None   # 需要额外计算
                }
            }
            
            # 3. 调用 LLM 生成分析
            llm_result = await self.llm_service.generate_smart_analysis(
                stock_code=stock_code,
                stock_name=stock_name,
                report_date=report_date.isoformat(),
                stock_data=stock_data,
                pmr_data=pmr_data
            )
            
            if not llm_result:
                logger.warning(f"LLM 分析失败: {stock_code}")
                # 仍然返回 PMR 数据
                return {
                    'smart_analysis': None,
                    'formatted': None,
                    'pmr_data': json.dumps(pmr_data, ensure_ascii=False),
                    'llm_model': None,
                    'llm_provider': None
                }
            
            # 4. 格式化 LLM 回复
            formatted = self._format_smart_analysis(llm_result)
            
            return {
                'smart_analysis': json.dumps(llm_result, ensure_ascii=False),
                'formatted': formatted,
                'pmr_data': json.dumps(pmr_data, ensure_ascii=False),
                'llm_model': llm_result.get('llm_model'),
                'llm_provider': llm_result.get('llm_provider')
            }
            
        except Exception as e:
            logger.error(f"生成智能分析失败: {str(e)}")
            return None
    
    def _format_smart_analysis(self, llm_result: Dict) -> str:
        """
        格式化 LLM 分析结果为 Markdown
        
        Args:
            llm_result: LLM 返回的 JSON 数据
            
        Returns:
            格式化后的 Markdown 文本
        """
        try:
            md = f"""# [BOT] 智能分析报告

## [CHART] PMR 综合评级

**整体评级**: {llm_result.get('overall_rating', 'N/A')}  
**综合评分**: {llm_result.get('overall_score', 'N/A')}/5.0

### 行情环境判断

**当前环境**: {llm_result.get('market_environment', 'N/A')}  
**判断依据**: {llm_result.get('environment_reason', 'N/A')}

---

## 📈 PMR 详细分析

"""
            
            # PMR 汇总表格
            pmr_summary = llm_result.get('pmr_summary', {})
            
            md += "| 周期 | PMR 值 | 评级 | 趋势判断 | 操作建议 |\n"
            md += "|------|--------|------|----------|----------|\n"
            
            for ma_period in ['MA5', 'MA10', 'MA20', 'MA30', 'MA60']:
                if ma_period in pmr_summary:
                    info = pmr_summary[ma_period]
                    md += f"| {ma_period} | {info.get('pmr', 0):.2f} | {info.get('rating', 'N/A')} | {info.get('trend', 'N/A')} | {info.get('suggestion', 'N/A')} |\n"
            
            md += "\n---\n\n"
            
            # 综合分析
            md += f"## 💡 综合分析\n\n{llm_result.get('analysis', 'N/A')}\n\n"
            
            # 操作建议
            md += f"## [TARGET] 操作建议\n\n{llm_result.get('operation_suggestion', 'N/A')}\n\n"
            
            # 风险提示
            md += f"## [WARN]️ 风险提示\n\n{llm_result.get('risk_warning', 'N/A')}\n\n"
            
            # 关键价位
            key_levels = llm_result.get('key_levels', {})
            if key_levels:
                md += "## 📍 关键价位\n\n"
                md += f"- **支撑位 1**: {key_levels.get('support_1', 'N/A')}\n"
                md += f"- **支撑位 2**: {key_levels.get('support_2', 'N/A')}\n"
                md += f"- **压力位 1**: {key_levels.get('resistance_1', 'N/A')}\n"
                md += f"- **压力位 2**: {key_levels.get('resistance_2', 'N/A')}\n"
                md += f"- **MA5**: {key_levels.get('ma5', 'N/A')}\n"
                md += f"- **MA20**: {key_levels.get('ma20', 'N/A')}\n"
                md += f"- **MA60**: {key_levels.get('ma60', 'N/A')}\n\n"
            
            # 未来 3 日预测
            forecast = llm_result.get('next_3days_forecast', {})
            if forecast:
                md += "## 🔮 未来 3 日预测\n\n"
                for day_key in ['day1', 'day2', 'day3']:
                    if day_key in forecast:
                        day_info = forecast[day_key]
                        day_num = int(day_key[-1])
                        md += f"**第 {day_num} 日**: {day_info.get('direction', 'N/A')} (概率: {day_info.get('probability', 0):.0%})\n"
                        md += f"- 理由: {day_info.get('reason', 'N/A')}\n\n"
            
            return md
            
        except Exception as e:
            logger.error(f"格式化智能分析失败: {str(e)}")
            return "格式化失败"
    
    async def export_report_to_markdown(self, report: DailyReport) -> str:
        """导出报告为Markdown格式"""
        md = f"""# {report.stock_name}({report.stock_code}) - {report.report_date} 分析报告

生成时间: {report.create_time}

## 一、行情回顾

- 开盘价: {report.open_price}
- 收盘价: {report.close_price}
- 最高价: {report.high_price}
- 最低价: {report.low_price}
- 涨跌幅: {report.change_pct:.2f}%
- 涨跌额: {report.change_amount}
- 成交量: {report.volume}
- 换手率: {report.turnover_rate:.2f}%

## 二、技术面分析

**评分**: {report.technical_score}/5.0

### 均线系统
- MA5: {report.ma5}
- MA10: {report.ma10}
- MA20: {report.ma20}

### 技术指标
- MACD: {report.macd}
- MACD信号线: {report.macd_signal}
- MACD柱: {report.macd_hist}
- RSI: {report.rsi}
- KDJ-K: {report.kdj_k}
- KDJ-D: {report.kdj_d}
- KDJ-J: {report.kdj_j}

## 三、基本面分析

**评分**: {report.fundamental_score}/5.0

- 市盈率(PE): {report.pe_ratio}
- 市净率(PB): {report.pb_ratio}
- 市值: {report.market_cap}万元

## 四、资金面分析

**评分**: {report.money_score}/5.0

- 主力资金净流入: {report.main_money}万元
- 大单净买卖: {report.big_order_money}万元

## 五、消息面分析

**评分**: {report.news_score}/5.0

{report.news_summary}

## 六、国际面分析

**评分**: {report.international_score}/5.0

{report.international_summary}

## 七、明日预测

- 预测方向: {report.predict_direction}
- 预测概率: {report.predict_probability:.1%}
- 目标价区间: {report.target_price_low} - {report.target_price_high}
- 风险等级: {report.risk_level}
- 置信度: {report.confidence}

## 八、操作建议

- 操作建议: **{report.action}**
- 建议仓位: {report.position}%
- 止损位: {report.stop_loss}
- 止盈位: {report.take_profit}

{report.action_summary}

## 九、报告总结

{report.summary}

---

**免责声明**: 本报告仅供参考,不构成投资建议。投资者据此操作,风险自担。
"""
        return md
