import asyncio
import logging
import os
import pickle
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, date
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from config.settings import settings
from database.session import async_session_maker
from database.operations import get_reports_for_training
from database.models import DailyReport

logger = logging.getLogger(__name__)


class StockPredictionModel:
    """股票预测模型"""
    
    def __init__(self):
        self.model = None
        self.model_path = settings.data_dir / "model" / "stock_predictor.pkl"
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 特征列表
        self.feature_names = [
            # 技术指标
            'ma5', 'ma10', 'ma20', 'ma_ratio',
            'macd', 'macd_signal', 'macd_hist',
            'rsi', 'kdj_k', 'kdj_d', 'kdj_j',
            
            # 价格特征
            'price_change_1d', 'price_change_5d', 'price_change_10d',
            'volatility_10d', 'volatility_20d',
            
            # 成交量特征
            'volume_ratio', 'turnover_rate',
            
            # 基本面特征
            'pe_ratio', 'pb_ratio', 'market_cap',
            'roe', 'roa', 'debt_ratio',
            
            # 市场特征
            'sector_ranking', 'sector_money_flow',
            'us_market_change', 'correlation_score'
        ]
        
        # 移除 __init__ 中的同步模型加载
        # self._load_model()
    
    def _load_model_sync(self):
        """同步加载模型 (用于首次预测)"""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info(f"成功加载模型: {self.model_path}")
            except Exception as e:
                logger.error(f"加载模型失败: {str(e)}")
                self.model = None
        else:
            logger.info("未找到已保存的模型")

    async def _load_model(self):
        """加载已保存的模型 (异步处理)"""
        if await asyncio.to_thread(self.model_path.exists):
            try:
                def _load():
                    with open(self.model_path, 'rb') as f:
                        return pickle.load(f)
                self.model = await asyncio.to_thread(_load)
                logger.info(f"成功加载模型: {self.model_path}")
            except Exception as e:
                logger.error(f"加载模型失败: {str(e)}")
                self.model = None
        else:
            logger.info("未找到已保存的模型")
    
    async def _save_model(self):
        """保存模型 (异步处理)"""
        try:
            def _save():
                with open(self.model_path, 'wb') as f:
                    pickle.dump(self.model, f)
            await asyncio.to_thread(_save)
            logger.info(f"成功保存模型: {self.model_path}")
        except Exception as e:
            logger.error(f"保存模型失败: {str(e)}")
    
    async def prepare_training_data(self, days: int = 365) -> Tuple[np.ndarray, np.ndarray]:
        """
        准备训练数据
        
        Args:
            days: 使用最近多少天的数据
        
        Returns:
            features, labels
        """
        logger.info(f"开始准备训练数据，使用最近 {days} 天的数据")
        
        async with async_session_maker() as session:
            # 使用 ops 函数获取训练数据
            reports = await get_reports_for_training(session, days)
            
            if not reports:
                logger.warning("没有找到足够的训练数据")
                return None, None
            
            logger.info(f"找到 {len(reports)} 条训练数据")
            
            # 构建特征矩阵
            features_list = []
            labels_list = []
            
            for report in reports:
                try:
                    # 提取特征
                    features = self._extract_features_from_report(report)
                    
                    # 标签：1=上涨, 0=震荡, -1=下跌
                    if report.actual_direction == '上涨':
                        label = 1
                    elif report.actual_direction == '下跌':
                        label = -1
                    else:
                        label = 0
                    
                    features_list.append(features)
                    labels_list.append(label)
                    
                except Exception as e:
                    logger.error(f"处理报告 {report.stock_code} {report.report_date} 失败: {str(e)}")
                    continue
            
            if not features_list:
                logger.warning("没有提取到有效的特征数据")
                return None, None
            
            X = np.array(features_list)
            y = np.array(labels_list)
            
            logger.info(f"训练数据准备完成: {X.shape[0]} 样本, {X.shape[1]} 特征")
            
            return X, y
    
    def _extract_features_from_report(self, report: DailyReport) -> List[float]:
        """从报告中提取特征"""
        features = []
        
        # 技术指标
        features.extend([
            float(report.ma5 or 0),
            float(report.ma10 or 0),
            float(report.ma20 or 0),
            float(report.ma5 / report.ma10 if report.ma5 and report.ma10 else 1.0),  # ma_ratio
            float(report.macd or 0),
            float(report.macd_signal or 0),
            float(report.macd_hist or 0),
            float(report.rsi or 50),
            float(report.kdj_k or 50),
            float(report.kdj_d or 50),
            float(report.kdj_j or 50)
        ])
        
        # 价格特征（从报告中提取或使用默认值）
        features.extend([
            float(report.change_pct or 0),  # 1日涨跌幅
            0.0,  # 5日涨跌幅（需要计算）
            0.0,  # 10日涨跌幅
            0.0,  # 10日波动率
            0.0   # 20日波动率
        ])
        
        # 成交量特征
        features.extend([
            1.0,  # volume_ratio（需要计算）
            float(report.turnover_rate or 0)
        ])
        
        # 基本面特征
        features.extend([
            float(report.pe_ratio or 0),
            float(report.pb_ratio or 0),
            float(report.market_cap or 0),
            0.0,  # roe（需要从财务数据获取）
            0.0,  # roa
            0.0   # debt_ratio
        ])
        
        # 市场特征
        features.extend([
            0.0,  # sector_ranking
            float(report.main_money or 0),  # sector_money_flow
            0.0,  # us_market_change
            0.0   # correlation_score
        ])
        
        return features
    
    async def train(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        训练模型 (异步)
        
        Args:
            X: 特征矩阵
            y: 标签
        
        Returns:
            训练结果
        """
        try:
            logger.info("开始训练模型...")
            
            def _train_logic():
                # 分割训练集和测试集
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                # 创建LightGBM数据集
                train_data = lgb.Dataset(X_train, label=y_train)
                test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
                
                # 模型参数
                params = {
                    'objective': 'multiclass',
                    'num_class': 3,  # -1, 0, 1
                    'metric': 'multi_logloss',
                    'boosting_type': 'gbdt',
                    'num_leaves': 31,
                    'learning_rate': 0.05,
                    'feature_fraction': 0.8,
                    'bagging_fraction': 0.8,
                    'bagging_freq': 5,
                    'verbose': -1,
                    'seed': 42
                }
                
                # 训练模型
                trained_model = lgb.train(
                    params,
                    train_data,
                    num_boost_round=100,
                    valid_sets=[test_data],
                    callbacks=[
                        lgb.early_stopping(stopping_rounds=10),
                        lgb.log_evaluation(period=10)
                    ]
                )
                
                # 预测测试集
                y_pred = trained_model.predict(X_test)
                y_pred_class = np.argmax(y_pred, axis=1) - 1  # 转换回 -1, 0, 1
                
                # 计算评估指标
                accuracy = accuracy_score(y_test, y_pred_class)
                precision = precision_score(y_test, y_pred_class, average='weighted', zero_division=0)
                recall = recall_score(y_test, y_pred_class, average='weighted', zero_division=0)
                f1 = f1_score(y_test, y_pred_class, average='weighted', zero_division=0)
                
                return trained_model, {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1
                }
            
            self.model, metrics = await asyncio.to_thread(_train_logic)
            
            logger.info(f"模型训练完成 - 准确率: {metrics['accuracy']:.4f}, F1分数: {metrics['f1_score']:.4f}")
            
            # 保存模型
            await self._save_model()
            
            return metrics
            
        except Exception as e:
            logger.error(f"模型训练失败: {str(e)}", exc_info=True)
            raise
    
    def predict(self, features: np.ndarray) -> Dict:
        """
        预测 (同步, 建议使用 asyncio.to_thread 调用)
        
        Args:
            features: 特征数组
        
        Returns:
            预测结果
        """
        if self.model is None:
            # 尝试同步加载
            self._load_model_sync()
            
            if self.model is None:
                logger.warning("模型未加载，返回默认预测")
                return {
                    'direction': '震荡',
                    'probability': 0.5,
                    'confidence': '低'
                }
        
        try:
            # 预测
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            proba = self.model.predict(features)[0]
            
            # 获取预测类别和概率
            # 类别: 0=-1(下跌), 1=0(震荡), 2=1(上涨)
            pred_class = np.argmax(proba)
            
            if pred_class == 0:
                direction = '下跌'
                probability = proba[0]
            elif pred_class == 2:
                direction = '上涨'
                probability = proba[2]
            else:
                direction = '震荡'
                probability = proba[1]
            
            # 置信度
            if probability > 0.7:
                confidence = '高'
            elif probability > 0.55:
                confidence = '中'
            else:
                confidence = '低'
            
            return {
                'direction': direction,
                'probability': float(probability),
                'confidence': confidence,
                'probabilities': {
                    '下跌': float(proba[0]),
                    '震荡': float(proba[1]),
                    '上涨': float(proba[2])
                }
            }
            
        except Exception as e:
            logger.error(f"预测失败: {str(e)}")
            return {
                'direction': '震荡',
                'probability': 0.5,
                'confidence': '低'
            }
    
    def get_feature_importance(self) -> Dict:
        """获取特征重要性"""
        if self.model is None:
            return {}
        
        try:
            importance = self.model.feature_importance(importance_type='gain')
            feature_importance = dict(zip(self.feature_names, importance.tolist()))
            
            # 排序
            sorted_importance = dict(
                sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            )
            
            return sorted_importance
        except Exception as e:
            logger.error(f"获取特征重要性失败: {str(e)}")
            return {}


# 全局模型实例
prediction_model = StockPredictionModel()
