/**
 * 财务指标卡片组件
 * 显示12个核心财务指标的网格
 */
import { BarChart2 } from 'lucide-react';
import CollapsibleCard from './CollapsibleCard';

interface FinancialMetricsCardProps {
  data: Record<string, any>;
}

// 财务指标配置
const FINANCIAL_METRICS = [
  { label: '市盈率(PE)', key: 'pe_ratio', unit: '', format: 'number' },
  { label: '市净率(PB)', key: 'pb_ratio', unit: '', format: 'number' },
  { label: '市销率(PS)', key: 'ps_ratio', unit: '', format: 'number' },
  { label: 'PEG', key: 'peg_ratio', unit: '', format: 'number' },
  { label: 'ROE', key: 'roe', unit: '%', format: 'percent' },
  { label: 'ROA', key: 'roa', unit: '%', format: 'percent' },
  { label: '毛利率', key: 'gross_margin', unit: '%', format: 'percent' },
  { label: '净利率', key: 'net_margin', unit: '%', format: 'percent' },
  { label: '负债率', key: 'debt_ratio', unit: '%', format: 'percent' },
  { label: '营收增长', key: 'revenue_growth', unit: '%', format: 'percent' },
  { label: '利润增长', key: 'profit_growth', unit: '%', format: 'percent' },
  { label: '现金流', key: 'cash_flow', unit: '亿', format: 'currency' },
];

export default function FinancialMetricsCard({ data }: FinancialMetricsCardProps) {
  // 格式化数值
  const formatValue = (value: any, format: string) => {
    if (value === null || value === undefined) return '--';
    switch (format) {
      case 'percent':
        return (value * 100).toFixed(2);
      case 'currency':
        return (value / 100000000).toFixed(2);
      default:
        return typeof value === 'number' ? value.toFixed(2) : value;
    }
  };

  // 判断数值颜色
  const getValueColor = (key: string, value: number) => {
    if (value === null || value === undefined) return 'var(--text-muted)';
    
    // 增长类指标 - A股风格：红涨绿跌
    if (['revenue_growth', 'profit_growth'].includes(key)) {
      return value > 0 ? 'var(--success-color)' : value < 0 ? 'var(--danger-color)' : 'var(--text-muted)';
    }
    // 负债率
    if (key === 'debt_ratio') {
      return value > 0.7 ? 'var(--danger-color)' : value > 0.5 ? 'var(--warning-color)' : 'var(--success-color)';
    }
    return 'var(--text-primary)';
  };

  return (
    <CollapsibleCard 
      title="财务数据" 
      icon={<BarChart2 size={16} style={{ color: 'var(--primary-color)' }} />}
      defaultOpen={true}
      className="flex-shrink-0"
    >
      <div className="grid grid-cols-2 gap-2 p-2">
        {FINANCIAL_METRICS.map(metric => {
          const value = data[metric.key];
          const formatted = formatValue(value, metric.format);
          const colorStyle = typeof value === 'number' ? { color: getValueColor(metric.key, value) } : { color: 'var(--text-muted)' };

          return (
            <div key={metric.key} className="p-2.5" style={{ backgroundColor: 'var(--bg-dark)' }}>
              <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>{metric.label}</div>
              <div className="text-sm font-bold font-mono" style={colorStyle}>
                {formatted}{metric.unit && value !== null && value !== undefined ? metric.unit : ''}
              </div>
            </div>
          );
        })}
      </div>
    </CollapsibleCard>
  );
}
