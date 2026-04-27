import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { marketApi } from '../services/api';
import { Activity, TrendingUp, TrendingDown, BarChart3, Loader2, X, Maximize2, Scale, Gauge, DollarSign, Table } from 'lucide-react';
import * as echarts from 'echarts';
import CollapsibleCard from './CollapsibleCard';
import MarketBreadthChart from './MarketBreadthChart';
import { useTheme } from '../contexts/ThemeContext';

interface TurnoverPoint {
  date: string;
  amount: number;
}

interface MarketFundFlowPoint {
  date: string;
  amount: number;
  main_net_inflow: number;
  main_net_inflow_pct: number;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function parseFlexibleNumber(value: unknown) {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const normalized = trimmed.replace(/,/g, '').replace(/%/g, '');
  const numeric = Number(normalized.replace(/[^\d.-]/g, ''));
  if (!Number.isFinite(numeric)) return null;
  if (trimmed.includes('万亿')) return numeric * 1000000000000;
  if (trimmed.includes('亿')) return numeric * 100000000;
  if (trimmed.includes('万元') || trimmed.includes('万')) return numeric * 10000;
  return numeric;
}

function normalizeMoneyToYuan(value: number) {
  const abs = Math.abs(value);
  if (!Number.isFinite(value)) return 0;
  if (abs >= 100000000) return value;
  if (abs >= 10000) return value * 10000;
  return value * 100000000;
}

function normalizeDateText(value: unknown) {
  if (value == null) return '';
  const text = String(value).trim();
  if (!text) return '';
  const digitsOnly = text.replace(/[^\d]/g, '');
  if (digitsOnly.length >= 8) {
    const y = digitsOnly.slice(0, 4);
    const m = digitsOnly.slice(4, 6);
    const d = digitsOnly.slice(6, 8);
    return `${y}-${m}-${d}`;
  }
  const date = new Date(text);
  if (!Number.isNaN(date.getTime())) {
    const y = date.getFullYear();
    const m = `${date.getMonth() + 1}`.padStart(2, '0');
    const d = `${date.getDate()}`.padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
  return '';
}

function getDateTimestamp(value: string) {
  if (!value) return Number.NEGATIVE_INFINITY;
  const date = new Date(value);
  if (!Number.isNaN(date.getTime())) return date.getTime();
  const normalized = value.replace(/[^\d]/g, '');
  if (normalized.length >= 8) {
    const formatted = `${normalized.slice(0, 4)}-${normalized.slice(4, 6)}-${normalized.slice(6, 8)}`;
    const retry = new Date(formatted);
    if (!Number.isNaN(retry.getTime())) return retry.getTime();
  }
  return Number.NEGATIVE_INFINITY;
}

function formatAmountYi(value: number | null | undefined) {
  if (!Number.isFinite(value as number) || !value) return '--';
  const yi = (value as number) / 100000000; // 转换为亿
  if (yi >= 10000) {
    // 大于1万亿,显示万亿单位
    return `${(yi / 10000).toFixed(2)}万亿`;
  }
  return `${yi.toFixed(2)}亿`;
}

function TurnoverAmountChart({
  data,
  isDark,
  height = 240,
}: {
  data: TurnoverPoint[];
  isDark: boolean;
  height?: number;
}) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);
  const currentThemeRef = useRef<boolean>(isDark);

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    const colors = {
      background: isDark ? '#0a0a0a' : '#ffffff',
      text: isDark ? '#e8e8e8' : '#0f172a',
      textSecondary: isDark ? '#808080' : '#64748b',
      border: isDark ? '#1a1a1a' : '#e2e8f0',
      splitLine: isDark ? '#1a1a1a' : '#e2e8f0',
      tooltipBg: isDark ? 'rgba(0, 0, 0, 0.95)' : 'rgba(255, 255, 255, 0.95)',
      tooltipBorder: isDark ? '#1a1a1a' : '#e2e8f0',
      upColor: '#ef4444',   // 红色 - 成交额增加
      downColor: '#22c55e', // 绿色 - 成交额减少
      rateColor: isDark ? '#f97316' : '#ea580c', // 橙色 - 变化率曲线
    };

    const dates = data.map((item) => item.date);
    const amountValues = data.map((item) => item.amount);
    
    // 计算成交额变化率: (当天-前一天)/前一天
    const changeRateValues = amountValues.map((value, index) => {
      if (index === 0) return null;
      const prevValue = amountValues[index - 1];
      if (!prevValue || prevValue === 0) return null;
      return ((value - prevValue) / prevValue) * 100; // 转为百分比
    });
    
    // 为每个柱子设置颜色: 比前一天增加用红色,减少用绿色
    const barColors = amountValues.map((value, index) => {
      if (index === 0) return colors.upColor; // 第一天默认红色
      const prevValue = amountValues[index - 1];
      return value >= prevValue ? colors.upColor : colors.downColor;
    });

    if (!chartInstanceRef.current) {
      chartInstanceRef.current = echarts.init(chartRef.current, isDark ? 'dark' : undefined);
      currentThemeRef.current = isDark;
    } else if (isDark !== currentThemeRef.current) {
      chartInstanceRef.current.dispose();
      chartInstanceRef.current = echarts.init(chartRef.current, isDark ? 'dark' : undefined);
      currentThemeRef.current = isDark;
    }

    chartInstanceRef.current.setOption({
      backgroundColor: colors.background,
      tooltip: {
        trigger: 'axis',
        confine: true,
        backgroundColor: colors.tooltipBg,
        borderColor: colors.tooltipBorder,
        textStyle: { color: colors.text, fontSize: 11 },
        formatter: (params: any) => {
          if (!params || params.length === 0) return '';
          const amountItem = params.find((item: any) => item.seriesName === '成交额');
          const rateItem = params.find((item: any) => item.seriesName === '变化率');
          const dataIndex = amountItem?.dataIndex || 0;
          const currentAmount = amountItem?.data || 0;
          const prevAmount = dataIndex > 0 ? amountValues[dataIndex - 1] : null;
          const changeRate = rateItem?.data;
          
          let changeText = '';
          if (dataIndex > 0 && prevAmount !== null) {
            const change = currentAmount - prevAmount;
            const changePercent = ((change / prevAmount) * 100).toFixed(2);
            const changeYi = (change / 100000000).toFixed(2);
            changeText = `
              <div>环比变化: <span style="color:${currentAmount >= prevAmount ? colors.upColor : colors.downColor};font-weight:500;">
                ${currentAmount >= prevAmount ? '+' : ''}${changeYi}亿 (${changePercent}%)
              </span></div>
            `;
          }
          
          return `
            <div style="font-weight:600;margin-bottom:4px;">${params[0].axisValue}</div>
            <div>成交额: <span style="color:${currentAmount >= (prevAmount || 0) ? colors.upColor : colors.downColor};font-weight:500;">
              ${formatAmountYi(currentAmount)}
            </span></div>
            ${changeText}
            ${changeRate !== null ? `<div>变化率: <span style="color:${colors.rateColor};font-weight:500;">${changeRate.toFixed(2)}%</span></div>` : ''}
          `;
        },
      },
      legend: {
        data: ['成交额', '变化率'],
        top: 6,
        textStyle: { color: colors.text, fontSize: 10 },
        itemWidth: 14,
        itemHeight: 8,
      },
      grid: {
        left: '8%',
        right: '12%',
        top: 34,
        bottom: 46,
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: colors.border } },
        axisLabel: { color: colors.textSecondary, fontSize: 9 },
      },
      yAxis: [
        {
          type: 'value',
          name: '亿元',
          position: 'left',
          axisLine: { lineStyle: { color: colors.border }, show: true },
          axisLabel: {
            color: colors.textSecondary,
            fontSize: 9,
            formatter: (value: number) => (value / 100000000).toFixed(0),
          },
          splitLine: { lineStyle: { color: colors.splitLine } },
        },
        {
          type: 'value',
          name: '变化率%',
          position: 'right',
          nameTextStyle: { color: colors.textSecondary, fontSize: 9 },
          axisLine: { lineStyle: { color: colors.rateColor }, show: true },
          axisLabel: {
            color: colors.rateColor,
            fontSize: 9,
            formatter: (value: number) => value.toFixed(0) + '%',
          },
          splitLine: { show: false },
        },
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: 0,
          start: 45,
          end: 100,
        },
      ],
      series: [
        {
          name: '成交额',
          type: 'bar',
          yAxisIndex: 0,
          data: amountValues.map((value, index) => ({
            value,
            itemStyle: { color: barColors[index] },
          })),
          barMaxWidth: 18,
        },
        {
          name: '变化率',
          type: 'line',
          yAxisIndex: 1,
          data: changeRateValues,
          smooth: true,
          symbol: 'none',
          lineStyle: { color: colors.rateColor, width: 2 },
        },
      ],
    });
    const handleResize = () => {
      chartInstanceRef.current?.resize();
    };
    requestAnimationFrame(handleResize);
    const resizeTimer = window.setTimeout(handleResize, 120);
    window.addEventListener('resize', handleResize);
    return () => {
      window.clearTimeout(resizeTimer);
      window.removeEventListener('resize', handleResize);
    };
  }, [data, isDark]);

  useEffect(() => {
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.dispose();
        chartInstanceRef.current = null;
      }
    };
  }, []);

  if (data.length === 0) {
    return (
      <div className={`p-3 rounded border text-xs ${
        isDark ? 'bg-[#1a1a1a] border-[#2a2a2a] text-gray-400' : 'bg-white border-gray-200 text-gray-600'
      }`}>
        暂无成交额历史数据
      </div>
    );
  }

  return <div ref={chartRef} style={{ width: '100%', height: `${height}px` }} />;
}

export default function MarketSentimentCard() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const queryClient = useQueryClient();
  const [wsConnected, setWsConnected] = useState<boolean>(() => Boolean((window as any).__stockPegWsConnected));
  const lastInvalidateRef = useRef(0);
  const [showExpandedModal, setShowExpandedModal] = useState(false);

  useEffect(() => {
    const onConnected = () => setWsConnected(true);
    const onDisconnected = () => setWsConnected(false);
    window.addEventListener('websocket-connected', onConnected);
    window.addEventListener('websocket-disconnected', onDisconnected);
    return () => {
      window.removeEventListener('websocket-connected', onConnected);
      window.removeEventListener('websocket-disconnected', onDisconnected);
    };
  }, []);

  useEffect(() => {
    const invalidate = () => {
      const now = Date.now();
      if (now - lastInvalidateRef.current < 15000) return;
      lastInvalidateRef.current = now;
      queryClient.invalidateQueries({ queryKey: ['market-sentiment'] });
    };

    const onMessage = (event: Event) => {
      const message = (event as CustomEvent).detail;
      const messageType = message?.type;
      if (!messageType) return;
      if (
        messageType === 'market_sentiment_updated' ||
        messageType === 'market_data_updated' ||
        messageType === 'quote' ||
        messageType === 'quote_updated' ||
        messageType === 'background_update_progress'
      ) {
        invalidate();
      }
    };

    window.addEventListener('websocket-message', onMessage);
    window.addEventListener('market-sentiment-updated', invalidate);
    return () => {
      window.removeEventListener('websocket-message', onMessage);
      window.removeEventListener('market-sentiment-updated', invalidate);
    };
  }, [queryClient]);

  const { data: sentiment, isLoading, isFetching, isError, error, refetch } = useQuery({
    queryKey: ['market-sentiment'],
    queryFn: marketApi.getMarketSentiment,
    refetchInterval: wsConnected ? false : 60000,
  });

  const { data: shIndexKlineData } = useQuery({
    queryKey: ['sh-index-kline-turnover', 60],
    queryFn: () => marketApi.getIndexKline('000001', 'day', 60),
    enabled: showExpandedModal,
    refetchInterval: wsConnected ? false : 60000,
  });

  const { data: marketFundFlowData } = useQuery({
    queryKey: ['market-fund-flow', 20],
    queryFn: () => marketApi.getMarketFundFlow(20),
    enabled: showExpandedModal,
    refetchInterval: wsConnected ? false : 120000, // 2分钟更新一次
  });

  const total_count = sentiment?.total_count ?? 0;
  const up_count = sentiment?.up_count ?? 0;
  const down_count = sentiment?.down_count ?? 0;
  const flat_count = sentiment?.flat_count ?? 0;
  const limit_up = sentiment?.limit_up ?? 0;
  const limit_down = sentiment?.limit_down ?? 0;
  const market_breadth = sentiment?.market_breadth ?? 0;
  const avg_change_pct = sentiment?.avg_change_pct ?? 0;

  const upDownRatio = down_count > 0 ? up_count / down_count : (up_count > 0 ? up_count : 0);
  const limitUpDownRatio = limit_down > 0 ? limit_up / limit_down : (limit_up > 0 ? limit_up : 0);
  const breadthValue = Number(market_breadth ?? 0);
  const avgChangeValue = Number(avg_change_pct ?? 0);

  const fearGreedIndex = useMemo(() => {
    const breadthScore = clamp((breadthValue - 30) * 2.5, 0, 100);
    const avgChangeScore = clamp((avgChangeValue + 2) * 25, 0, 100);
    const upDownScore = clamp((upDownRatio - 0.5) * 60, 0, 100);
    const limitScore = clamp((limitUpDownRatio - 0.5) * 55, 0, 100);
    const score = breadthScore * 0.35 + avgChangeScore * 0.25 + upDownScore * 0.2 + limitScore * 0.2;
    return Math.round(clamp(score, 0, 100));
  }, [breadthValue, avgChangeValue, upDownRatio, limitUpDownRatio]);

  const fearGreedLabel = fearGreedIndex >= 70
    ? '贪婪偏热'
    : fearGreedIndex >= 55
      ? '偏乐观'
      : fearGreedIndex >= 45
        ? '中性'
        : fearGreedIndex >= 30
          ? '偏谨慎'
          : '恐惧';

  const turnoverSeries = useMemo<TurnoverPoint[]>(() => {
    const raw = (shIndexKlineData?.klines || []) as any[];
    return raw
      .map((item) => {
        const close = Number(item.close ?? item.c ?? item.收盘 ?? 0);
        const volume = Number(item.volume ?? item.vol ?? item.成交量 ?? 0);
        const rawAmount = Number(item.amount ?? item.turnover ?? item.total_amount ?? item.成交额 ?? 0);
        const amount = rawAmount > 0 ? rawAmount : (volume > 0 && close > 0 ? volume * close : 0);
        return {
          date: String(item.date || item.trade_date || item.datetime || item.日期 || ''),
          amount,
        };
      })
      .filter((item) => item.date && Number.isFinite(item.amount) && item.amount > 0);
  }, [shIndexKlineData]);

  const currentTurnover = turnoverSeries.length > 0 ? turnoverSeries[turnoverSeries.length - 1].amount : null;
  const recentTurnoverWindow = turnoverSeries.slice(-20);
  const avgTurnover20 = recentTurnoverWindow.length > 0
    ? recentTurnoverWindow.reduce((sum, item) => sum + item.amount, 0) / recentTurnoverWindow.length
    : null;
  const turnoverRatio = currentTurnover && avgTurnover20 && avgTurnover20 > 0 ? currentTurnover / avgTurnover20 : null;

  // 处理市场净流入数据
  const marketFundFlowSeries = useMemo<MarketFundFlowPoint[]>(() => {
    const raw = (marketFundFlowData?.flows || []) as any[];
    return raw
      .map((item) => ({
        date: normalizeDateText(item.date),
        amount: normalizeMoneyToYuan(parseFlexibleNumber(item.amount) ?? 0),
        main_net_inflow: normalizeMoneyToYuan(parseFlexibleNumber(item.main_net_inflow) ?? 0),
        main_net_inflow_pct: parseFlexibleNumber(item.main_net_inflow_pct) ?? 0,
      }))
      .filter((item) => item.date && Number.isFinite(item.amount) && item.amount > 0)
      .sort((a, b) => getDateTimestamp(b.date) - getDateTimestamp(a.date));
  }, [marketFundFlowData]);

  // 计算不同时间段的净流入汇总
  const fundFlowSummary = useMemo(() => {
    if (marketFundFlowSeries.length === 0) return null;

    const periods = [
      { label: '20天', days: 20 },
      { label: '10天', days: 10 },
      { label: '5天', days: 5 },
      { label: '3天', days: 3 },
      { label: '2天', days: 2 },
      { label: '1天', days: 1 },
    ];

    return periods.map(({ label, days }) => {
      const data = marketFundFlowSeries.slice(0, Math.min(days, marketFundFlowSeries.length));
      const totalInflow = data.reduce((sum, item) => sum + item.main_net_inflow, 0);
      const totalAmount = data.reduce((sum, item) => sum + item.amount, 0);
      const avgInflowPct = data.length > 0 
        ? data.reduce((sum, item) => sum + item.main_net_inflow_pct, 0) / data.length 
        : 0;

      return {
        label,
        days,
        totalInflow,
        totalAmount,
        avgInflowPct,
        latestDate: data[0]?.date || '--',
        latestAmount: data[0]?.amount || 0,
      };
    });
  }, [marketFundFlowSeries]);

  const fallbackMarketTurnover = useMemo(() => {
    if (fundFlowSummary) return null;
    const raw = (marketFundFlowData?.flows || []) as any[];
    let fallbackAmount: number | null = null;
    for (const item of raw) {
      const parsed = parseFlexibleNumber(item?.amount);
      if (parsed == null) continue;
      const normalized = normalizeMoneyToYuan(parsed);
      if (normalized > 0) {
        fallbackAmount = normalized;
        break;
      }
    }
    if (!fallbackAmount && currentTurnover && currentTurnover > 0) {
      fallbackAmount = currentTurnover;
    }
    if (!fallbackAmount) return null;
    const now = new Date();
    const today = `${now.getFullYear()}-${`${now.getMonth() + 1}`.padStart(2, '0')}-${`${now.getDate()}`.padStart(2, '0')}`;
    const time = now.toLocaleTimeString('zh-CN', { hour12: false });
    return { date: today, time, amount: fallbackAmount };
  }, [fundFlowSummary, marketFundFlowData, currentTurnover]);

  const getAssessmentTone = (level: 'positive' | 'neutral' | 'negative') => {
    if (level === 'positive') return isDark ? 'text-emerald-300' : 'text-emerald-700';
    if (level === 'negative') return isDark ? 'text-rose-300' : 'text-rose-700';
    return isDark ? 'text-amber-300' : 'text-amber-700';
  };

  const assessments = [
    {
      metric: '涨跌家数比',
      value: `${upDownRatio.toFixed(2)} : 1`,
      standard: '> 1.20 偏强；0.85-1.20 中性；< 0.85 偏弱',
      conclusion: upDownRatio > 1.2 ? '上涨家数明显占优，做多扩散较强' : upDownRatio >= 0.85 ? '多空家数接近平衡，处于震荡状态' : '下跌家数占优，短线情绪偏弱',
      level: upDownRatio > 1.2 ? 'positive' as const : upDownRatio >= 0.85 ? 'neutral' as const : 'negative' as const,
    },
    {
      metric: '涨停/跌停家数比',
      value: `${limitUpDownRatio.toFixed(2)} : 1`,
      standard: '> 1.50 偏强；0.80-1.50 中性；< 0.80 偏弱',
      conclusion: limitUpDownRatio > 1.5 ? '涨停效应占优，短线风险偏好较高' : limitUpDownRatio >= 0.8 ? '涨跌停情绪中性，博弈平衡' : '跌停压力偏重，风险偏好不足',
      level: limitUpDownRatio > 1.5 ? 'positive' as const : limitUpDownRatio >= 0.8 ? 'neutral' as const : 'negative' as const,
    },
    {
      metric: '恐惧贪婪指数',
      value: `${fearGreedIndex} / 100`,
      standard: '> 60 偏贪婪；40-60 中性；< 40 偏恐惧',
      conclusion: fearGreedIndex > 60 ? '市场风险偏好抬升，但需注意追涨过热' : fearGreedIndex >= 40 ? '情绪处于中性区，交易风格偏均衡' : '防御情绪占优，资金偏谨慎',
      level: fearGreedIndex > 60 ? 'positive' as const : fearGreedIndex >= 40 ? 'neutral' as const : 'negative' as const,
    },
    {
      metric: '成交额活跃度',
      value: turnoverRatio ? `${(turnoverRatio * 100).toFixed(1)}%（相对20日均额）` : '--',
      standard: '> 110% 放量；90-110% 常态；< 90% 缩量',
      conclusion: !turnoverRatio
        ? '成交额数据不足，暂不判定'
        : turnoverRatio > 1.1
          ? '出现放量，趋势延续概率提升'
          : turnoverRatio >= 0.9
            ? '成交额接近日常均值，驱动强度一般'
            : '成交额缩量，资金观望情绪偏强',
      level: !turnoverRatio ? 'neutral' as const : turnoverRatio > 1.1 ? 'positive' as const : turnoverRatio >= 0.9 ? 'neutral' as const : 'negative' as const,
    },
  ];

  if (isLoading) {
    return (
      <CollapsibleCard
        title="市场情绪"
        icon={<Activity size={16} className="text-pink-600" />}
        defaultOpen={true}
      >
        <div className="p-5">
          <div className={`rounded border flex items-center justify-center gap-2.5 py-6 ${
            isDark ? 'bg-[#141414] border-[#2a2a2a]' : 'bg-gray-50 border-gray-200'
          }`}>
            <Loader2 size={14} className={`animate-spin ${isDark ? 'text-pink-400' : 'text-pink-600'}`} />
            <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              {isFetching ? '加载市场情绪中...' : '等待市场情绪数据...'}
            </span>
          </div>
        </div>
      </CollapsibleCard>
    );
  }

  if (isError) {
    const errorData = error as any;
    const isInsufficientData = errorData?.response?.data?.detail?.error === 'insufficient_data';
    const errorDetail = errorData?.response?.data?.detail;

    return (
      <CollapsibleCard
        title="市场情绪"
        icon={<Activity size={16} className="text-pink-600" />}
        defaultOpen={true}
      >
        <div className="p-5">
          <div className={`rounded border py-4 px-3 space-y-3 ${
            isDark ? 'bg-[#141414] border-[#2a2a2a]' : 'bg-gray-50 border-gray-200'
          }`}>
            {isInsufficientData ? (
              <>
                <div className={`text-xs font-medium ${isDark ? 'text-orange-300' : 'text-orange-600'}`}>
                  ⚠️ 数据不足，无法提供市场情绪分析
                </div>
                <div className={`text-xs space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <div>系统需要至少 <strong className={isDark ? 'text-orange-300' : 'text-orange-600'}>5000只</strong> A股股票数据</div>
                  {errorDetail?.details && (
                    <div className={`text-[11px] mt-2 p-2 rounded ${isDark ? 'bg-[#1a1a1a]' : 'bg-white'}`}>
                      <div>缓存数据: {errorDetail.details.cache_count || 0} 只</div>
                      <div>本地数据: {errorDetail.details.local_count || 0} 只</div>
                      <div className="mt-1 text-orange-500">
                        {errorDetail.suggestion}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <div className={`text-xs ${isDark ? 'text-orange-300' : 'text-orange-600'}`}>
                  市场情绪接口请求失败
                </div>
                <div className={`text-[11px] break-words ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {error instanceof Error ? error.message : '未知错误'}
                </div>
              </>
            )}
            <button
              type="button"
              onClick={() => refetch()}
              className={`text-xs px-2.5 py-1.5 rounded border transition-colors ${
                isDark
                  ? 'border-[#3a3a3a] text-gray-200 hover:bg-[#262626]'
                  : 'border-gray-300 text-gray-700 hover:bg-gray-100'
              }`}
            >
              重试
            </button>
          </div>
        </div>
      </CollapsibleCard>
    );
  }

  if (!sentiment) {
    return (
      <CollapsibleCard
        title="市场情绪"
        icon={<Activity size={16} className="text-pink-600" />}
        defaultOpen={true}
      >
        <div className="p-5">
          <div className={`rounded border flex items-center justify-center py-6 ${
            isDark ? 'bg-[#141414] border-[#2a2a2a] text-gray-400' : 'bg-gray-50 border-gray-200 text-gray-600'
          }`}>
            <span className="text-xs">暂无市场情绪数据</span>
          </div>
        </div>
      </CollapsibleCard>
    );
  }

  const renderSentimentBody = (expanded: boolean) => (
    <div className={expanded ? 'p-4 space-y-3' : 'p-3 space-y-3'}>
      <div className="grid grid-cols-2 gap-2">
        <div className={`p-3 rounded border ${
          isDark 
            ? 'bg-gradient-to-br from-red-950/50 to-red-900/30 border-red-900/50' 
            : 'bg-gradient-to-br from-red-50 to-red-100 border-red-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className="text-red-500" />
              <span className={`text-xs font-medium ${isDark ? 'text-red-400' : 'text-red-700'}`}>涨停</span>
            </div>
            <div className="text-xl font-bold text-red-500">{limit_up}</div>
          </div>
        </div>
        
        <div className={`p-3 rounded border ${
          isDark 
            ? 'bg-gradient-to-br from-green-950/50 to-green-900/30 border-green-900/50' 
            : 'bg-gradient-to-br from-green-50 to-green-100 border-green-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingDown size={16} className="text-green-500" />
              <span className={`text-xs font-medium ${isDark ? 'text-green-400' : 'text-green-700'}`}>跌停</span>
            </div>
            <div className="text-xl font-bold text-green-500">{limit_down}</div>
          </div>
        </div>
      </div>

      <div className={`p-3 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-50'}`}>
        <div className="flex items-center justify-between mb-2">
          <span className={`text-xs font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>涨跌分布</span>
          <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>共 {total_count} 只</span>
        </div>
        
        <div className={`h-6 rounded overflow-hidden flex ${isDark ? 'bg-[#1a1a1a]' : 'bg-gray-200'}`}>
          {up_count > 0 && (
            <div
              className="bg-red-500 flex items-center justify-center"
              style={{ width: `${(up_count / total_count) * 100}%` }}
            >
              <span className="text-xs text-white font-medium px-1">
                {up_count}
              </span>
            </div>
          )}
          {flat_count > 0 && (
            <div
              className={`flex items-center justify-center ${isDark ? 'bg-gray-700' : 'bg-gray-400'}`}
              style={{ width: `${(flat_count / total_count) * 100}%` }}
            >
              <span className="text-xs text-white font-medium px-1">
                {flat_count}
              </span>
            </div>
          )}
          {down_count > 0 && (
            <div
              className="bg-green-500 flex items-center justify-center"
              style={{ width: `${(down_count / total_count) * 100}%` }}
            >
              <span className="text-xs text-white font-medium px-1">
                {down_count}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className={`p-2.5 rounded border ${
          isDark 
            ? 'bg-[#1a1a1a] border-[#2a2a2a]' 
            : 'bg-white border-gray-200'
        }`}>
          <div className="flex items-center gap-1.5 mb-1">
            <BarChart3 size={12} className="text-blue-500" />
            <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>市场宽度</span>
          </div>
          <div className={`text-base font-bold ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
            {market_breadth?.toFixed(1)}%
          </div>
          <div className={`text-xs mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>上涨占比</div>
        </div>

        <div className={`p-2.5 rounded border ${
          isDark 
            ? 'bg-[#1a1a1a] border-[#2a2a2a]' 
            : 'bg-white border-gray-200'
        }`}>
          <div className="flex items-center gap-1.5 mb-1">
            {avg_change_pct >= 0 ? (
              <TrendingUp size={12} className="text-red-500" />
            ) : (
              <TrendingDown size={12} className="text-green-500" />
            )}
            <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>平均涨跌</span>
          </div>
          <div className={`text-base font-bold ${avg_change_pct >= 0 ? 'text-red-500' : 'text-green-500'}`}>
            {avg_change_pct >= 0 ? '+' : ''}{avg_change_pct?.toFixed(2)}%
          </div>
          <div className={`text-xs mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>全市场均值</div>
        </div>
      </div>

      {expanded && (
        <div className="grid grid-cols-2 gap-2">
          <div className={`p-2.5 rounded border ${
            isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
          }`}>
            <div className="flex items-center gap-1.5 mb-1">
              <Scale size={12} className="text-violet-500" />
              <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>涨跌家数比</span>
            </div>
            <div className={`text-base font-bold ${upDownRatio >= 1 ? 'text-red-500' : 'text-green-500'}`}>
              {upDownRatio.toFixed(2)} : 1
            </div>
            <div className={`text-xs mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>上涨/下跌</div>
          </div>
          <div className={`p-2.5 rounded border ${
            isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
          }`}>
            <div className="flex items-center gap-1.5 mb-1">
              <Scale size={12} className="text-fuchsia-500" />
              <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>涨停/跌停家数比</span>
            </div>
            <div className={`text-base font-bold ${limitUpDownRatio >= 1 ? 'text-red-500' : 'text-green-500'}`}>
              {limitUpDownRatio.toFixed(2)} : 1
            </div>
            <div className={`text-xs mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>涨停/跌停</div>
          </div>
          <div className={`p-2.5 rounded border ${
            isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
          }`}>
            <div className="flex items-center gap-1.5 mb-1">
              <Gauge size={12} className="text-amber-500" />
              <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>恐惧贪婪指数</span>
            </div>
            <div className={`text-base font-bold ${
              fearGreedIndex >= 60 ? 'text-red-500' : fearGreedIndex < 40 ? 'text-green-500' : (isDark ? 'text-gray-200' : 'text-gray-800')
            }`}>
              {fearGreedIndex}
            </div>
            <div className={`text-xs mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{fearGreedLabel}</div>
          </div>
          <div className={`p-2.5 rounded border ${
            isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
          }`}>
            <div className="flex items-center gap-1.5 mb-1">
              <DollarSign size={12} className="text-blue-500" />
              <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>当日成交额</span>
            </div>
            <div className={`text-base font-bold ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
              {formatAmountYi(currentTurnover)}
            </div>
            <div className={`text-xs mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              {turnoverRatio ? `较20日均额 ${(turnoverRatio * 100).toFixed(1)}%` : '暂无可比均值'}
            </div>
          </div>
        </div>
      )}

      <MarketBreadthChart
        height={expanded ? 320 : 210}
      />

      {expanded && (
        <div className={`p-3 rounded border ${
          isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
        }`}>
          <div className={`text-xs font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            成交额趋势（上证指数）
          </div>
          <TurnoverAmountChart data={turnoverSeries} isDark={isDark} />
        </div>
      )}

      {expanded && (fundFlowSummary || fallbackMarketTurnover) && (
        <div className={`p-3 rounded border ${
          isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
        }`}>
          <div className="flex items-center gap-2 mb-3">
            <Table size={14} className="text-blue-500" />
            <span className={`text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              市场资金净流入统计
            </span>
          </div>
          
          {fundFlowSummary ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className={isDark ? 'border-b border-[#2a2a2a]' : 'border-b border-gray-200'}>
                      <th className={`text-left py-2 px-2 font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>时间周期</th>
                      <th className={`text-right py-2 px-2 font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>净流入额(亿)</th>
                      <th className={`text-right py-2 px-2 font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>平均净流入占比</th>
                      <th className={`text-right py-2 px-2 font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>累计成交额(万亿)</th>
                      <th className={`text-left py-2 px-2 font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>最近日期</th>
                      <th className={`text-right py-2 px-2 font-medium ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>当日成交额(万亿)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fundFlowSummary.map((item) => (
                      <tr 
                        key={item.label}
                        className={isDark ? 'border-b border-[#2a2a2a]' : 'border-b border-gray-100'}
                      >
                        <td className={`py-2 px-2 font-medium ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                          {item.label}
                        </td>
                        <td className={`text-right py-2 px-2 font-semibold ${
                          item.totalInflow >= 0 ? 'text-red-500' : 'text-green-500'
                        }`}>
                          {(item.totalInflow / 100000000).toFixed(2)}
                        </td>
                        <td className={`text-right py-2 px-2 ${
                          item.avgInflowPct >= 0 ? 'text-red-500' : 'text-green-500'
                        }`}>
                          {item.avgInflowPct.toFixed(2)}%
                        </td>
                        <td className={`text-right py-2 px-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                          {(item.totalAmount / 1000000000000).toFixed(2)}
                        </td>
                        <td className={`py-2 px-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                          {item.latestDate}
                        </td>
                        <td className={`text-right py-2 px-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                          {(item.latestAmount / 1000000000000).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className={`text-xs mt-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                注：净流入为正值表示资金净流入市场，负值表示资金净流出市场
              </div>
            </>
          ) : (
            <div className={`rounded border p-3 text-xs ${
              isDark ? 'border-[#2a2a2a] bg-[#111111] text-gray-300' : 'border-gray-200 bg-gray-50 text-gray-700'
            }`}>
              <div className="flex items-center justify-between gap-3">
                <span>当日市场总成交金额</span>
                <span className="font-semibold">{formatAmountYi(fallbackMarketTurnover?.amount)}</span>
              </div>
              <div className={`mt-2 flex items-center justify-between ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <span>时间</span>
                <span>{fallbackMarketTurnover ? `${fallbackMarketTurnover.date} ${fallbackMarketTurnover.time}` : '--'}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {expanded && (
        <div className={`p-3 rounded border ${
          isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
        }`}>
          <div className={`text-xs font-medium mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            市场情绪评估
          </div>
          <div className="space-y-2">
            {assessments.map((item) => (
              <div
                key={item.metric}
                className={`rounded border p-2 ${
                  isDark ? 'border-[#2a2a2a] bg-[#111111]' : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className={`text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{item.metric}</span>
                  <span className={`text-xs font-semibold ${getAssessmentTone(item.level)}`}>{item.value}</span>
                </div>
                <div className={`text-[11px] mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>标准：{item.standard}</div>
                <div className={`text-[11px] mt-1 ${getAssessmentTone(item.level)}`}>结论：{item.conclusion}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className={`text-xs text-right ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
        更新于: {new Date().toLocaleTimeString('zh-CN')}
      </div>
    </div>
  );

  // 后端已确保数据 >= 5000，前端不再需要警告
  return (
    <>
      <CollapsibleCard
        title="市场情绪"
        icon={<Activity size={16} className="text-pink-600" />}
        defaultOpen={true}
        action={
          <button
            type="button"
            onClick={() => setShowExpandedModal(true)}
            className={`p-1.5 rounded transition-colors ${
              isDark
                ? 'text-gray-400 hover:text-white hover:bg-[#2a2a2a]'
                : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
            }`}
            title="查看放大图"
          >
            <Maximize2 size={14} />
          </button>
        }
      >
        {renderSentimentBody(false)}
      </CollapsibleCard>
      {showExpandedModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
            onClick={() => setShowExpandedModal(false)}
          />
          <div className="flex min-h-full items-center justify-center p-4">
            <div
              className={`relative w-full max-w-5xl max-h-[90vh] overflow-y-auto rounded-lg shadow-2xl ${
                isDark ? 'bg-[#1a1a1a] border border-[#2a2a2a]' : 'bg-white border border-gray-200'
              }`}
              onClick={(e) => e.stopPropagation()}
            >
              <div className={`flex items-center justify-between px-5 py-3 border-b ${
                isDark ? 'border-[#2a2a2a] bg-[#0f0f0f]' : 'border-gray-200 bg-gray-50'
              }`}>
                <h3 className={`text-sm font-semibold ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>
                  市场情绪（放大版）
                </h3>
                <button
                  type="button"
                  onClick={() => setShowExpandedModal(false)}
                  className={`p-1.5 rounded transition-colors ${
                    isDark
                      ? 'text-gray-400 hover:text-white hover:bg-[#2a2a2a]'
                      : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                  title="关闭"
                >
                  <X size={16} />
                </button>
              </div>
              {renderSentimentBody(true)}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
