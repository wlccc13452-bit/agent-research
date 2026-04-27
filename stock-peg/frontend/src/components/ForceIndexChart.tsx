import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import * as echarts from 'echarts';
import { useTheme } from '../contexts/ThemeContext';
import { getPinnedZoomWindow, getUnifiedAxisLabelInterval } from '../utils/klineZoom';

interface ForceIndexChartProps {
  data: {
    dates: string[];
    rawForceIndex: number[];
    fi2Ema: number[];
    fi13Ema: number[];
  };
  zoomRange?: {
    start: number;
    end: number;
  };
}

// 主题颜色配置 - 按照招商证券APP标准
const getThemeColors = (isDark: boolean) => ({
  background: isDark ? '#0a0a0a' : '#ffffff',
  text: isDark ? '#e8e8e8' : '#0f172a',
  textSecondary: isDark ? '#808080' : '#64748b',
  border: isDark ? '#1a1a1a' : '#e2e8f0',
  splitLine: isDark ? '#1a1a1a' : '#e2e8f0',
  tooltipBg: isDark ? 'rgba(0, 0, 0, 0.95)' : 'rgba(255, 255, 255, 0.95)',
  tooltipBorder: isDark ? '#1a1a1a' : '#e2e8f0',
  fi2Color: '#ffffff',      // 白色 - FI2 EMA (短期)
  fi13Color: '#ff0000',     // 红色 - FI13 EMA (中期)
  positiveColor: '#ff0000', // 红色 - FORCE正值柱
  negativeColor: '#00ff00', // 绿色 - FORCE负值柱
  zeroAxisColor: '#808080', // 灰色 - 零轴
});

const ForceIndexChart = forwardRef<any, ForceIndexChartProps>(({ data, zoomRange }, ref) => {
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
          const dataIndex = params[0].dataIndex;
          const force = data.rawForceIndex[dataIndex];
          const fi2 = data.fi2Ema[dataIndex];
          const fi13 = data.fi13Ema[dataIndex];
          
          if (!data.dates[dataIndex] || force === null) return '';
          
          const trend = fi13 > 0 ? '📈 上涨' : fi13 < 0 ? '📉 下跌' : '➡️ 横盘';
          const signal = fi2 > 0 ? '买入' : fi2 < 0 ? '卖出' : '中性';
          const forceColor = force >= 0 ? colors.positiveColor : colors.negativeColor;
          
          return `
            <div>
              <div style="font-weight: bold; margin-bottom: 4px;">${data.dates[dataIndex]}</div>
              <div>FORCE: <span style="font-weight: 500; color: ${forceColor}">${force.toFixed(2)}</span></div>
              <div>FI2: <span style="font-weight: 500; color: ${colors.fi2Color}">${fi2?.toFixed(2) || '-'}</span></div>
              <div>FI13: <span style="font-weight: 500; color: ${colors.fi13Color}">${fi13?.toFixed(2) || '-'}</span></div>
              <div style="margin-top: 4px; border-top: 1px solid #e5e7eb; padding-top: 4px;">
                <div>趋势: <span style="font-weight: 500;">${trend}</span></div>
                <div>信号: <span style="font-weight: 500;">${signal}</span></div>
              </div>
            </div>
          `;
        }
      },
      legend: {
        data: ['FI2', 'FI13'],
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
        // FORCE 柱状图
        {
          name: 'FORCE',
          type: 'bar',
          data: data.rawForceIndex,
          barWidth: '60%',
          itemStyle: {
            color: (params: any) => {
              return params.value >= 0 ? colors.positiveColor : colors.negativeColor;
            }
          },
          z: 1
        },
        // FI2 EMA - 白色粗线
        {
          name: 'FI2',
          type: 'line',
          data: data.fi2Ema,
          lineStyle: { width: 2, color: colors.fi2Color },
          symbol: 'none',
          smooth: true,
          z: 2
        },
        // FI13 EMA - 红色粗线
        {
          name: 'FI13',
          type: 'line',
          data: data.fi13Ema,
          lineStyle: { width: 3, color: colors.fi13Color },
          symbol: 'none',
          smooth: true,
          z: 3
        },
        // 零轴参考线
        {
          name: '零轴',
          type: 'line',
          data: new Array(data.dates.length).fill(0),
          lineStyle: { 
            width: 1, 
            color: colors.zeroAxisColor, 
            type: 'dashed' 
          },
          symbol: 'none',
          z: 4
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

export default ForceIndexChart;
