import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import * as echarts from 'echarts';
import { useTheme } from '../contexts/ThemeContext';
import { getPinnedZoomWindow, getUnifiedAxisLabelInterval } from '../utils/klineZoom';

interface PMR5ChartProps {
  data: {
    dates: string[];
    pmr5?: (number | null)[];
  };
  zoomRange?: {
    start: number;
    end: number;
  };
}

// 主题颜色配置
const getThemeColors = (isDark: boolean) => ({
  background: isDark ? '#0a0a0a' : '#ffffff',
  text: isDark ? '#e8e8e8' : '#0f172a',
  textSecondary: isDark ? '#808080' : '#64748b',
  border: isDark ? '#1a1a1a' : '#e2e8f0',
  splitLine: isDark ? '#1a1a1a' : '#e2e8f0',
  tooltipBg: isDark ? 'rgba(0, 0, 0, 0.95)' : 'rgba(255, 255, 255, 0.95)',
  tooltipBorder: isDark ? '#1a1a1a' : '#e2e8f0',
  pmr5Color: '#f97316',   // 橙色
  referenceLine: '#ff0000', // 红色（参考线）
});

const PMR5Chart = forwardRef<any, PMR5ChartProps>(({ data, zoomRange }, ref) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const currentThemeRef = useRef<boolean>(isDark);

  useImperativeHandle(ref, () => ({
    getEchartsInstance: () => chartInstance.current
  }));

  useEffect(() => {
    if (!chartRef.current || !data || !data.dates || data.dates.length === 0) return;
    if (!data.pmr5 || !data.pmr5.some(v => v !== null)) return;

    const colors = getThemeColors(isDark);
    const zoomStart = zoomRange?.start ?? 0;
    const zoomEnd = zoomRange?.end ?? 100;
    const zoomWindow = getPinnedZoomWindow(data.dates.length, { start: zoomStart, end: zoomEnd });
    const axisLabelInterval = getUnifiedAxisLabelInterval(data.dates.length, { start: zoomStart, end: zoomEnd });
    
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current, isDark ? 'dark' : undefined);
      currentThemeRef.current = isDark;
    } else if (isDark !== currentThemeRef.current) {
      chartInstance.current.dispose();
      chartInstance.current = echarts.init(chartRef.current, isDark ? 'dark' : undefined);
      currentThemeRef.current = isDark;
    }
    
    const option: echarts.EChartsOption = {
      backgroundColor: colors.background,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        confine: true,
        backgroundColor: colors.tooltipBg,
        borderColor: colors.tooltipBorder,
        padding: [8, 12],
        textStyle: { color: colors.text, fontSize: 12 },
        formatter: (params: any) => {
          if (!params || params.length === 0) return '';
          
          const dataIndex = params[0].dataIndex;
          const date = data.dates[dataIndex];
          const value = data.pmr5?.[dataIndex];
          
          if (value === null || value === undefined) return '';
          
          return `
            <div>
              <div style="font-weight: bold; margin-bottom: 4px;">${date}</div>
              <div>PMR5: <span style="font-weight: 500; color: ${colors.pmr5Color}">${value.toFixed(4)}</span></div>
            </div>
          `;
        }
      },
      legend: {
        data: ['PMR5'],
        top: 5,
        textStyle: { color: colors.text, fontSize: 11 }
      },
      grid: {
        left: '10%',
        right: '12%',
        top: 30,
        bottom: 20
      },
      xAxis: {
        type: 'category',
        data: data.dates,
        boundaryGap: false,
        axisLine: { lineStyle: { color: colors.border } },
        axisLabel: { color: colors.textSecondary, fontSize: 11, interval: axisLabelInterval },
        splitLine: { show: false },
        min: 0,
        max: data.dates.length - 1
      },
      yAxis: {
        type: 'value',
        scale: true,
        splitNumber: 4,
        position: 'right',
        axisLine: { lineStyle: { color: colors.border }, show: true },
        axisLabel: { color: colors.textSecondary, fontSize: 11 },
        splitLine: { lineStyle: { color: colors.splitLine } }
      },
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: 0,
            startValue: zoomWindow.startIndex,
            endValue: zoomWindow.endIndex
          }
        ],
      series: [
        {
          name: 'PMR5',
          type: 'line',
          data: data.pmr5,
          lineStyle: { width: 2, color: colors.pmr5Color },
          symbol: 'none',
          connectNulls: true,
          // 添加参考线（PMR=1表示股价涨幅=均线涨幅）
          markLine: {
            silent: true,
            symbol: 'none',
            data: [
              {
                yAxis: 1,
                lineStyle: {
                  color: colors.referenceLine,
                  type: 'dashed',
                  width: 1
                },
                label: {
                  show: true,
                  position: 'end',
                  formatter: '基准线(1.0)',
                  color: colors.textSecondary,
                  fontSize: 10
                }
              }
            ]
          }
        }
      ]
    };
    
    chartInstance.current.setOption(option);
  }, [data, isDark, zoomRange?.start, zoomRange?.end]);

  useEffect(() => {
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, []);

  return (
    <div 
      ref={chartRef} 
      style={{ width: '100%', height: '100%' }}
    />
  );
});

export default PMR5Chart;
