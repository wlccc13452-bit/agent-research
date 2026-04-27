/**
 * 市场趋势分析卡片组件
 * 显示价格分位数、ADX、波动率、趋势方向和均线状态
 */
import { TrendingUp, Activity, BarChart3 } from 'lucide-react';
import CollapsibleCard from './CollapsibleCard';

interface MarketTrendCardProps {
  data: {
    price_percentile_3y?: number;
    adx?: number;
    volatility_30d?: number;
    trend_direction?: string;
    ma_status?: string;
    score?: number;
  };
}

export default function MarketTrendCard({ data }: MarketTrendCardProps) {
  if (!data || Object.keys(data).length === 0) return null;

  // 格式化百分比
  const formatPercent = (value?: number) => {
    if (value === undefined || value === null) return '--';
    return (value * 100).toFixed(2) + '%';
  };

  // 格式化数值
  const formatNumber = (value?: number) => {
    if (value === undefined || value === null) return '--';
    return value.toFixed(2);
  };

  // 获取趋势颜色
  const getTrendColor = (trend?: string) => {
    if (!trend) return 'var(--text-muted)';
    if (trend.includes('多头') || trend.includes('反弹')) return 'var(--success-color)';
    if (trend.includes('空头') || trend.includes('下跌')) return 'var(--danger-color)';
    return 'var(--warning-color)';
  };

  // 获取分位数颜色 (低位绿色，高位红色)
  const getPercentileColor = (val?: number) => {
    if (val === undefined || val === null) return 'var(--text-muted)';
    if (val < 0.3) return 'var(--success-color)';
    if (val > 0.7) return 'var(--danger-color)';
    return 'var(--text-primary)';
  };

  return (
    <CollapsibleCard 
      title="市场趋势分析" 
      icon={<Activity size={16} style={{ color: 'var(--primary-color)' }} />}
      defaultOpen={true}
      className="flex-shrink-0"
    >
      <div className="p-3 space-y-3">
        {/* 核心指标网格 */}
        <div className="grid grid-cols-3 gap-2">
          <div className="p-2.5" style={{ backgroundColor: 'var(--bg-dark)' }}>
            <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>3年价格分位</div>
            <div className="text-sm font-bold font-mono" style={{ color: getPercentileColor(data.price_percentile_3y) }}>
              {formatPercent(data.price_percentile_3y)}
            </div>
          </div>
          <div className="p-2.5" style={{ backgroundColor: 'var(--bg-dark)' }}>
            <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>趋势强度(ADX)</div>
            <div className="text-sm font-bold font-mono" style={{ color: 'var(--text-primary)' }}>
              {formatNumber(data.adx)}
            </div>
          </div>
          <div className="p-2.5" style={{ backgroundColor: 'var(--bg-dark)' }}>
            <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>30日波动率</div>
            <div className="text-sm font-bold font-mono" style={{ color: 'var(--text-primary)' }}>
              {formatPercent(data.volatility_30d)}
            </div>
          </div>
        </div>

        {/* 趋势描述 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between p-2 rounded" style={{ backgroundColor: 'var(--bg-hover)' }}>
            <div className="flex items-center gap-2">
              <TrendingUp size={14} style={{ color: 'var(--text-secondary)' }} />
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>趋势方向</span>
            </div>
            <span className="text-sm font-bold" style={{ color: getTrendColor(data.trend_direction) }}>
              {data.trend_direction || '--'}
            </span>
          </div>

          <div className="flex items-center justify-between p-2 rounded" style={{ backgroundColor: 'var(--bg-hover)' }}>
            <div className="flex items-center gap-2">
              <BarChart3 size={14} style={{ color: 'var(--text-secondary)' }} />
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>均线状态</span>
            </div>
            <span className="text-xs font-medium text-right" style={{ color: 'var(--text-primary)', maxWidth: '70%' }}>
              {data.ma_status || '--'}
            </span>
          </div>
        </div>

        {/* 趋势评分 */}
        {data.score !== undefined && (
          <div className="pt-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>趋势综合评分</span>
              <span className="text-xs font-bold" style={{ color: 'var(--primary-color)' }}>{data.score.toFixed(1)} / 5.0</span>
            </div>
            <div className="h-1.5 w-full bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full transition-all duration-500" 
                style={{ 
                  width: `${(data.score / 5) * 100}%`,
                  backgroundColor: data.score > 3.5 ? 'var(--success-color)' : data.score > 2.5 ? 'var(--primary-color)' : 'var(--danger-color)'
                }}
              ></div>
            </div>
          </div>
        )}
      </div>
    </CollapsibleCard>
  );
}
