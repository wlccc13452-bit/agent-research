import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import * as echarts from 'echarts';
import { useTheme } from '../contexts/ThemeContext';
import { getPinnedZoomWindow, getUnifiedAxisLabelInterval } from '../utils/klineZoom';

interface VolumeChartProps {
  data: Array<{
    date: string;
    open: number;
    close: number;
    volume: number;
  }>;
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
  tooltipBg: isDark ? 'rgba(0, 0, 0, 0.95)' : 'rgba(255, 255, 255, 0.95)',
  tooltipBorder: isDark ? '#1a1a1a' : '#e2e8f0',
  upVolColor: '#ef4444',
  downVolColor: isDark ? '#22d3ee' : '#22c55e',
});

const VolumeChart = forwardRef<any, VolumeChartProps>(({ data, zoomRange }, ref) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const currentThemeRef = useRef<boolean>(isDark);

  useImperativeHandle(ref, () => ({
    getEchartsInstance: () => chartInstance.current
  }));

  useEffect(() => {
    if (!chartRef.current || !data || data.length === 0) return;

    const colors = getThemeColors(isDark);
    const zoomStart = zoomRange?.start ?? 0;
    const zoomEnd = zoomRange?.end ?? 100;
    const zoomWindow = getPinnedZoomWindow(data.length, { start: zoomStart, end: zoomEnd });
    const axisLabelInterval = getUnifiedAxisLabelInterval(data.length, { start: zoomStart, end: zoomEnd });
    
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current, isDark ? 'dark' : undefined);
      currentThemeRef.current = isDark;
    } else if (isDark !== currentThemeRef.current) {
      chartInstance.current.dispose();
      chartInstance.current = echarts.init(chartRef.current, isDark ? 'dark' : undefined);
      currentThemeRef.current = isDark;
    }
    
    const dates = data.map(d => d.date);
    const volumes = data.map(d => d.volume);
    
    const option: echarts.EChartsOption = {
      backgroundColor: colors.background,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        confine: true,
        backgroundColor: colors.tooltipBg,
        borderColor: colors.tooltipBorder,
        padding: [8, 12],
        textStyle: { color: colors.text, fontSize: 12 },
        formatter: (params: any) => {
          const dataIndex = params[0].dataIndex;
          const d = data[dataIndex];
          if (!d) return '';
          return `
            <div>
              <div style="font-weight: bold; margin-bottom: 4px;">${d.date}</div>
              <div>成交量: <span style="font-weight: 500;">${(d.volume / 10000).toFixed(2)}万</span></div>
            </div>
          `;
        }
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
        axisLabel: {
          color: colors.textSecondary,
          fontSize: 11,
          interval: axisLabelInterval
        },
        splitLine: { show: false },
        axisTick: { show: false },
        min: 0,
        max: data.length - 1
      },
      yAxis: {
        scale: true,
        splitNumber: 2,
        position: 'right',
        axisLine: { lineStyle: { color: colors.border }, show: true },
        axisLabel: {
          color: colors.textSecondary,
          fontSize: 12,
          formatter: (value: number) => (value / 10000).toFixed(0) + '万'
        },
        splitLine: { show: false }
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
          name: '成交量',
          type: 'bar',
          data: volumes,
          itemStyle: {
            color: (params: any) => {
              const dataIndex = params.dataIndex;
              const d = data[dataIndex];
              return d.close >= d.open ? colors.upVolColor : colors.downVolColor;
            }
          }
        }
      ]
    };
    
    chartInstance.current.setOption(option);
  }, [data, isDark, zoomRange?.start, zoomRange?.end]);

  // 组件销毁时释放实例
  useEffect(() => {
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, []);

  // 暴露chart实例和getOption方法
  useEffect(() => {
    if (chartInstance.current) {
      (chartRef.current as any).getEchartsOption = () => {
        return chartInstance.current?.getOption();
      };
    }
  }, [data, isDark]);

  return (
    <div 
      ref={chartRef} 
      style={{ width: '100%', height: '100%' }}
    />
  );
});

export default VolumeChart;
