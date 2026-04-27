"""每日分析报告路由"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from datetime import date, timedelta
from typing import List, Optional
import logging
import json

from services.report_generator import ReportGenerator
from services.llm_report_service import LLMReportService
from routers.holding import holding_manager  # 使用全局单例
from services.websocket_manager import manager as ws_manager
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# 创建报告生成器
report_generator = ReportGenerator()
# 使用全局单例（已在导入时定义）
# holding_manager 来自 routers.holding
llm_report_service = LLMReportService()


class GenerateReportRequest(BaseModel):
    """生成报告请求"""
    stock_code: str
    stock_name: str
    sector: str
    report_date: date


@router.get("/list")
async def get_reports_list(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    stock_code: Optional[str] = Query(None, description="股票代码")
):
    """获取报告列表"""
    try:
        # 默认查询最近7天
        if not start_date:
            start_date = date.today() - timedelta(days=7)
        if not end_date:
            end_date = date.today()
        
        reports = await report_generator.get_reports_list(start_date, end_date, stock_code)
        
        # 转换为字典列表
        reports_list = []
        for report in reports:
            reports_list.append({
                'id': report.id,
                'stock_code': report.stock_code,
                'stock_name': report.stock_name,
                'report_date': report.report_date.isoformat(),
                'overall_score': report.overall_score,
                'predict_direction': report.predict_direction,
                'predict_probability': report.predict_probability,
                'action': report.action
            })
        
        return {
            'reports': reports_list,
            'count': len(reports_list)
        }
        
    except Exception as e:
        logger.error(f"获取报告列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{stock_code}/{report_date}")
async def get_report_detail(stock_code: str, report_date: date):
    """获取报告详情"""
    try:
        report = await report_generator.get_report(stock_code, report_date)
        
        if not report:
            raise HTTPException(status_code=404, detail=f"未找到报告 {stock_code} {report_date}")
        
        # 转换为字典
        report_dict = {
            'id': report.id,
            'stock_code': report.stock_code,
            'stock_name': report.stock_name,
            'report_date': report.report_date.isoformat(),
            'create_time': report.create_time.isoformat(),
            
            # 行情回顾
            'market': {
                'open': float(report.open_price) if report.open_price else None,
                'close': float(report.close_price) if report.close_price else None,
                'high': float(report.high_price) if report.high_price else None,
                'low': float(report.low_price) if report.low_price else None,
                'change_pct': float(report.change_pct) if report.change_pct else None,
                'volume': report.volume,
                'turnover_rate': float(report.turnover_rate) if report.turnover_rate else None
            },
            
            # 技术面
            'technical': {
                'ma5': float(report.ma5) if report.ma5 else None,
                'ma10': float(report.ma10) if report.ma10 else None,
                'ma20': float(report.ma20) if report.ma20 else None,
                'macd': float(report.macd) if report.macd else None,
                'macd_signal': float(report.macd_signal) if report.macd_signal else None,
                'macd_hist': float(report.macd_hist) if report.macd_hist else None,
                'rsi': float(report.rsi) if report.rsi else None,
                'kdj_k': float(report.kdj_k) if report.kdj_k else None,
                'kdj_d': float(report.kdj_d) if report.kdj_d else None,
                'kdj_j': float(report.kdj_j) if report.kdj_j else None,
                'score': report.technical_score
            },
            
            # 基本面
            'fundamental': {
                'pe_ratio': float(report.pe_ratio) if report.pe_ratio else None,
                'pb_ratio': float(report.pb_ratio) if report.pb_ratio else None,
                'market_cap': float(report.market_cap) if report.market_cap else None,
                'score': report.fundamental_score
            },
            
            # 资金面
            'money': {
                'main_money': float(report.main_money) if report.main_money else None,
                'big_order_money': float(report.big_order_money) if report.big_order_money else None,
                'score': report.money_score
            },
            
            # 消息面
            'news': {
                'score': report.news_score,
                'summary': report.news_summary
            },
            
            # 国际面
            'international': {
                'score': report.international_score,
                'summary': report.international_summary
            },
            
            # 预测结果
            'prediction': {
                'direction': report.predict_direction,
                'probability': float(report.predict_probability) if report.predict_probability else None,
                'target_price_low': float(report.target_price_low) if report.target_price_low else None,
                'target_price_high': float(report.target_price_high) if report.target_price_high else None,
                'risk_level': report.risk_level,
                'confidence': report.confidence,
                'key_factors': report.key_factors
            },
            
            # 操作建议
            'action': {
                'action': report.action,
                'position': float(report.position) if report.position else None,
                'stop_loss': float(report.stop_loss) if report.stop_loss else None,
                'take_profit': float(report.take_profit) if report.take_profit else None,
                'summary': report.action_summary
            },
            
            # 总结
            'summary': {
                'overall_score': report.overall_score,
                'summary': report.summary
            },
            
            # 验证
            'verification': {
                'actual_direction': report.actual_direction,
                'actual_change_pct': float(report.actual_change_pct) if report.actual_change_pct else None,
                'is_correct': report.is_correct
            },
            
            # 智能分析（新增）
            'smart_analysis': {
                'raw': json.loads(report.smart_analysis) if report.smart_analysis else None,
                'formatted': report.smart_analysis_formatted,
                'pmr_data': json.loads(report.pmr_data) if report.pmr_data else None,
                'llm_model': report.llm_model,
                'llm_provider': report.llm_provider
            }
        }
        
        return report_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_report(request: GenerateReportRequest, background_tasks: BackgroundTasks):
    """生成单只股票报告"""
    try:
        # 定义进度回调函数
        async def progress_callback(stage: str, progress: int, message: str):
            """通过WebSocket推送进度"""
            await ws_manager.broadcast({
                'type': 'report_progress',
                'stock_code': request.stock_code,
                'stage': stage,
                'progress': progress,
                'message': message,
                'timestamp': date.today().isoformat()
            })
            logger.info(f"报告生成进度 [{request.stock_code}]: {progress}% - {message}")
        
        async def run_generation():
            try:
                report = await report_generator.generate_daily_report(
                    request.stock_code,
                    request.stock_name,
                    request.sector,
                    request.report_date,
                    progress_callback=progress_callback
                )
                
                if report:
                    # 推送报告完成通知
                    await ws_manager.broadcast({
                        'type': 'report_completed',
                        'stock_code': request.stock_code,
                        'stock_name': request.stock_name,
                        'report_date': request.report_date.isoformat(),
                        'overall_score': report.get('overall_score'),
                        'predict_direction': report.get('predict_direction'),
                        'summary': report.get('smart_analysis_formatted'),
                        'timestamp': date.today().isoformat()
                    })
                else:
                    logger.error(f"报告生成失败: {request.stock_code}")
                    await ws_manager.broadcast({
                        'type': 'report_error',
                        'stock_code': request.stock_code,
                        'error': "报告生成失败",
                        'timestamp': date.today().isoformat()
                    })
            except Exception as e:
                logger.error(f"后台生成报告出错: {str(e)}")
                await ws_manager.broadcast({
                    'type': 'report_error',
                    'stock_code': request.stock_code,
                    'error': str(e),
                    'timestamp': date.today().isoformat()
                })

        # 将任务添加到后台
        background_tasks.add_task(run_generation)
        
        return {
            "message": "报告生成任务已启动",
            "stock_code": request.stock_code,
            "report_date": request.report_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"生成报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-all")
async def generate_all_reports(background_tasks: BackgroundTasks):
    """生成所有持仓股票报告"""
    try:
        holdings = await holding_manager.load_holdings()
        report_date = date.today()
        
        # 使用 BackgroundTasks 异步执行，避免 HTTP 超时
        background_tasks.add_task(
            report_generator.generate_all_reports, 
            holdings.dict(), 
            report_date
        )
        
        return {"message": f"报告生成任务已在后台启动，日期: {report_date}"}
        
    except Exception as e:
        logger.error(f"批量生成报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{stock_code}/{report_date}")
async def export_report(stock_code: str, report_date: date):
    """导出报告为Markdown"""
    try:
        report = await report_generator.get_report(stock_code, report_date)
        
        if not report:
            raise HTTPException(status_code=404, detail=f"未找到报告 {stock_code} {report_date}")
        
        markdown = await report_generator.export_report_to_markdown(report)
        
        return {
            "markdown": markdown,
            "filename": f"{stock_code}_{report_date}.md"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify/{stock_code}/{report_date}")
async def verify_prediction(stock_code: str, report_date: date):
    """验证预测准确性"""
    try:
        await report_generator.verify_prediction(stock_code, report_date)
        return {"message": "预测验证完成"}
    except Exception as e:
        logger.error(f"验证预测失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LLM智能评估报告API ====================

class GenerateLLMReportRequest(BaseModel):
    """生成LLM报告请求"""
    stock_code: str
    stock_name: str
    days: int = 20  # 分析天数


@router.post("/llm/generate")
async def generate_llm_report(request: GenerateLLMReportRequest, background_tasks: BackgroundTasks):
    """
    生成LLM智能评估报告
    
    包括：
    - 20天K线数据
    - 技术指标分析（MA/EMA/MACD等）
    - 指数数据分析
    - 财务数据分析
    - 新闻数据分析
    - LLM智能评估
    - Markdown报告生成
    """
    try:
        # 定义进度回调函数
        async def progress_callback(stage: str, progress: int, message: str):
            """通过WebSocket推送进度"""
            await ws_manager.broadcast({
                'type': 'llm_report_progress',
                'stock_code': request.stock_code,
                'stage': stage,
                'progress': progress,
                'message': message,
                'timestamp': date.today().isoformat()
            })
            logger.info(f"LLM报告生成进度 [{request.stock_code}]: {progress}% - {message}")
        
        async def run_generation():
            try:
                # 发送开始通知
                await progress_callback('init', 0, '开始生成LLM智能评估报告...')
                
                # 生成报告
                result = await llm_report_service.generate_llm_report(
                    stock_code=request.stock_code,
                    stock_name=request.stock_name,
                    days=request.days
                )
                
                if result.get('success'):
                    # 推送报告完成通知
                    await ws_manager.broadcast({
                        'type': 'llm_report_completed',
                        'stock_code': request.stock_code,
                        'stock_name': request.stock_name,
                        'report_path': result.get('report_path'),
                        'markdown': result.get('markdown'),
                        'timestamp': date.today().isoformat()
                    })
                    
                    await progress_callback('completed', 100, 'LLM智能评估报告生成完成！')
                else:
                    logger.error(f"LLM报告生成失败: {request.stock_code}")
                    await ws_manager.broadcast({
                        'type': 'llm_report_error',
                        'stock_code': request.stock_code,
                        'error': result.get('error', '生成失败'),
                        'timestamp': date.today().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"后台生成LLM报告出错: {str(e)}")
                await ws_manager.broadcast({
                    'type': 'llm_report_error',
                    'stock_code': request.stock_code,
                    'error': str(e),
                    'timestamp': date.today().isoformat()
                })

        # 将任务添加到后台
        background_tasks.add_task(run_generation)
        
        return {
            "message": "LLM智能评估报告生成任务已启动",
            "stock_code": request.stock_code,
            "stock_name": request.stock_name
        }
        
    except Exception as e:
        logger.error(f"生成LLM报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm/list")
async def get_llm_report_list(
    stock_code: Optional[str] = Query(None, description="股票代码（可选）")
):
    """获取LLM智能评估报告列表"""
    try:
        reports = await llm_report_service.get_report_list(stock_code)
        
        return {
            'reports': reports,
            'count': len(reports)
        }
        
    except Exception as e:
        logger.error(f"获取LLM报告列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm/content/{file_name}")
async def get_llm_report_content(file_name: str):
    """获取LLM智能评估报告内容"""
    try:
        content = await llm_report_service.get_report_content(file_name)
        
        if not content:
            raise HTTPException(status_code=404, detail=f"未找到报告: {file_name}")
        
        return {
            "file_name": file_name,
            "content": content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取LLM报告内容失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

