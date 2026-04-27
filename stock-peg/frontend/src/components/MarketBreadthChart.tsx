import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { useQuery } from '@tanstack/react-query';
import { marketApi } from '../services/api';
import { useTheme } from '../contexts/ThemeContext';
import { Loader2, Maximize2 } from 'lucide-react';

interface MarketBreadthChartProps {
  height?: number;
  showExpandButton?: boolean;
  onExpand?: () => void;
}

export default function MarketBreadthChart({
  height = 210,
  showExpandButton = false,
  onExpand,
}: MarketBreadthChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const currentThemeRef = useRef<boolean>(isDark);

  // 获取上证指数历史数据
  const { data: shIndexData, isLoading: isLoadingSH } = useQuery({
    queryKey: ['sh-index-history'],
    queryFn: () => marketApi.getSHIndexHistory(60),
    refetchInterval: 60000, // 每分钟刷新
  });

  // 获取市场情绪历史数据
  const { data: sentimentData, isLoading: isLoadingSentiment } = useQuery({
    queryKey: ['market-sentiment-history'],
    queryFn: () => marketApi.getMarketSentimentHistory(60),
    refetchInterval: 60000,
  });

  const isLoading = isLoadingSH || isLoadingSentiment;

  useEffect(() => {
    if (!chartRef.current || !shIndexData?.history) return;

    const colors = {
      background: isDark ? '#0a0a0a' : '#ffffff',
      text: isDark ? '#e8e8e8' : '#0f172a',
      textSecondary: isDark ? '#808080' : '#64748b',
      border: isDark ? '#1a1a1a' : '#e2e8f0',
      splitLine: isDark ? '#1a1a1a' : '#e2e8f0',
      tooltipBg: isDark ? 'rgba(0, 0, 0, 0.95)' : 'rgba(255, 255, 255, 0.95)',
      tooltipBorder: isDark ? '#1a1a1a' : '#e2e8f0',
      indexColor: '#3b82f6', // 蓝色 - 上证指数
      breadthColor: '#ef4444', // 红色 - 下跌股票数
    };

    // 创建日期映射（sentimentData可能为空或数据不全）
    const sentimentMap = new Map<string, any>();
    if (sentimentData?.history) {
      (sentimentData.history as any[]).forEach((item: any) => {
        sentimentMap.set(item.date, item);
      });
    }

    // 合并数据（共享同一时间轴：以上证指数日期为准）
    const mergedData = (shIndexData.history as any[]).map((item: any) => {
      const sentiment: any | undefined = sentimentMap.get(item.date);
      const upCount = sentiment?.up_count ?? null;
      const flatCount = sentiment?.flat_count ?? null;
      const totalCount = sentiment?.total_count ?? null;
      const downCount = sentiment?.down_count ?? (
        upCount !== null && totalCount !== null
          ? totalCount - upCount - (flatCount ?? 0)
          : null
      );
      return {
        date: item.date,
        close: item.close,
        market_breadth: sentiment?.market_breadth ?? null,
        up_count: upCount,
        flat_count: flatCount,
        total_count: totalCount,
        down_count: downCount,
      };
    });

    if (mergedData.length === 0) return;

    // 统计有情绪数据的天数
    const sentimentDataCount = mergedData.filter(d => d.down_count !== null).length;
    
    // 如果情绪数据少于上证指数数据的一半，显示警告
    if (sentimentDataCount < mergedData.length * 0.5) {
      console.warn(`市场情绪数据不足: ${sentimentDataCount}/${mergedData.length} 天`);
    }

    const dates = mergedData.map((d: any) => d.date);
    const indexValues = mergedData.map((d: any) => d.close);
    const downCountValues = mergedData.map((d: any) => d.down_count);
    const validDownCountValues = downCountValues.filter((value: number | null) => Number.isFinite(value)) as number[];
    const downCountAxisMax = validDownCountValues.length > 0 ? Math.max(...validDownCountValues) * 1.1 : 5000;
    const validIndexValues = indexValues.filter((value: number) => Number.isFinite(value));
    const rawIndexMin = validIndexValues.length > 0 ? Math.min(...validIndexValues) : 0;
    const rawIndexMax = validIndexValues.length > 0 ? Math.max(...validIndexValues) : 0;
    const indexPadding = Math.max(10, (rawIndexMax - rawIndexMin) * 0.08);
    const indexAxisMin = Math.max(0, Math.floor(rawIndexMin - indexPadding));
    const indexAxisMax = Math.ceil(rawIndexMax + indexPadding);

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
        textStyle: { color: colors.text, fontSize: 11 },
        formatter: (params: any) => {
          if (!params || params.length === 0) return '';
          const dataIndex = params[0].dataIndex;
          const data = mergedData[dataIndex];
          if (!data) return '';

          return `
            <div style="font-weight: bold; margin-bottom: 4px;">${data.date}</div>
            <div>上证指数: <span style="color: ${colors.indexColor}; font-weight: 500;">${data.close.toFixed(2)}</span></div>
            <div>下跌股票数: <span style="color: ${colors.breadthColor}; font-weight: 500;">${data.down_count !== null ? data.down_count : '--'}</span></div>
            <div style="font-size: 10px; color: ${colors.textSecondary}; margin-top: 2px;">
              ${data.up_count !== null && data.total_count !== null ? `上涨 ${data.up_count} / 下跌 ${data.down_count} / 总计 ${data.total_count}` : '当日下跌数据缺失'}
            </div>
          `;
        },
      },
      legend: {
        data: ['上证指数', '下跌股票数'],
        top: 8,
        textStyle: { color: colors.text, fontSize: 10 },
        itemWidth: 15,
        itemHeight: 10,
      },
      grid: {
        left: '8%',
        right: '8%',
        top: 34,
        bottom: 50,
      },
      xAxis: {
        type: 'category',
        data: dates,
        boundaryGap: false,
        axisLine: { lineStyle: { color: colors.border } },
        axisLabel: {
          color: colors.textSecondary,
          fontSize: 9,
          interval: 'auto',
          rotate: 0,
        },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax',
      },
      axisPointer: {
        link: [{ xAxisIndex: 'all' }]
      },
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: 0,
          start: 45,
          end: 100,
          zoomLock: false,
        },
        {
          type: 'slider',
          xAxisIndex: 0,
          start: 45,
          end: 100,
          height: 14,
          bottom: 20,
          brushSelect: false,
          borderColor: colors.border,
          backgroundColor: isDark ? '#111111' : '#f8fafc',
          fillerColor: isDark ? 'rgba(148, 163, 184, 0.25)' : 'rgba(148, 163, 184, 0.3)',
          handleStyle: {
            color: isDark ? '#94a3b8' : '#64748b',
            borderColor: isDark ? '#94a3b8' : '#64748b',
          },
          moveHandleStyle: {
            color: isDark ? '#94a3b8' : '#64748b',
          },
          textStyle: {
            color: colors.textSecondary,
            fontSize: 9,
          },
        },
      ],
      yAxis: [
        {
          type: 'value',
          name: '上证指数',
          position: 'left',
          min: indexAxisMin,
          max: indexAxisMax,
          nameTextStyle: {
            color: colors.indexColor,
            fontSize: 9,
          },
          axisLine: { lineStyle: { color: colors.indexColor }, show: true },
          axisLabel: {
            color: colors.indexColor,
            fontSize: 9,
            formatter: (value: number) => value.toFixed(0),
          },
          splitLine: { lineStyle: { color: colors.splitLine } },
        },
        {
          type: 'value',
          name: '下跌股票数',
          position: 'right',
          min: 0,
          max: downCountAxisMax,
          nameTextStyle: {
            color: colors.breadthColor,
            fontSize: 9,
          },
          axisLine: { lineStyle: { color: colors.breadthColor }, show: true },
          axisLabel: {
            color: colors.breadthColor,
            fontSize: 9,
            formatter: '{value}',
          },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: '上证指数',
          type: 'line',
          yAxisIndex: 0,
          data: indexValues,
          lineStyle: { width: 1.5, color: colors.indexColor },
          itemStyle: { color: colors.indexColor },
          symbol: 'none',
          smooth: true,
          connectNulls: false,
        },
        {
          name: '下跌股票数',
          type: 'line',
          yAxisIndex: 1,
          data: downCountValues,
          lineStyle: { width: 1.5, color: colors.breadthColor },
          itemStyle: { color: colors.breadthColor },
          symbol: 'none',
          smooth: true,
          connectNulls: false,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: `${colors.breadthColor}40` },
              { offset: 1, color: `${colors.breadthColor}05` },
            ]),
          },
        },
      ],
    };

    chartInstance.current.setOption(option);
  }, [shIndexData, sentimentData, isDark]);

  useEffect(() => {
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, []);

  if (isLoading) {
    return (
      <div className={`p-3 rounded border ${
        isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center justify-center py-8">
          <Loader2 size={16} className={`animate-spin ${isDark ? 'text-blue-400' : 'text-blue-500'}`} />
          <span className={`text-xs ml-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            加载中...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-3 rounded border relative ${
      isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
    }`}>
      {showExpandButton && (
        <button
          type="button"
          onClick={onExpand}
          className={`absolute right-2 top-2 z-10 p-1.5 rounded transition-colors ${
            isDark
              ? 'bg-[#0f0f0f]/90 border border-[#2a2a2a] text-gray-300 hover:text-white hover:bg-[#1a1a1a]'
              : 'bg-white/90 border border-gray-200 text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
          title="查看放大图"
        >
          <Maximize2 size={14} />
        </button>
      )}
      <div 
        ref={chartRef} 
        style={{ width: '100%', height: `${height}px` }}
      />
      {/* 数据不足提示 */}
      {sentimentData?.history && sentimentData.history.length < 7 && (
        <div className={`absolute bottom-4 left-1/2 transform -translate-x-1/2 px-3 py-1.5 rounded text-xs ${
          isDark ? 'bg-yellow-900/20 text-yellow-300 border border-yellow-700/50' : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
        }`}>
          市场情绪数据积累中（当前{sentimentData.history.length}天，建议等待7天以上）
        </div>
      )}
    </div>
  );
}
