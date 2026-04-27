import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import * as echarts from 'echarts';
import { useTheme } from '../contexts/ThemeContext';
import { getPinnedZoomWindow, getUnifiedAxisLabelInterval } from '../utils/klineZoom';

interface MACDChartProps {
  data: {
    dif: number[];
    dea: number[];
    macdHist: number[];
  };
  dates: string[];
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
  macdColor: '#ffffff',
  macdSignalColor: '#ffff00',
  macdUpColor: '#ff0000',
  macdDownColor: '#00ff00',
});

const MACDChart = forwardRef<any, MACDChartProps>(({ data, dates, zoomRange }, ref) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const currentThemeRef = useRef<boolean>(isDark);

  useImperativeHandle(ref, () => ({
    getEchartsInstance: () => chartInstance.current
  }));

  useEffect(() => {
    if (!chartRef.current || !data || !dates || dates.length === 0) return;

    const colors = getThemeColors(isDark);
    const zoomStart = zoomRange?.start ?? 0;
    const zoomEnd = zoomRange?.end ?? 100;
    const zoomWindow = getPinnedZoomWindow(dates.length, { start: zoomStart, end: zoomEnd });
    const axisLabelInterval = getUnifiedAxisLabelInterval(dates.length, { start: zoomStart, end: zoomEnd });
    
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
          const dataIndex = params[0].dataIndex;
          const macd = data.dif[dataIndex];
          const signal = data.dea[dataIndex];
          const hist = data.macdHist[dataIndex];
          
          if (!dates[dataIndex] || macd === null) return '';
          
          return `
            <div>
              <div style="font-weight: bold; margin-bottom: 4px;">${dates[dataIndex]}</div>
              <div>DIF: <span style="font-weight: 500;">${macd.toFixed(4)}</span></div>
              <div>DEA: <span style="font-weight: 500;">${signal?.toFixed(4) || '-'}</span></div>
              <div>MACD: <span style="font-weight: 500;">${hist?.toFixed(4) || '-'}</span></div>
            </div>
          `;
        }
      },
      legend: {
        data: ['MACD', 'DEA', 'MACD柱'],
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
        data: dates,
        boundaryGap: false,
        axisLine: { lineStyle: { color: colors.border } },
        axisLabel: { color: colors.textSecondary, fontSize: 11, interval: axisLabelInterval },
        splitLine: { show: false },
        min: 0,
        max: dates.length - 1
      },
      yAxis: {
        scale: true,
        splitNumber: 2,
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
          name: 'MACD',
          type: 'line',
          data: data.dif,
          lineStyle: { width: 1, color: colors.macdColor },
          symbol: 'none'
        },
        {
          name: 'DEA',
          type: 'line',
          data: data.dea,
          lineStyle: { width: 1, color: colors.macdSignalColor },
          symbol: 'none'
        },
        {
          name: 'MACD柱',
          type: 'bar',
          data: data.macdHist,
          itemStyle: {
            color: (params: any) => {
              return params.value >= 0 ? colors.macdUpColor : colors.macdDownColor;
            }
          }
        }
      ]
    };
    
    chartInstance.current.setOption(option);
  }, [data, dates, isDark, zoomRange?.start, zoomRange?.end]);

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

export default MACDChart;
