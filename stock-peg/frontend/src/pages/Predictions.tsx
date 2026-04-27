import { useQuery } from '@tanstack/react-query';
import { predictionApi } from '../services/api';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function Predictions() {
  // 获取所有预测
  const { data: predictionsData, isLoading } = useQuery({
    queryKey: ['predictions'],
    queryFn: predictionApi.predictAll,
  });

  // 获取板块轮动分析
  const { data: rotation } = useQuery({
    queryKey: ['sector-rotation'],
    queryFn: predictionApi.analyzeSectorRotation,
  });

  if (isLoading) {
    return <div className="loading">加载中...</div>;
  }

  const predictions = predictionsData?.predictions || [];

  return (
    <div className="predictions-page">
      <div className="page-header">
        <h2>明日预测</h2>
        <p>基于多维度数据的智能预测分析</p>
      </div>

      {/* 板块轮动分析 */}
      {rotation && (
        <div className="section">
          <h3>板块轮动分析</h3>
          <div className="rotation-grid">
            <div className="rotation-card">
              <h4>当前热点板块</h4>
              <div className="hotspot-list">
                {rotation.hotspot_sectors?.map((sector: string) => (
                  <div key={sector} className="hotspot-tag">
                    {sector}
                  </div>
                ))}
              </div>
            </div>

            {rotation.next_hotspot_prediction && (
              <div className="rotation-card highlight">
                <h4>预测下一个热点</h4>
                <div className="prediction-value">{rotation.next_hotspot_prediction}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 预测卡片 */}
      <div className="section">
        <h3>个股预测</h3>
        <div className="predictions-grid">
          {predictions.map((pred: any) => {
            const direction = pred.prediction?.direction;
            const probability = pred.prediction?.probability || 0;
            const isUp = direction === '上涨';
            const isDown = direction === '下跌';

            return (
              <div
                key={pred.stock_code}
                className={`prediction-card ${isUp ? 'up' : isDown ? 'down' : ''}`}
              >
                <div className="prediction-header">
                  <h4>{pred.stock_name}</h4>
                  <span className="stock-code">{pred.stock_code}</span>
                </div>

                <div className="prediction-direction">
                  {isUp ? (
                    <TrendingUp className="direction-icon" />
                  ) : isDown ? (
                    <TrendingDown className="direction-icon" />
                  ) : (
                    <Minus className="direction-icon" />
                  )}
                  <span className="direction-text">{direction}</span>
                </div>

                <div className="prediction-probability">
                  <div className="probability-bar">
                    <div
                      className="probability-fill"
                      style={{ width: `${probability * 100}%` }}
                    />
                  </div>
                  <span className="probability-text">
                    概率: {(probability * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="prediction-details">
                  <div className="detail-item">
                    <span className="label">置信度:</span>
                    <span className="value">{pred.prediction?.confidence}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">风险等级:</span>
                    <span className="value">{pred.prediction?.risk_level}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">目标价:</span>
                    <span className="value">
                      {pred.prediction?.target_price_range?.join(' - ')}
                    </span>
                  </div>
                </div>

                <div className="prediction-scores">
                  <div className="score-item">
                    <span>技术面</span>
                    <span className="score">{pred.technical_score?.toFixed(1)}</span>
                  </div>
                  <div className="score-item">
                    <span>基本面</span>
                    <span className="score">{pred.fundamental_score?.toFixed(1)}</span>
                  </div>
                  <div className="score-item">
                    <span>综合</span>
                    <span className="score">{pred.overall_score?.toFixed(1)}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
