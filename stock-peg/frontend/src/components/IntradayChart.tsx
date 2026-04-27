import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { useTheme } from '../contexts/ThemeContext';

interface IntradayData {
  time: string;
  price: number;
  volume: number;
  amount: number;
  high: number;
  low: number;
}

interface IntradayChartProps {
  data: IntradayData[];
  stockCode: string;
  stockName: string;
  avgPrice: number;
  preClose: number;
  height?: string;
}

// 主题颜色配置 - 纯黑/深灰色系
const getThemeColors = (isDark: boolean) => ({
  background: isDark ? '#0a0a0a' : '#ffffff',
  text: isDark ? '#e8e8e8' : '#0f172a',
  textSecondary: isDark ? '#808080' : '#64748b',
  border: isDark ? '#1a1a1a' : '#e2e8f0',
  splitLine: isDark ? '#1a1a1a' : '#e2e8f0',
  tooltipBg: isDark ? 'rgba(0, 0, 0, 0.95)' : 'rgba(255, 255, 255, 0.95)',
  tooltipBorder: isDark ? '#1a1a1a' : '#e2e8f0',
  upColor: '#ef4444',   // 红涨
  downColor: '#22c55e', // 绿跌
  avgColor: '#f59e0b',  // 均价线黄色
});

export default function IntradayChart({ 
  data, 
  stockCode, 
  stockName, 
  avgPrice, 
  preClose,
  height = '100%' 
}: IntradayChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  useEffect(() => {
    if (!chartRef.current || !data || data.length === 0) return;

    const container = chartRef.current;
    const colors = getThemeColors(isDark);
    
    const updateChart = () => {
      if (container.clientWidth === 0 || container.clientHeight === 0) return;

      // 主题变化时销毁旧实例并重新创建
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
      chartInstance.current = echarts.init(container, isDark ? 'dark' : undefined);

      // 准备数据
      const times = data.map(d => d.time);
      const prices = data.map(d => d.price);
      const volumes = data.map(d => d.volume);
      const avgPrices = data.map(() => avgPrice); // 均价线

      // 计算涨跌幅
      const latestPrice = prices[prices.length - 1];
      const change = latestPrice - preClose;
      const priceColor = change >= 0 ? colors.upColor : colors.downColor;

      // 图表配置
      const option: echarts.EChartsOption = {
        backgroundColor: colors.background,
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          backgroundColor: colors.tooltipBg,
          borderColor: colors.tooltipBorder,
          textStyle: {
            color: colors.text
          },
          formatter: function (params: any) {
            const dataIndex = params[0].dataIndex;
            const d = data[dataIndex];
            if (!d) return '';
            
            const change = d.price - preClose;
            const changePct = preClose !== 0 ? ((change / preClose) * 100).toFixed(2) : '0.00';
            const color = change >= 0 ? colors.upColor : colors.downColor;
            
            return `
              <div style="padding: 8px;">
                <div style="font-weight: bold; margin-bottom: 8px;">${stockName || stockCode} · ${d.time}</div>
                <div>价格: ${d.price.toFixed(2)}</div>
                <div>均价: ${avgPrice.toFixed(2)}</div>
                <div>成交量: ${(d.volume / 10000).toFixed(2)}万</div>
                <div>成交额: ${(d.amount / 100000000).toFixed(2)}亿</div>
                <div style="color: ${color};">
                  涨跌: ${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePct}%)
                </div>
              </div>
            `;
          }
        },
        axisPointer: {
          link: [{ xAxisIndex: 'all' }],
          label: {
            backgroundColor: colors.border
          }
        },
        legend: {
          data: ['价格', '均价', '成交量'],
          top: 10,
          textStyle: {
            color: colors.text
          }
        },
        grid: [
          {
            left: '10%',
            right: '12%',
            top: 50,
            height: '50%'
          },
          {
            left: '10%',
            right: '12%',
            top: '70%',
            height: '15%'
          }
        ],
        xAxis: [
          {
            type: 'category',
            data: times,
            boundaryGap: false,
            axisLine: { lineStyle: { color: colors.border } },
            axisLabel: { 
              color: colors.textSecondary,
              fontSize: 10,
              interval: 29 // 每30分钟显示一个标签
            },
            splitLine: { show: false },
            min: 'dataMin',
            max: 'dataMax'
          },
          {
            type: 'category',
            gridIndex: 1,
            data: times,
            boundaryGap: false,
            axisLine: { lineStyle: { color: colors.border } },
            axisLabel: { show: false },
            splitLine: { show: false },
            axisTick: { show: false },
            min: 'dataMin',
            max: 'dataMax'
          }
        ],
        yAxis: [
          {
            scale: true,
            position: 'right',
            axisLine: { 
              lineStyle: { color: colors.border },
              show: true
            },
            axisLabel: { 
              color: colors.textSecondary,
              fontSize: 12
            },
            splitLine: {
              lineStyle: {
                color: colors.splitLine
              }
            },
            // 昨日收盘价作为基准线
            axisPointer: {
              label: {
                formatter: function(params: any) {
                  const val = params.value;
                  const change = val - preClose;
                  const changePct = preClose !== 0 ? ((change / preClose) * 100).toFixed(2) : '0.00';
                  return `${val.toFixed(2)} (${change >= 0 ? '+' : ''}${changePct}%)`;
                }
              }
            }
          },
          {
            scale: true,
            gridIndex: 1,
            splitNumber: 2,
            position: 'right',
            axisLine: { 
              lineStyle: { color: colors.border },
              show: true
            },
            axisLabel: { 
              color: colors.textSecondary,
              fontSize: 12,
              formatter: (value: number) => (value / 10000).toFixed(0) + '万'
            },
            splitLine: { show: false }
          }
        ],
        series: [
          {
            name: '价格',
            type: 'line',
            data: prices,
            smooth: true,
            lineStyle: {
              width: 2,
              color: priceColor
            },
            symbol: 'none',
            // 填充渐变
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: change >= 0 ? 'rgba(239, 68, 68, 0.3)' : 'rgba(34, 197, 94, 0.3)' },
                { offset: 1, color: 'rgba(0, 0, 0, 0)' }
              ])
            },
            markLine: {
              silent: true,
              symbol: 'none',
              lineStyle: {
                color: colors.textSecondary,
                type: 'dashed',
                width: 1
              },
              label: {
                show: true,
                color: colors.textSecondary,
                formatter: `昨收: ${preClose.toFixed(2)}`
              },
              data: [
                { yAxis: preClose }
              ]
            }
          },
          {
            name: '均价',
            type: 'line',
            data: avgPrices,
            smooth: true,
            lineStyle: {
              width: 1,
              color: colors.avgColor,
              type: 'dashed'
            },
            symbol: 'none'
          },
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes,
            itemStyle: {
              color: function (params: any) {
                const dataIndex = params.dataIndex;
                const d = data[dataIndex];
                // 根据价格涨跌设置颜色
                return d.price >= preClose ? colors.upColor : colors.downColor;
              }
            }
          }
        ]
      };

      chartInstance.current.setOption(option);
    };

    // Initialize resize observer
    const resizeObserver = new ResizeObserver(() => {
      if (container.clientWidth > 0 && container.clientHeight > 0) {
        if (!chartInstance.current) {
          updateChart();
        }
        chartInstance.current?.resize();
      }
    });
    
    resizeObserver.observe(container);
    
    // Initial render
    updateChart();

    return () => {
      resizeObserver.disconnect();
      chartInstance.current?.dispose();
      chartInstance.current = null;
    };
  }, [data, stockCode, stockName, avgPrice, preClose, isDark]);

  return (
    <div 
      ref={chartRef} 
      style={{ 
        width: '100%', 
        height,
        backgroundColor: isDark ? '#0a0a0a' : '#ffffff'
      }} 
    />
  );
}
