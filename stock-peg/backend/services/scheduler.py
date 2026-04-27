"""定时任务调度服务"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Optional

from routers.holding import holding_manager  # 使用全局单例
from services.report_generator import ReportGenerator
from services.us_market_analyzer import USMarketAnalyzer
from services.prediction_engine import PredictionEngine
from config.settings import settings

logger = logging.getLogger(__name__)


def _resolve_trade_date(sentiment: dict) -> Optional[date]:
    trade_date_value = sentiment.get("trade_date")
    if isinstance(trade_date_value, date):
        return trade_date_value
    if isinstance(trade_date_value, str):
        text = trade_date_value.strip()
        for fmt in ("%Y%m%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
    return None


def _is_complete_sentiment(sentiment: Optional[dict]) -> bool:
    if not sentiment:
        return False
    total_count = int(sentiment.get("total_count") or 0)
    if total_count < 5000:
        return False
    if sentiment.get("data_quality") != "full":
        return False
    up_count = int(sentiment.get("up_count") or 0)
    down_count = int(sentiment.get("down_count") or 0)
    flat_count = int(sentiment.get("flat_count") or 0)
    if up_count <= 0 and down_count <= 0 and flat_count <= 0:
        return False
    return (up_count + down_count + flat_count) >= int(total_count * 0.95)


class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        # 配置调度器默认值
        # misfire_grace_time: 任务错过时间后多长时间内仍可执行 (3600秒 = 1小时)
        # coalesce: 多个错过的任务是否合并为一个执行
        job_defaults = {
            'misfire_grace_time': 3600,
            'coalesce': True,
            'max_instances': 1
        }
        self.scheduler = AsyncIOScheduler(job_defaults=job_defaults)
        # 使用全局单例
        # self.holding_manager = holding_manager  # 已经在导入时使用
        self.report_generator = ReportGenerator()
        self.us_market_analyzer = USMarketAnalyzer()
        self.prediction_engine = PredictionEngine()
        self.is_running = False
    
    def start(self):
        """启动定时任务"""
        if self.is_running:
            logger.warning("定时任务已在运行中")
            return
        
        try:
            # 1. 每日15:30生成分析报告（交易日）
            self.scheduler.add_job(
                self.generate_daily_reports,
                CronTrigger(hour=15, minute=30, day_of_week='mon-fri'),
                id='generate_daily_reports',
                name='生成每日分析报告',
                replace_existing=True
            )
            
            # 2. 每日9:30验证预测准确性（交易日）
            self.scheduler.add_job(
                self.verify_predictions,
                CronTrigger(hour=9, minute=30, day_of_week='mon-fri'),
                id='verify_predictions',
                name='验证预测准确性',
                replace_existing=True
            )
            
            # 3. 每日5:00生成美股市场报告（美股收盘后）
            self.scheduler.add_job(
                self.generate_us_market_report,
                CronTrigger(hour=5, minute=0, day_of_week='tue-sat'),  # 美股周一至周五交易，北京时间周二至周六
                id='generate_us_market_report',
                name='生成美股市场报告',
                replace_existing=True
            )
            
            # 4. 每周日重训练模型
            self.scheduler.add_job(
                self.retrain_model,
                CronTrigger(hour=2, minute=0, day_of_week='sun'),
                id='retrain_model',
                name='重新训练预测模型',
                replace_existing=True
            )
            
            # 5. 每小时更新预测结果（每小时整点执行）
            self.scheduler.add_job(
                self.update_predictions,
                CronTrigger(hour='*', minute=0, second=0),  # 明确指定整点执行
                id='update_predictions',
                name='更新预测结果',
                replace_existing=True
            )
            
            # 6. 每小时检查并补齐缺失数据 (Proactive Discovery)
            from services.background_updater import background_updater
            self.scheduler.add_job(
                background_updater.scan_and_update_missing_data,
                CronTrigger(hour='*', minute=30), # 每小时30分执行
                id='scan_and_update_missing_data',
                name='扫描并补齐缺失数据',
                replace_existing=True
            )
            
            # 7. 市场情绪数据定时更新（启动后立即执行一次）
            self.scheduler.add_job(
                self.update_market_sentiment,
                CronTrigger(hour='*', minute='*/5', day_of_week='mon-fri'),  # 交易时间每5分钟
                id='update_market_sentiment_trading',
                name='更新市场情绪数据（交易时间）',
                replace_existing=True
            )
            
            # 8. 非交易时间每60分钟检查一次
            self.scheduler.add_job(
                self.update_market_sentiment,
                CronTrigger(hour='*', minute=0),  # 每小时整点
                id='update_market_sentiment_non_trading',
                name='更新市场情绪数据（非交易时间）',
                replace_existing=True
            )
            
            # 9. 价格提醒监控（A股交易时段每分钟检查）
            # 从配置文件读取交易时段
            morning_start = settings.morning_session_start.split(':')
            morning_end = settings.morning_session_end.split(':')
            afternoon_start = settings.afternoon_session_start.split(':')
            afternoon_end = settings.afternoon_session_end.split(':')
            
            morning_start_hour = int(morning_start[0])
            morning_start_minute = int(morning_start[1])
            morning_end_hour = int(morning_end[0])
            morning_end_minute = int(morning_end[1])
            
            afternoon_start_hour = int(afternoon_start[0])
            afternoon_start_minute = int(afternoon_start[1])
            afternoon_end_hour = int(afternoon_end[0])
            afternoon_end_minute = int(afternoon_end[1])
            
            # 构建交易日配置（周几）
            trading_days = ','.join([str(d) for d in settings.trading_days_list])
            
            # 上午盘: 配置的开始时间-结束时间
            # 如果开始时间分钟不为0，需要分两个job
            if morning_start_minute != 0:
                # 第一个job：开始时间的整点到结束时间前一小时
                if morning_start_hour < morning_end_hour - 1:
                    self.scheduler.add_job(
                        self.check_price_alerts,
                        CronTrigger(
                            hour=f'{morning_start_hour+1}-{morning_end_hour-1}',
                            minute='*',
                            day_of_week=trading_days
                        ),
                        id='check_price_alerts_morning_middle',
                        name='检查价格提醒（上午盘中段）',
                        replace_existing=True
                    )
                
                # 第二个job：开始时间所在的小时
                self.scheduler.add_job(
                    self.check_price_alerts,
                    CronTrigger(
                        hour=str(morning_start_hour),
                        minute=f'{morning_start_minute}-59',
                        day_of_week=trading_days
                    ),
                    id='check_price_alerts_morning_start',
                    name='检查价格提醒（上午盘开始）',
                    replace_existing=True
                )
                
                # 第三个job：结束时间所在的小时
                self.scheduler.add_job(
                    self.check_price_alerts,
                    CronTrigger(
                        hour=str(morning_end_hour),
                        minute=f'0-{morning_end_minute}',
                        day_of_week=trading_days
                    ),
                    id='check_price_alerts_morning_end',
                    name='检查价格提醒（上午盘结束）',
                    replace_existing=True
                )
            else:
                # 简化情况：开始时间为整点
                # 如果结束时间分钟不为0，需要分两个job
                if morning_end_minute != 0:
                    # 第一个job：开始时间整点到结束时间前一小时
                    if morning_start_hour < morning_end_hour:
                        self.scheduler.add_job(
                            self.check_price_alerts,
                            CronTrigger(
                                hour=f'{morning_start_hour}-{morning_end_hour-1}',
                                minute='*',
                                day_of_week=trading_days
                            ),
                            id='check_price_alerts_morning_1',
                            name='检查价格提醒（上午盘前半段）',
                            replace_existing=True
                        )
                    
                    # 第二个job：结束时间所在的小时
                    self.scheduler.add_job(
                        self.check_price_alerts,
                        CronTrigger(
                            hour=str(morning_end_hour),
                            minute=f'0-{morning_end_minute}',
                            day_of_week=trading_days
                        ),
                        id='check_price_alerts_morning_2',
                        name='检查价格提醒（上午盘后半段）',
                        replace_existing=True
                    )
                else:
                    # 最简单情况：开始和结束都是整点
                    self.scheduler.add_job(
                        self.check_price_alerts,
                        CronTrigger(
                            hour=f'{morning_start_hour}-{morning_end_hour}',
                            minute='*',
                            day_of_week=trading_days
                        ),
                        id='check_price_alerts_morning',
                        name='检查价格提醒（上午盘）',
                        replace_existing=True
                    )
            
            # 下午盘: 配置的开始时间-结束时间
            # 使用同样的逻辑处理下午盘
            if afternoon_start_minute != 0:
                # 下午盘开始时间不在整点
                if afternoon_start_hour < afternoon_end_hour - 1:
                    self.scheduler.add_job(
                        self.check_price_alerts,
                        CronTrigger(
                            hour=f'{afternoon_start_hour+1}-{afternoon_end_hour-1}',
                            minute='*',
                            day_of_week=trading_days
                        ),
                        id='check_price_alerts_afternoon_middle',
                        name='检查价格提醒（下午盘中段）',
                        replace_existing=True
                    )
                
                self.scheduler.add_job(
                    self.check_price_alerts,
                    CronTrigger(
                        hour=str(afternoon_start_hour),
                        minute=f'{afternoon_start_minute}-59',
                        day_of_week=trading_days
                    ),
                    id='check_price_alerts_afternoon_start',
                    name='检查价格提醒（下午盘开始）',
                    replace_existing=True
                )
                
                self.scheduler.add_job(
                    self.check_price_alerts,
                    CronTrigger(
                        hour=str(afternoon_end_hour),
                        minute=f'0-{afternoon_end_minute}',
                        day_of_week=trading_days
                    ),
                    id='check_price_alerts_afternoon_end',
                    name='检查价格提醒（下午盘结束）',
                    replace_existing=True
                )
            else:
                # 下午盘开始时间在整点
                if afternoon_end_minute != 0:
                    if afternoon_start_hour < afternoon_end_hour:
                        self.scheduler.add_job(
                            self.check_price_alerts,
                            CronTrigger(
                                hour=f'{afternoon_start_hour}-{afternoon_end_hour-1}',
                                minute='*',
                                day_of_week=trading_days
                            ),
                            id='check_price_alerts_afternoon_1',
                            name='检查价格提醒（下午盘前半段）',
                            replace_existing=True
                        )
                    
                    self.scheduler.add_job(
                        self.check_price_alerts,
                        CronTrigger(
                            hour=str(afternoon_end_hour),
                            minute=f'0-{afternoon_end_minute}',
                            day_of_week=trading_days
                        ),
                        id='check_price_alerts_afternoon_2',
                        name='检查价格提醒（下午盘后半段）',
                        replace_existing=True
                    )
                else:
                    self.scheduler.add_job(
                        self.check_price_alerts,
                        CronTrigger(
                            hour=f'{afternoon_start_hour}-{afternoon_end_hour}',
                            minute='*',
                            day_of_week=trading_days
                        ),
                        id='check_price_alerts_afternoon',
                        name='检查价格提醒（下午盘）',
                        replace_existing=True
                    )
            
            # 10. 每周一凌晨3:00检查不活跃数据源
            self.scheduler.add_job(
                self.check_inactive_datasources,
                CronTrigger(hour=3, minute=0, day_of_week='mon'),
                id='check_inactive_datasources',
                name='检查不活跃数据源',
                replace_existing=True
            )

            # 启动调度器
            self.scheduler.start()
            self.is_running = True
            
            logger.info("定时任务调度器已启动")
            logger.info("已注册的任务:")
            for job in self.scheduler.get_jobs():
                logger.info(f"  - {job.name} (ID: {job.id})")
            
            # 启动后立即更新一次市场情绪数据
            logger.info("启动时立即更新市场情绪数据...")
            asyncio.create_task(self.update_market_sentiment())
            
        except Exception as e:
            logger.error(f"启动定时任务失败: {str(e)}")
            raise
    
    def stop(self):
        """停止定时任务"""
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("定时任务调度器已停止")
        except Exception as e:
            logger.error(f"停止定时任务失败: {str(e)}")
    
    async def generate_daily_reports(self):
        """生成每日分析报告"""
        try:
            logger.info("=" * 50)
            logger.info("开始生成每日分析报告")
            start_time = datetime.now()
            
            # 加载持仓数据（使用全局单例）
            holdings = await holding_manager.load_holdings()
            
            # 生成所有持仓股票的报告
            today = date.today()
            await self.report_generator.generate_all_reports(
                holdings.dict(),
                today
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"每日分析报告生成完成，耗时 {elapsed:.2f} 秒")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"生成每日分析报告失败: {str(e)}", exc_info=True)
    
    async def verify_predictions(self):
        """验证预测准确性"""
        try:
            logger.info("=" * 50)
            logger.info("开始验证预测准确性")
            
            # 获取昨天的日期（跳过周末）
            today = date.today()
            if today.weekday() == 0:  # 周一
                yesterday = today - timedelta(days=3)
            elif today.weekday() == 6:  # 周日
                yesterday = today - timedelta(days=2)
            else:
                yesterday = today - timedelta(days=1)
            
            # 加载持仓数据（使用全局单例）
            holdings = await holding_manager.load_holdings()
            
            # 验证每个股票的预测
            for sector in holdings.sectors:
                for stock in sector.stocks:
                    await self.report_generator.verify_prediction(
                        stock.code,
                        yesterday
                    )
            
            logger.info("预测准确性验证完成")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"验证预测准确性失败: {str(e)}", exc_info=True)
    
    async def generate_us_market_report(self):
        """生成美股市场报告"""
        try:
            logger.info("=" * 50)
            logger.info("开始生成美股市场报告")
            start_time = datetime.now()
            
            # 加载持仓数据（使用全局单例）
            holdings = await holding_manager.load_holdings()
            
            # 生成美股市场报告
            report = await self.us_market_analyzer.generate_daily_us_report(
                holdings.dict()
            )
            
            # 保存报告到文件
            report_date = datetime.now().strftime('%Y%m%d')
            report_path = settings.data_dir / f"us_market_report_{report_date}.md"
            
            import aiofiles
            async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
                await f.write(report)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"美股市场报告生成完成，耗时 {elapsed:.2f} 秒")
            logger.info(f"报告已保存至: {report_path}")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"生成美股市场报告失败: {str(e)}", exc_info=True)
    
    async def retrain_model(self):
        """重新训练预测模型"""
        try:
            logger.info("=" * 50)
            logger.info("开始重新训练预测模型")
            start_time = datetime.now()
            
            # TODO: 实现模型训练逻辑
            # 1. 从数据库加载历史数据
            # 2. 特征工程
            # 3. 训练LightGBM模型
            # 4. 评估模型性能
            # 5. 保存模型
            
            logger.warning("模型训练功能尚未实现，跳过")
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"模型训练完成，耗时 {elapsed:.2f} 秒")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"模型训练失败: {str(e)}", exc_info=True)
    
    async def update_predictions(self):
        """更新预测结果"""
        try:
            logger.info("开始更新预测结果")
            
            # 加载持仓数据（使用全局单例）
            holdings = await holding_manager.load_holdings()
            
            # 为每个股票生成预测
            predictions = await self.prediction_engine.predict_all_holdings(
                holdings.dict()
            )
            
            logger.info(f"已更新 {len(predictions)} 只股票的预测结果")
        except asyncio.CancelledError:
            logger.info("更新预测结果任务已取消（应用正在关闭）")
            return
            
        except Exception as e:
            logger.error(f"更新预测结果失败: {str(e)}")
    
    async def update_market_sentiment(self):
        """更新市场情绪数据到缓存
        
        逻辑：
        1. 获取市场情绪数据（含 trade_date）
        2. 如果 trade_date 已有完整数据，跳过（避免非交易日反复覆盖）
        3. 否则保存/更新到缓存
        """
        try:
            logger.info("=" * 50)
            logger.info("开始更新市场情绪数据")
            start_time = datetime.now()
            
            # 导入服务
            from datasource import get_datasource, DataSourceType
            from services.market_sentiment_cache_service import market_sentiment_cache_service
            from services.quote_data_service import quote_data_service
            from database.session import get_db
            from database.operations.market_sentiment_ops import get_latest_sentiment
            
            # 获取市场情绪数据
            akshare_source = get_datasource().get_source(DataSourceType.AKSHARE)
            sentiment = await akshare_source.get_market_sentiment() if akshare_source else None
            
            if _is_complete_sentiment(sentiment):
                trade_date = _resolve_trade_date(sentiment)
                
                # 检查是否已有该交易日的完整数据，避免非交易日反复覆盖
                async for db in get_db():
                    existing = await get_latest_sentiment(db)
                    if (existing and 
                        existing.get('trade_date') == trade_date and
                        existing.get('total_count', 0) >= 5000):
                        logger.info(
                            f"[SKIP] {trade_date} 已有完整数据 "
                            f"(total={existing['total_count']}, "
                            f"up={existing['up_count']}, down={existing['down_count']}), "
                            f"跳过更新"
                        )
                        break
                    
                    # 获取上证指数数据
                    try:
                        sh_klines = await akshare_source.get_index_kline("000001", "day", 2) if akshare_source else None
                        if sh_klines and len(sh_klines) > 0:
                            latest_kline = sh_klines[-1]
                            sentiment['sh_index_close'] = latest_kline.get('close')
                            if len(sh_klines) > 1:
                                prev_close = sh_klines[-2].get('close')
                                curr_close = latest_kline.get('close')
                                if prev_close and curr_close:
                                    sentiment['sh_index_change_pct'] = round(
                                        (curr_close - prev_close) / prev_close * 100, 2
                                    )
                    except Exception as e:
                        logger.warning(f"获取上证指数数据失败: {str(e)}")
                    
                    # 保存到缓存
                    success = await market_sentiment_cache_service.save_sentiment(
                        db,
                        sentiment,
                        trade_date
                    )
                    if success:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        logger.info(
                            f"[OK] 市场情绪数据已更新: {trade_date}, "
                            f"{sentiment['total_count']} 只股票, "
                            f"up={sentiment['up_count']}, down={sentiment['down_count']}, "
                            f"数据源: {sentiment.get('data_source')}, 耗时: {elapsed:.2f}秒"
                        )
                    else:
                        logger.warning("市场情绪数据保存失败")
                    break
            else:
                # 数据不足，记录警告
                count = sentiment.get('total_count', 0) if sentiment else 0
                source = sentiment.get('data_source', 'none') if sentiment else 'none'
                logger.warning(f"[WARN]️ 市场情绪数据不完整: {count} 只股票 (数据源: {source}), 跳过更新")
            
            logger.info("=" * 50)
        except asyncio.CancelledError:
            logger.info("更新市场情绪任务已取消（应用正在关闭）")
            return
            
        except Exception as e:
            logger.error(f"更新市场情绪数据失败: {str(e)}", exc_info=True)
    
    async def check_price_alerts(self):
        """检查价格提醒并触发通知（使用优化版服务）"""
        try:
            # [START] 使用优化版服务：批量获取 + 并发处理 + 冷却机制 + 滞后防护
            from services.price_alert_monitor_service_optimized import price_alert_monitor_service_optimized
            
            result = await price_alert_monitor_service_optimized.check_all_alerts()
            
            # Defensive check: ensure result is not None
            if result is None:
                logger.error("价格提醒检查返回None，可能是数据库连接失败")
                return
            
            if result.get("status") == "success":
                triggered = result.get("triggered_count", 0)
                total = result.get("total_alerts", 0)
                elapsed = result.get("elapsed_seconds", 0)
                metrics = result.get("metrics", {})
                
                if triggered > 0:
                    logger.info(f"🔔 价格提醒检查完成: {triggered}/{total} 个提醒已触发 (耗时: {elapsed:.2f}s)")
                
                # 性能监控
                if metrics.get('total_checks', 0) % 100 == 0 and metrics.get('total_checks', 0) > 0:
                    logger.info(f"[CHART] 监控性能统计: 总检查 {metrics['total_checks']} 次, "
                               f"总触发 {metrics['total_checks']} 次, "
                               f"平均耗时 {metrics['avg_check_time']:.2f}s")
                    
            elif result.get("status") == "skipped":
                # Outside trading hours, skip silently
                pass
            else:
                logger.warning(f"价格提醒检查失败: {result}")
                
        except asyncio.CancelledError:
            logger.info("价格提醒检查任务已取消（应用正在关闭）")
            return
            
        except Exception as e:
            logger.error(f"检查价格提醒失败: {str(e)}", exc_info=True)

    async def check_inactive_datasources(self):
        """检查不活跃数据源（超过7天未使用则自动禁用）"""
        try:
            from datasource.core.call_recorder import call_recorder
            inactive = call_recorder.check_inactive_sources(days=7)
            if inactive:
                logger.info(f"已禁用不活跃数据源: {inactive}")
            else:
                logger.info("所有数据源均活跃")
        except Exception as e:
            logger.error(f"检查不活跃数据源失败: {str(e)}", exc_info=True)

    def get_jobs_info(self) -> list:
        """获取所有任务信息"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            })
        return jobs


# 全局任务调度器实例
task_scheduler = TaskScheduler()
