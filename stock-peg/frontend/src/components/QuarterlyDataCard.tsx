/**
 * 季度数据卡片组件
 * 包含季度趋势图表和季度明细表格
 */
import { BarChart2, Table } from 'lucide-react';
import CollapsibleCard from './CollapsibleCard';
import ReactECharts from 'echarts-for-react';
import { useTheme } from '../contexts/ThemeContext';

interface QuarterlyDataCardProps {
  quarterlyData: any;
}

// 主题颜色配置 - 纯黑/深灰色系
const getThemeColors = (isDark: boolean) => ({
  background: isDark ? '#1a1a1a' : '#ffffff',
  text: isDark ? '#e8e8e8' : '#0f172a',
  textSecondary: isDark ? '#a0a0a0' : '#64748b',
  border: isDark ? '#2a2a2a' : '#e2e8f0',
  splitLine: isDark ? '#2a2a2a' : '#e2e8f0',
  tooltipBg: isDark ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.95)',
  tooltipBorder: isDark ? '#3a3a3a' : '#e2e8f0',
  revenueColor: '#3b82f6',
  profitColor: '#22c55e',
  grossMarginColor: '#f59e0b',
  netMarginColor: '#ef4444',
});

export default function QuarterlyDataCard({ quarterlyData }: QuarterlyDataCardProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // 准备季度数据图表配置
  const getQuarterlyChartOption = () => {
    if (!quarterlyData?.quarters || quarterlyData.quarters.length === 0) {
      return {};
    }
    
    const colors = getThemeColors(isDark);

    const quarters = quarterlyData.quarters;
    const dates = quarters.map((q: any) => q.date);
    const revenues = quarters.map((q: any) => (q.revenue / 100000000).toFixed(2)); // 转换为亿元
    const netProfits = quarters.map((q: any) => (q.net_profit / 100000000).toFixed(2)); // 转换为亿元
    const grossMargins = quarters.map((q: any) => (q.gross_margin * 100).toFixed(2));
    const netMargins = quarters.map((q: any) => (q.net_margin * 100).toFixed(2));

    return {
      title: {
        text: '最近3年季度财务数据',
        left: 'center',
        textStyle: {
          color: colors.text,
          fontSize: 14,
        },
      },
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        backgroundColor: colors.tooltipBg,
        borderColor: colors.tooltipBorder,
        textStyle: {
          color: colors.text,
        },
      },
      legend: {
        data: ['营业收入', '净利润', '毛利率', '净利率'],
        bottom: 0,
        textStyle: {
          color: colors.textSecondary,
        },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '15%',
        containLabel: true,
      },
      xAxis: [
        {
          type: 'category',
          data: dates,
          axisLine: {
            lineStyle: {
              color: colors.border,
            },
          },
          axisLabel: {
            color: colors.textSecondary,
            fontSize: 10,
            rotate: 45,
          },
        },
      ],
      yAxis: [
        {
          type: 'value',
          name: '金额(亿元)',
          position: 'left',
          axisLine: {
            lineStyle: {
              color: colors.border,
            },
          },
          axisLabel: {
            color: colors.textSecondary,
          },
          splitLine: {
            lineStyle: {
              color: colors.splitLine,
            },
          },
        },
        {
          type: 'value',
          name: '比率(%)',
          position: 'right',
          axisLine: {
            lineStyle: {
              color: colors.border,
            },
          },
          axisLabel: {
            color: colors.textSecondary,
          },
          splitLine: {
            show: false,
          },
        },
      ],
      series: [
        {
          name: '营业收入',
          type: 'bar',
          data: revenues,
          itemStyle: {
            color: colors.revenueColor,
          },
        },
        {
          name: '净利润',
          type: 'bar',
          data: netProfits,
          itemStyle: {
            color: colors.profitColor,
          },
        },
        {
          name: '毛利率',
          type: 'line',
          yAxisIndex: 1,
          data: grossMargins,
          itemStyle: {
            color: colors.grossMarginColor,
          },
          lineStyle: {
            width: 2,
          },
        },
        {
          name: '净利率',
          type: 'line',
          yAxisIndex: 1,
          data: netMargins,
          itemStyle: {
            color: colors.netMarginColor,
          },
          lineStyle: {
            width: 2,
          },
        },
      ],
    };
  };

  return (
    <>
      {/* 季度数据柱状图 */}
      <CollapsibleCard 
        title="季度数据趋势" 
        icon={<BarChart2 size={16} style={{ color: 'var(--success-color)' }} />}
        defaultOpen={true}
        className="flex-shrink-0"
      >
        <div className="p-2">
          {quarterlyData?.quarters && quarterlyData.quarters.length > 0 ? (
            <ReactECharts
              option={getQuarterlyChartOption()}
              style={{ height: '300px', width: '100%', backgroundColor: isDark ? '#1a1a1a' : '#ffffff' }}
              opts={{ renderer: 'svg' }}
              theme={isDark ? 'dark' : undefined}
            />
          ) : (
            <div className="h-64 flex items-center justify-center" style={{ color: 'var(--text-secondary)' }}>
              暂无季度数据
            </div>
          )}
        </div>
      </CollapsibleCard>

      {/* 季度数据表格 */}
      <CollapsibleCard 
        title="季度数据明细" 
        icon={<Table size={16} style={{ color: '#a855f7' }} />}
        defaultOpen={false}
        className="flex-shrink-0"
      >
        <div className="p-2">
          {quarterlyData?.quarters && quarterlyData.quarters.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr style={{ backgroundColor: 'var(--bg-dark)', color: 'var(--text-secondary)' }}>
                    <th className="px-2 py-1.5 text-left font-medium">季度</th>
                    <th className="px-2 py-1.5 text-right font-medium">营业收入(亿)</th>
                    <th className="px-2 py-1.5 text-right font-medium">毛利(亿)</th>
                    <th className="px-2 py-1.5 text-right font-medium">净利润(亿)</th>
                    <th className="px-2 py-1.5 text-right font-medium">毛利率(%)</th>
                    <th className="px-2 py-1.5 text-right font-medium">净利率(%)</th>
                  </tr>
                </thead>
                <tbody>
                  {quarterlyData.quarters.map((q: any, idx: number) => (
                    <tr 
                      key={q.date} 
                      className="hover:bg-opacity-50"
                      style={{ 
                        backgroundColor: idx % 2 === 0 ? 'var(--bg-card)' : 'var(--bg-hover)',
                      }}
                    >
                      <td className="px-2 py-1.5 font-medium" style={{ color: 'var(--text-secondary)' }}>{q.date}</td>
                      <td className="px-2 py-1.5 text-right font-mono" style={{ color: 'var(--text-secondary)' }}>
                        {(q.revenue / 100000000).toFixed(2)}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono" style={{ color: 'var(--text-secondary)' }}>
                        {((q.gross_profit || 0) / 100000000).toFixed(2)}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono">
                        <span style={{ color: q.net_profit > 0 ? 'var(--success-color)' : 'var(--danger-color)' }}>
                          {(q.net_profit / 100000000).toFixed(2)}
                        </span>
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono" style={{ color: 'var(--text-secondary)' }}>
                        {(q.gross_margin * 100).toFixed(2)}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono">
                        <span style={{ color: q.net_margin > 0 ? 'var(--success-color)' : 'var(--danger-color)' }}>
                          {(q.net_margin * 100).toFixed(2)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="h-32 flex items-center justify-center" style={{ color: 'var(--text-secondary)' }}>
              暂无季度数据
            </div>
          )}
        </div>
      </CollapsibleCard>
    </>
  );
}
