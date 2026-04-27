import { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import * as echarts from 'echarts';
import { useTheme } from '../contexts/ThemeContext';
import { stocksApi } from '../services/api';
import HorizontalResizableDivider from './HorizontalResizableDivider';
import IndicatorContainer from './IndicatorContainer';
import { DEFAULT_ZOOM_RANGE, getZoomRangeFromPayload, areZoomRangesEqual, getPinnedZoomWindow, getUnifiedAxisLabelInterval } from '../utils/klineZoom';

interface KLineData {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
}

interface KLineChartProps {
  data: KLineData[];
  stockCode: string;
  stockName: string;
  height?: string;
  trendMode?: boolean;
  compactLineMode?: boolean;
  goToLatestTrigger?: number;
}

interface ChartHeights {
  kline: number;      // K线图高度（百分比）
  indicator1: number; // 指标容器1高度（百分比）
  indicator2: number; // 指标容器2高度（百分比）
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
  upColor: isDark ? 'transparent' : '#ef4444',
  upBorderColor: isDark ? '#ff0000' : '#ef4444',
  downColor: isDark ? '#22d3ee' : '#22c55e',
  downBorderColor: isDark ? '#22d3ee' : '#22c55e',
  ma5Color: '#f97316',
  ma10Color: '#ffff00',
  ma20Color: '#ff00ff',
  ma30Color: '#0000ff',
  ma60Color: '#00ff00',
  ma120Color: '#f59e0b',
  ema9Color: '#38bdf8',
  ema20Color: '#ff00ff',  // 同 MA21
  ema60Color: '#00ff00',  // 同 MA60
  ema120Color: '#8b4513', // 同 MA120
  // 趋势判断K线颜色（EMA21 vs MA21）
  uptrendColor: '#22c55e',
  uptrendBorderColor: '#22c55e',
  downtrendColor: '#000000',
  downtrendBorderColor: '#ffffff',
});

// 计算EMA
const calculateEMA = (data: number[], period: number): number[] => {
  const result: number[] = [];
  const multiplier = 2 / (period + 1);
  
  let sum = 0;
  for (let i = 0; i < period; i++) {
    sum += data[i];
  }
  result[period - 1] = sum / period;
  
  for (let i = period; i < data.length; i++) {
    result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1];
  }
  
  for (let i = 0; i < period - 1; i++) {
    result[i] = null as any;
  }
  
  return result;
};

// 计算MACD
const calculateMACD = (closes: number[]) => {
  const ema12 = calculateEMA(closes, 12);
  const ema26 = calculateEMA(closes, 26);
  
  const dif: number[] = [];
  for (let i = 0; i < closes.length; i++) {
    if (ema12[i] !== null && ema26[i] !== null) {
      dif[i] = ema12[i] - ema26[i];
    } else {
      dif[i] = null as any;
    }
  }
  
  const dea = calculateEMA(dif.filter(v => v !== null), 9);
  
  const deaFull: number[] = [];
  let deaIndex = 0;
  for (let i = 0; i < dif.length; i++) {
    if (dif[i] === null) {
      deaFull[i] = null as any;
    } else {
      deaFull[i] = dea[deaIndex++] ?? null;
    }
  }
  
  const macdHist: number[] = [];
  for (let i = 0; i < closes.length; i++) {
    if (dif[i] !== null && deaFull[i] !== null) {
      macdHist[i] = (dif[i] - deaFull[i]) * 2;
    } else {
      macdHist[i] = null as any;
    }
  }
  
  return { dif, dea: deaFull, macdHist };
};

export default function KLineChart({ 
  data, 
  stockCode, 
  stockName, 
  height = '100%',
  trendMode = false,
  compactLineMode = false,
  goToLatestTrigger = 0
}: KLineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const klineChartRef = useRef<HTMLDivElement>(null);
  const klineInstance = useRef<echarts.ECharts | null>(null);
  
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  
  // 追踪当前主题（用于检测主题变化）
  const currentThemeRef = useRef<boolean>(isDark);
  
  // 用于图表同步的ref
  const indicator1ChartRef = useRef<any>(null);
  const indicator2ChartRef = useRef<any>(null);
  const zoomRangeRef = useRef(DEFAULT_ZOOM_RANGE);
  const isSyncingZoomRef = useRef(false);
  
  // 用于强制重新同步图表的版本号
  const [indicatorVersion, setIndicatorVersion] = useState(0);
  const [zoomRange, setZoomRange] = useState(DEFAULT_ZOOM_RANGE);
  
  // 管理图表高度百分比
  const [chartHeights, setChartHeights] = useState<ChartHeights>({
    kline: 58,
    indicator1: 20,
    indicator2: 22
  });
  
  // PMR数据状态
  const [pmrData, setPmrData] = useState<any>(null);
  
  // Force Index数据状态
  const [forceIndexData, setForceIndexData] = useState<any>(null);
  
  const MIN_HEIGHT_PERCENT = 10;
  const MAX_HEIGHT_PERCENT = 80;

  const getAllCharts = useCallback(
    () =>
      [
        klineInstance.current,
        indicator1ChartRef.current?.getEchartsInstance?.(),
        indicator2ChartRef.current?.getEchartsInstance?.()
      ].filter(Boolean) as echarts.ECharts[],
    []
  );

  const applyZoomToCharts = useCallback((range: { start: number; end: number }, silent = true) => {
    const charts = getAllCharts();
    if (charts.length === 0 || data.length === 0) return;

    const zoomWindow = getPinnedZoomWindow(data.length, range);
    charts.forEach((chart) => {
      chart.dispatchAction({
        type: 'dataZoom',
        dataZoomIndex: 0,
        start: range.start,
        end: range.end,
        startValue: zoomWindow.startIndex,
        endValue: zoomWindow.endIndex,
        silent
      });
    });
  }, [data.length, getAllCharts]);

  // 获取PMR数据
  const alignedPmrData = useMemo(() => {
    if (!data || data.length === 0 || !pmrData || !pmrData.dates) return null;
    
    const dates = data.map(d => d.date);
    const pmrMap = new Map();
    pmrData.dates.forEach((date: string, i: number) => {
      pmrMap.set(date, i);
    });
    
    const result: any = { dates };
    const periods = [5, 10, 20, 30, 60];
    
    periods.forEach(period => {
      const key = `pmr${period}`;
      if (pmrData[key]) {
        result[key] = dates.map(date => {
          const index = pmrMap.get(date);
          return index !== undefined ? pmrData[key][index] : null;
        });
      }
    });
    
    return result;
  }, [data, pmrData]);

  useEffect(() => {
    const fetchPMR = async () => {
      if (!stockCode || !data || data.length === 0) return;
      
      try {
        console.log('正在获取PMR数据...', stockCode, '请求天数:', data.length);
        // 获取与K线数据同样长度的PMR数据
        const result = await stocksApi.getPMR(stockCode, data.length);
        console.log('获取到PMR数据:', result);
        setPmrData(result);
      } catch (error) {
        console.error('获取PMR数据失败:', error);
        setPmrData(null);
      }
    };
    
    fetchPMR();
  }, [stockCode, data.length]); // 使用 data.length 作为依赖，只有当K线数据变化时才重新获取PMR

  // 获取Force Index数据
  useEffect(() => {
    const fetchForceIndex = async () => {
      if (!stockCode || !data || data.length === 0) return;
      
      try {
        console.log('正在获取Force Index数据...', stockCode, '请求天数:', data.length);
        const result = await stocksApi.getForceIndex(stockCode, 'day', data.length);
        console.log('获取到Force Index数据:', result);
        
        if (result && result.recent_data) {
          // 对齐数据日期
          const dates = data.map(d => d.date);
          const fiMap = new Map();
          result.recent_data.forEach((item: any) => {
            fiMap.set(item.date, item);
          });
          
          const alignedData = {
            dates,
            rawForceIndex: dates.map(date => {
              const item = fiMap.get(date);
              return item ? item.raw_force_index : null;
            }),
            fi2Ema: dates.map(date => {
              const item = fiMap.get(date);
              return item ? item.fi_short_ema : null;
            }),
            fi13Ema: dates.map(date => {
              const item = fiMap.get(date);
              return item ? item.fi_long_ema : null;
            })
          };
          
          setForceIndexData(alignedData);
        } else {
          setForceIndexData(null);
        }
      } catch (error) {
        console.error('获取Force Index数据失败:', error);
        setForceIndexData(null);
      }
    };
    
    fetchForceIndex();
  }, [stockCode, data.length]);

  useEffect(() => {
    zoomRangeRef.current = zoomRange;
  }, [zoomRange]);

  useEffect(() => {
    const initialZoomRange = DEFAULT_ZOOM_RANGE;
    zoomRangeRef.current = initialZoomRange;
    setZoomRange(initialZoomRange);
  }, [stockCode]);
  
  // 处理K线和指标1之间的拖拽
  const handleKlineIndicator1Resize = (delta: number) => {
    if (!containerRef.current) return;
    
    const containerHeight = containerRef.current.clientHeight;
    const deltaPercent = (delta / containerHeight) * 100;
    
    setChartHeights(prev => {
      const newKline = Math.max(MIN_HEIGHT_PERCENT, Math.min(MAX_HEIGHT_PERCENT, prev.kline + deltaPercent));
      const deltaDiff = newKline - prev.kline;
      const newIndicator1 = prev.indicator1 - deltaDiff;
      
      if (newIndicator1 < MIN_HEIGHT_PERCENT) {
        return prev;
      }
      
      return {
        ...prev,
        kline: newKline,
        indicator1: newIndicator1
      };
    });
  };
  
  // 处理指标1和指标2之间的拖拽
  const handleIndicator1Indicator2Resize = (delta: number) => {
    if (!containerRef.current) return;
    
    const containerHeight = containerRef.current.clientHeight;
    const deltaPercent = (delta / containerHeight) * 100;
    
    setChartHeights(prev => {
      const newIndicator1 = Math.max(MIN_HEIGHT_PERCENT, Math.min(MAX_HEIGHT_PERCENT, prev.indicator1 + deltaPercent));
      const deltaDiff = newIndicator1 - prev.indicator1;
      const newIndicator2 = prev.indicator2 - deltaDiff;
      
      if (newIndicator2 < MIN_HEIGHT_PERCENT) {
        return prev;
      }
      
      return {
        ...prev,
        indicator1: newIndicator1,
        indicator2: newIndicator2
      };
    });
  };
  
  // 计算MA均线
  const calculateMA = (dayCount: number) => {
    const result = [];
    for (let i = 0; i < data.length; i++) {
      if (i < dayCount - 1) {
        result.push('-');
        continue;
      }
      let sum = 0;
      for (let j = 0; j < dayCount; j++) {
        sum += data[i - j].close;
      }
      result.push((sum / dayCount).toFixed(2));
    }
    return result;
  };
  
  // 计算MACD数据
  const macdData = useMemo(() => {
    if (!data || data.length === 0) return null;
    const closes = data.map(d => d.close);
    return calculateMACD(closes);
  }, [data]);
  
  // 计算EMA21和趋势判断数据
  const trendData = useMemo(() => {
    if (!data || data.length === 0) return null;
    
    const closes = data.map(d => d.close);
    const ema21 = calculateEMA(closes, 21);
    const ma21 = calculateMA(21);
    
    // 计算每个K线的趋势状态
    const trendStatus = ema21.map((ema, index) => {
      const ma = parseFloat(ma21[index]);
      if (ema === null || isNaN(ma)) return null;
      const close = data[index]?.close;
      if (typeof close !== 'number') return null;
      return ema > ma && close > ma ? 'up' : 'down';
    });
    
    return { ema21, ma21, trendStatus };
  }, [data]);
  
  // 初始化和更新K线图
  useEffect(() => {
    if (!klineChartRef.current || !data || data.length === 0) {
      return;
    }
    
    try {
      const colors = getThemeColors(isDark);
      
      // 只在实例不存在或主题改变时重新初始化
      if (!klineInstance.current) {
        klineInstance.current = echarts.init(klineChartRef.current, isDark ? 'dark' : undefined);
        currentThemeRef.current = isDark;
      } else if (isDark !== currentThemeRef.current) {
        // 如果主题改变，重新初始化
        klineInstance.current.dispose();
        klineInstance.current = echarts.init(klineChartRef.current, isDark ? 'dark' : undefined);
        currentThemeRef.current = isDark;
      }
      
      const dates = data.map(d => d.date);
      const axisLabelInterval = getUnifiedAxisLabelInterval(data.length, zoomRange);
      const zoomWindow = getPinnedZoomWindow(data.length, zoomRange);
      const ohlc = data.map(d => [d.open, d.close, d.low, d.high]);
      const ma5 = calculateMA(5);
      const ma10 = calculateMA(10);
      const ma21 = calculateMA(21);
      const ma30 = calculateMA(30);
      const ma60 = calculateMA(60);
      const ma120 = calculateMA(120);
      const ema9 = calculateEMA(data.map(d => d.close), 9);
      const ema21 = trendData?.ema21 || calculateEMA(data.map(d => d.close), 21);
      const ema60 = calculateEMA(data.map(d => d.close), 60);
      const ema120 = calculateEMA(data.map(d => d.close), 120);
      
      // 根据趋势模式动态生成K线颜色
      let klineItemStyle = {};
      if (trendMode && trendData) {
        // 趋势模式：根据EMA21和MA21关系判断颜色
        klineItemStyle = {
          color: (params: any) => {
            const trend = trendData.trendStatus[params.dataIndex];
            if (trend === 'up') {
              return colors.uptrendColor;
            } else if (trend === 'down') {
              return colors.downtrendColor;
            }
            return data[params.dataIndex].close >= data[params.dataIndex].open
              ? colors.upColor : colors.downColor;
          },
          color0: (params: any) => {
            const trend = trendData.trendStatus[params.dataIndex];
            if (trend === 'up') {
              return colors.uptrendColor;
            } else if (trend === 'down') {
              return colors.downtrendColor;
            }
            return data[params.dataIndex].close >= data[params.dataIndex].open
              ? colors.upColor : colors.downColor;
          },
          borderColor: (params: any) => {
            const trend = trendData.trendStatus[params.dataIndex];
            if (trend === 'up') {
              return colors.uptrendBorderColor;
            } else if (trend === 'down') {
              return colors.downtrendBorderColor;
            }
            return data[params.dataIndex].close >= data[params.dataIndex].open
              ? colors.upBorderColor : colors.downBorderColor;
          },
          borderColor0: (params: any) => {
            const trend = trendData.trendStatus[params.dataIndex];
            if (trend === 'up') {
              return colors.uptrendBorderColor;
            } else if (trend === 'down') {
              return colors.downtrendBorderColor;
            }
            return data[params.dataIndex].close >= data[params.dataIndex].open
              ? colors.upBorderColor : colors.downBorderColor;
          }
        };
      } else {
        // 传统模式：红涨绿跌
        klineItemStyle = {
          color: colors.upColor,
          color0: colors.downColor,
          borderColor: colors.upBorderColor,
          borderColor0: colors.downBorderColor
        };
      }
      
      const compactVisibleNames = data.length >= 120
        ? ['K线', 'EMA9', 'EMA21', 'MA21', 'MA120']
        : ['K线', 'EMA9', 'EMA21', 'MA21'];

      const legendData = compactLineMode
        ? compactVisibleNames
        : trendMode
          ? ['K线', 'EMA9', 'MA21', 'EMA21', 'MA60', 'EMA60', 'MA120', 'EMA120']
          : ['K线', 'MA5', 'MA10', 'EMA9', 'MA21', 'EMA21', 'MA30', 'MA60', 'EMA60', 'MA120', 'EMA120'];

      const legendSelected = legendData.reduce<Record<string, boolean>>((acc, name) => {
        acc[name] = true;
        return acc;
      }, {});

      const series: any[] = [
        {
          name: 'K线',
          type: 'candlestick',
          data: ohlc,
          itemStyle: klineItemStyle
        },
        {
          name: 'EMA9',
          type: 'line',
          data: ema9,
          smooth: true,
          itemStyle: { color: colors.ema9Color },
          lineStyle: { width: 1.8, color: colors.ema9Color },
          symbol: 'none'
        },
        ...(
          trendMode || compactLineMode
            ? []
            : [
                {
                  name: 'MA5',
                  type: 'line',
                  data: ma5,
                  smooth: true,
                  itemStyle: { color: colors.ma5Color },
                  lineStyle: { width: 1, color: colors.ma5Color },
                  symbol: 'none'
                },
                {
                  name: 'MA10',
                  type: 'line',
                  data: ma10,
                  smooth: true,
                  itemStyle: { color: colors.ma10Color },
                  lineStyle: { width: 1, color: colors.ma10Color },
                  symbol: 'none'
                }
              ]
        ),
        {
          name: 'MA21',
          type: 'line',
          data: ma21,
          smooth: true,
          itemStyle: { color: colors.ma20Color },
          lineStyle: { width: 1, color: colors.ma20Color },
          symbol: 'none'
        },
        {
          name: 'EMA21',
          type: 'line',
          data: ema21,
          smooth: true,
          itemStyle: { color: colors.ema20Color },
          lineStyle: { width: 1.5, color: colors.ema20Color, type: 'dotted' },
          symbol: 'none'
        },
        ...(
          trendMode || compactLineMode
            ? []
            : [
                {
                  name: 'MA30',
                  type: 'line',
                  data: ma30,
                  smooth: true,
                  itemStyle: { color: colors.ma30Color },
                  lineStyle: { width: 1, color: colors.ma30Color },
                  symbol: 'none'
                }
              ]
        ),
        {
          name: 'MA60',
          type: 'line',
          data: ma60,
          smooth: true,
          itemStyle: { color: colors.ma60Color },
          lineStyle: { width: 1, color: colors.ma60Color },
          symbol: 'none'
        },
        {
          name: 'EMA60',
          type: 'line',
          data: ema60,
          smooth: true,
          itemStyle: { color: colors.ema60Color },
          lineStyle: { width: 1.5, color: colors.ema60Color, type: 'dotted' },
          symbol: 'none'
        },
        {
          name: 'MA120',
          type: 'line',
          data: ma120,
          smooth: true,
          itemStyle: { color: colors.ma120Color },
          lineStyle: { width: compactLineMode ? 2 : 1.2, color: colors.ma120Color },
          symbol: 'none'
        },
        {
          name: 'EMA120',
          type: 'line',
          data: ema120,
          smooth: true,
          itemStyle: { color: colors.ema120Color },
          lineStyle: { width: 1.5, color: colors.ema120Color, type: 'dotted' },
          symbol: 'none'
        }
      ];

      const filteredSeries = compactLineMode
        ? series.filter((item) => compactVisibleNames.includes(item.name))
        : series;

      const option: echarts.EChartsOption = {
        backgroundColor: colors.background,
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          confine: true,
          backgroundColor: colors.tooltipBg,
          borderColor: colors.tooltipBorder,
          padding: [10, 15],
          extraCssText: 'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); white-space: nowrap;',
          textStyle: { color: colors.text, fontSize: 13 },
          formatter: (params: any) => {
            const dataIndex = params[0].dataIndex;
            const d = data[dataIndex];
            if (!d) return '';
            
            const change = d.close - d.open;
            const changePct = d.open !== 0 ? ((change / d.open) * 100).toFixed(2) : '0.00';
            const changeSign = change >= 0 ? '+' : '';
            const changeColor = change >= 0 ? '#ff0000' : '#00ff00';
            
            // 趋势模式下显示EMA21和趋势判断
            let trendInfo = '';
            if (trendMode && trendData) {
              const ema21Value = trendData.ema21[dataIndex];
              const ma21Value = trendData.ma21[dataIndex];
            const ma60Value = calculateMA(60)[dataIndex];
            const ma120Value = calculateMA(120)[dataIndex];
            const ema60Value = calculateEMA(data.map(d => d.close), 60)[dataIndex];
            const ema120Value = calculateEMA(data.map(d => d.close), 120)[dataIndex];
            const trend = trendData.trendStatus[dataIndex];
            const trendText = trend === 'up' ? '📈 上涨行情' : trend === 'down' ? '📉 下跌行情' : '-';
            const trendColor = trend === 'up' ? '#22c55e' : '#9ca3af';
            
            trendInfo = `
              <div style="border-top: 1px solid #e5e7eb; margin-top: 6px; padding-top: 6px;">
                <div>EMA21: <span style="font-weight: 500; color: ${colors.ema20Color}">${ema21Value ? ema21Value.toFixed(2) : '-'}</span></div>
                <div>MA21: <span style="font-weight: 500; color: ${colors.ma20Color}">${ma21Value !== '-' ? parseFloat(ma21Value).toFixed(2) : '-'}</span></div>
                <div style="display: flex; gap: 8px;">
                  <div>EMA60: <span style="font-weight: 500; color: ${colors.ema60Color}">${ema60Value ? ema60Value.toFixed(2) : '-'}</span></div>
                  <div>MA60: <span style="font-weight: 500; color: ${colors.ma60Color}">${ma60Value !== '-' ? parseFloat(ma60Value).toFixed(2) : '-'}</span></div>
                </div>
                <div style="display: flex; gap: 8px;">
                  <div>EMA120: <span style="font-weight: 500; color: ${colors.ema120Color}">${ema120Value ? ema120Value.toFixed(2) : '-'}</span></div>
                  <div>MA120: <span style="font-weight: 500; color: ${colors.ma120Color}">${ma120Value !== '-' ? parseFloat(ma120Value).toFixed(2) : '-'}</span></div>
                </div>
                <div>趋势: <span style="font-weight: 500; color: ${trendColor}">${trendText}</span></div>
              </div>
            `;
          }
            
            return `
              <div style="padding: 4px 0; line-height: 1.8;">
                <div style="font-weight: bold; margin-bottom: 6px; font-size: 14px;">${stockName || stockCode} · ${d.date}</div>
                <div>开盘: <span style="font-weight: 500;">${d.open.toFixed(2)}</span></div>
                <div>收盘: <span style="font-weight: 500;">${d.close.toFixed(2)}</span></div>
                <div>最高: <span style="font-weight: 500;">${d.high.toFixed(2)}</span></div>
                <div>最低: <span style="font-weight: 500;">${d.low.toFixed(2)}</span></div>
                <div>成交量: <span style="font-weight: 500;">${(d.volume / 10000).toFixed(2)}万</span></div>
                <div style="margin-top: 4px;">
                  涨跌: <span style="color: ${changeColor}; font-weight: 500;">${changeSign}${change.toFixed(2)} (${changePct}%)</span>
                </div>
                ${trendInfo}
              </div>
            `;
          }
        },
        legend: {
          data: legendData,
          selected: legendSelected,
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
          axisLabel: {
            color: colors.textSecondary,
            fontSize: 11,
            interval: axisLabelInterval
          },
          splitLine: { show: false },
          min: 0,
          max: data.length - 1
        },
        yAxis: {
          scale: true,
          position: 'right',
          axisLine: { lineStyle: { color: colors.border }, show: true },
          axisLabel: { color: colors.textSecondary, fontSize: 12 },
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
        series: filteredSeries
      };
      
      klineInstance.current.setOption(option, { replaceMerge: ['series', 'legend'] });
      
    } catch (error) {
      console.error('ECharts渲染失败:', error);
    }
  }, [data, stockCode, stockName, isDark, chartHeights.kline, trendMode, compactLineMode, trendData, calculateMA, zoomRange.start, zoomRange.end]);

  // 设置图表同步的Effect - 监听缩放事件并强制右侧贴边
  useEffect(() => {
    const syncCharts = () => {
      const charts: echarts.ECharts[] = [];
      
      if (klineInstance.current) {
        charts.push(klineInstance.current);
      }
      
      if (indicator1ChartRef.current?.getEchartsInstance?.()) {
        const inst = indicator1ChartRef.current.getEchartsInstance();
        if (inst) charts.push(inst);
      }
      
      if (indicator2ChartRef.current?.getEchartsInstance?.()) {
        const inst = indicator2ChartRef.current.getEchartsInstance();
        if (inst) charts.push(inst);
      }
      
      if (charts.length > 1) {
        console.log('正在同步图表...', charts.length);
        echarts.connect(charts);
      }

      const onDataZoom = (event: any) => {
        if (isSyncingZoomRef.current) return;
        const payload = event?.batch?.[0] || event;
        if (!payload) return;

        const normalized = getZoomRangeFromPayload(payload, data.length, zoomRangeRef.current, data.map((d) => d.date));
        if (areZoomRangesEqual(normalized, zoomRangeRef.current)) return;

        isSyncingZoomRef.current = true;
        zoomRangeRef.current = normalized;
        setZoomRange(normalized);
        applyZoomToCharts(normalized, true);

        setTimeout(() => {
          isSyncingZoomRef.current = false;
        }, 0);
      };

      charts.forEach((chart) => {
        chart.off('datazoom');
        chart.on('datazoom', onDataZoom);
      });

      applyZoomToCharts(zoomRangeRef.current, true);
    };

    // 减少延迟以更快同步图表
    const timer = setTimeout(syncCharts, 100);
    return () => clearTimeout(timer);
  }, [data, alignedPmrData, macdData, chartHeights, indicatorVersion, applyZoomToCharts]);

  useEffect(() => {
    applyZoomToCharts(zoomRange, true);
  }, [zoomRange.start, zoomRange.end, indicatorVersion, zoomRange, applyZoomToCharts]);

  // "回到最新"功能 - 将所有图表缩放到最新数据
  const handleGoToLatest = useCallback(() => {
    const newZoomRange = DEFAULT_ZOOM_RANGE;
    zoomRangeRef.current = newZoomRange;
    setZoomRange(newZoomRange);
    applyZoomToCharts(newZoomRange, true);
  }, [applyZoomToCharts]);

  useEffect(() => {
    if (goToLatestTrigger > 0) {
      handleGoToLatest();
    }
  }, [goToLatestTrigger, handleGoToLatest]);

  // 组件卸载时销毁实例
  useEffect(() => {
    return () => {
      if (klineInstance.current) {
        klineInstance.current.dispose();
        klineInstance.current = null;
      }
    };
  }, []);
  
  // 响应式调整 - 使用 ResizeObserver 监听容器大小变化
  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver(() => {
      klineInstance.current?.resize();
      
      // 同时也调整指标图表的大小
      if (indicator1ChartRef.current?.getEchartsInstance?.()) {
        indicator1ChartRef.current.getEchartsInstance()?.resize();
      }
      if (indicator2ChartRef.current?.getEchartsInstance?.()) {
        indicator2ChartRef.current.getEchartsInstance()?.resize();
      }
    });

    resizeObserver.observe(containerRef.current);
    
    // 同时保留 window resize 作为备用
    const handleWindowResize = () => {
      klineInstance.current?.resize();
      if (indicator1ChartRef.current?.getEchartsInstance?.()) {
        indicator1ChartRef.current.getEchartsInstance()?.resize();
      }
      if (indicator2ChartRef.current?.getEchartsInstance?.()) {
        indicator2ChartRef.current.getEchartsInstance()?.resize();
      }
    };
    
    window.addEventListener('resize', handleWindowResize);
    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', handleWindowResize);
    };
  }, []);
  
  return (
    <div 
      ref={containerRef}
      style={{ 
        width: '100%', 
        height,
        backgroundColor: isDark ? '#0a0a0a' : '#ffffff',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}
    >
      {/* 趋势模式说明 - 悬浮在图表左上角 */}
      {trendMode && (
        <div style={{
          position: 'absolute',
          top: '85px',
          left: '20px',
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          padding: '6px 10px',
          borderRadius: '4px',
          backgroundColor: isDark ? 'rgba(0, 0, 0, 0.6)' : 'rgba(255, 255, 255, 0.8)',
          border: `1px solid ${isDark ? '#333' : '#ddd'}`,
          fontSize: '11px',
          color: isDark ? '#9ca3af' : '#6b7280',
          pointerEvents: 'none'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ 
              display: 'inline-block', 
              width: '10px', 
              height: '10px', 
              backgroundColor: '#22c55e',
              border: '1px solid #22c55e'
            }}></span>
            <span>上涨 (EMA21 &gt; MA21 且 收盘 &gt; MA21)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ 
              display: 'inline-block', 
              width: '10px', 
              height: '10px', 
              backgroundColor: '#000000',
              border: '1px solid #ffffff'
            }}></span>
            <span>下跌 (其余情况)</span>
          </div>
        </div>
      )}

      {/* K线图 - 使用flex分配高度 */}
      <div 
        ref={klineChartRef}
        style={{ 
          width: '100%', 
          flex: `${chartHeights.kline} 0 0`,
          minHeight: '200px'
        }}
      />
      
      {/* 可拖拽分隔条 */}
      <HorizontalResizableDivider onResize={handleKlineIndicator1Resize} />
      
      {/* 指标容器1 */}
      <div 
        style={{ 
          width: '100%', 
          flex: `${chartHeights.indicator1} 0 0`,
          minHeight: '60px'
        }}
      >
        <IndicatorContainer
          volumeData={data}
          macdData={macdData || undefined}
          pmrData={alignedPmrData || undefined}
          forceIndexData={forceIndexData || undefined}
          dates={data?.map(d => d.date)}
          zoomRange={zoomRange}
          defaultIndicator="volume"
          chartRef={indicator1ChartRef}
          onIndicatorChange={() => setIndicatorVersion(v => v + 1)}
        />
      </div>
      
      {/* 可拖拽分隔条 */}
      <HorizontalResizableDivider onResize={handleIndicator1Indicator2Resize} />
      
      {/* 指标容器2 */}
      <div 
        style={{ 
          width: '100%', 
          flex: `${chartHeights.indicator2} 0 0`,
          minHeight: '60px'
        }}
      >
        <IndicatorContainer
          volumeData={data}
          macdData={macdData || undefined}
          pmrData={alignedPmrData || undefined}
          forceIndexData={forceIndexData || undefined}
          dates={data?.map(d => d.date)}
          zoomRange={zoomRange}
          defaultIndicator="macd"
          chartRef={indicator2ChartRef}
          onIndicatorChange={() => setIndicatorVersion(v => v + 1)}
        />
      </div>
    </div>
  );
}
