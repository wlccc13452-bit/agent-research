import { useQuery } from '@tanstack/react-query';
import { usMarketApi } from '../services/api';
import { TrendingUp, TrendingDown, Globe } from 'lucide-react';

export default function USMarket() {
  // 获取美股指数
  const { data: indicesResponse, isLoading: loadingIndices } = useQuery({
    queryKey: ['us-indices'],
    queryFn: usMarketApi.getIndices,
    refetchInterval: 60000, // 每分钟刷新
  });

  // 获取每日美股报告
  const { data: reportData, isLoading: loadingReport } = useQuery({
    queryKey: ['us-daily-report'],
    queryFn: usMarketApi.getDailyReport,
  });

  // 提取实际数据（适配新的API格式）
  const indices = indicesResponse?.data || indicesResponse;

  if (loadingIndices || loadingReport) {
    return <div className="loading">加载中...</div>;
  }

  const report = reportData?.report || '';

  return (
    <div className="us-market-page">
      <div className="page-header">
        <h2>美股市场分析</h2>
        <p>国际市场联动分析</p>
      </div>

      {/* 美股指数 */}
      {indices && (
        <div className="section">
          <h3>美股主要指数</h3>
          <div className="indices-grid">
            {Object.entries(indices).map(([name, data]: [string, any]) => {
              const isUp = data.change_pct > 0;
              const isDown = data.change_pct < 0;

              return (
                <div key={name} className={`index-card ${isUp ? 'up' : isDown ? 'down' : ''}`}>
                  <h4>{name}</h4>
                  <div className="index-price">{data.previous_close?.toFixed(2)}</div>
                  <div className="index-change">
                    {isUp ? (
                      <TrendingUp className="change-icon" />
                    ) : isDown ? (
                      <TrendingDown className="change-icon" />
                    ) : null}
                    <span className="change-pct">{data.change_pct?.toFixed(2)}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 美股市场报告 */}
      {report && (
        <div className="section">
          <h3>每日美股分析报告</h3>
          <div className="report-container">
            <pre className="report-content">{report}</pre>
          </div>
        </div>
      )}

      {/* 国际市场联动说明 */}
      <div className="section">
        <h3>国际市场联动</h3>
        <div className="info-cards">
          <div className="info-card">
            <Globe className="info-icon" />
            <h4>美股联动</h4>
            <p>通过AI分析持仓股票与美股相关标的的联动关系,预测次日开盘影响</p>
          </div>
          <div className="info-card">
            <h4>大宗商品</h4>
            <p>监控LME铝、铜等大宗商品期货价格,分析对有色板块的影响</p>
          </div>
          <div className="info-card">
            <h4>板块轮动</h4>
            <p>结合美股板块表现,预测A股板块轮动趋势</p>
          </div>
        </div>
      </div>
    </div>
  );
}
