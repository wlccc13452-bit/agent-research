/**
 * 财务分析标签页主组件
 * 整合三个子组件：财务数据、季度数据、年报/季报
 */
import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fundamentalApi } from '../services/api';
import { BarChart2, TrendingUp, TrendingDown, AlertCircle, Minus } from 'lucide-react';

// 子组件
import FinancialMetricsCard from './FinancialMetricsCard';
import MarketTrendCard from './MarketTrendCard';
import QuarterlyDataCard from './QuarterlyDataCard';
import AnnualReportCard from './AnnualReportCard';

interface FinancialTabProps {
  stockCode: string | null;
}

export default function FinancialTab({ stockCode }: FinancialTabProps) {
  const queryClient = useQueryClient();
  const [wsConnected, setWsConnected] = useState<boolean>(() => Boolean((window as any).__stockPegWsConnected));

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
    const onMessage = (event: Event) => {
      const message = (event as CustomEvent).detail;
      if (!message?.type) return;
      if (message.type !== 'financial_updated' && message.type !== 'financial-updated') return;
      if (!stockCode || message.stock_code !== stockCode) return;
      queryClient.invalidateQueries({ queryKey: ['fundamental', stockCode] });
      queryClient.invalidateQueries({ queryKey: ['valuation', stockCode] });
      queryClient.invalidateQueries({ queryKey: ['annual-report', stockCode] });
      queryClient.invalidateQueries({ queryKey: ['quarterly-data', stockCode] });
    };
    window.addEventListener('websocket-message', onMessage);
    return () => window.removeEventListener('websocket-message', onMessage);
  }, [stockCode, queryClient]);

  // 获取基本面数据
  const { data: fundamental, isLoading, error } = useQuery({
    queryKey: ['fundamental', stockCode],
    queryFn: () => fundamentalApi.analyze(stockCode!),
    enabled: !!stockCode && !stockCode.startsWith('UNKNOWN'),
    refetchInterval: wsConnected ? false : 180000,
  });

  // 获取估值数据
  const { data: valuation } = useQuery({
    queryKey: ['valuation', stockCode],
    queryFn: () => fundamentalApi.getValuation(stockCode!),
    enabled: !!stockCode && !stockCode.startsWith('UNKNOWN'),
    refetchInterval: wsConnected ? false : 180000,
  });

  // 获取年报数据
  const { data: annualReportResponse } = useQuery({
    queryKey: ['annual-report', stockCode],
    queryFn: () => fundamentalApi.getAnnualReport(stockCode!),
    enabled: !!stockCode && !stockCode.startsWith('UNKNOWN'),
    refetchInterval: wsConnected ? false : 300000,
  });

  // 获取季度财务数据
  const { data: quarterlyDataResponse } = useQuery({
    queryKey: ['quarterly-data', stockCode],
    queryFn: () => fundamentalApi.getQuarterlyData(stockCode!, 3),
    enabled: !!stockCode && !stockCode.startsWith('UNKNOWN'),
    refetchInterval: wsConnected ? false : 300000,
  });

  // 提取实际数据（适配新的API格式）
  const annualReport = annualReportResponse?.data || annualReportResponse;
  const quarterlyData = quarterlyDataResponse?.data || quarterlyDataResponse;

  if (!stockCode) {
    return (
      <div className="h-full flex items-center justify-center p-8" style={{ color: 'var(--text-secondary)' }}>
        <div className="text-center">
          <BarChart2 size={32} className="mx-auto mb-2" style={{ color: 'var(--text-muted)' }} />
          <p className="text-sm">请选择股票查看财务分析</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-3 space-y-3">
        <div className="animate-pulse space-y-2">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-10" style={{ backgroundColor: 'var(--bg-hover)' }}></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-8" style={{ color: 'var(--danger-color)' }}>
        <div className="text-center">
          <AlertCircle size={32} className="mx-auto mb-2" />
          <p className="text-sm">加载财务数据失败</p>
        </div>
      </div>
    );
  }

  // 后端返回的数据结构: {valuation, growth, financial_health, market_trend}
  // 直接使用 fundamental 中的数据
  const valuationData = valuation || {};
  
  // 合并数据 - 后端返回的数据结构
  const rawAllData = { 
    // 从 fundamental.valuation 中获取估值数据
    ...(fundamental?.valuation || {}),
    // 从 fundamental.growth 中获取成长数据
    ...(fundamental?.growth || {}),
    // 从 fundamental.financial_health 中获取财务健康数据
    ...(fundamental?.financial_health || {}),
    // 如果有单独的 valuation API 数据，也合并进来
    ...valuationData,
  };
  
  // 字段映射：将后端字段名映射到前端期望的字段名
  const allData = {
    ...rawAllData,
    pe_ratio: rawAllData.pe_ttm || rawAllData.pe_ratio || rawAllData.pe_lyr,
    pb_ratio: rawAllData.pb || rawAllData.pb_ratio,
    ps_ratio: rawAllData.ps_ttm || rawAllData.ps_ratio,
    peg_ratio: rawAllData.peg || rawAllData.peg_ratio,
    revenue_growth: rawAllData.revenue_cagr_3y || rawAllData.revenue_growth,
    profit_growth: rawAllData.profit_cagr_3y || rawAllData.profit_growth,
    cash_flow: rawAllData.cash_flow || rawAllData.operating_cashflow,
  };
  const recommendation = fundamental?.recommendation;
  const rating = recommendation?.rating || '观望';
  const recommendationUI = rating === '买入'
    ? {
        panelClass: 'bg-red-500/10 border-red-500/30',
        iconWrapClass: 'bg-red-500/15 text-red-500',
        badgeClass: 'bg-red-500/15 text-red-500',
        titleClass: 'text-red-500',
        hint: '偏进攻策略',
      }
    : rating === '卖出'
      ? {
          panelClass: 'bg-green-500/10 border-green-500/30',
          iconWrapClass: 'bg-green-500/15 text-green-500',
          badgeClass: 'bg-green-500/15 text-green-500',
          titleClass: 'text-green-500',
          hint: '偏防守策略',
        }
      : rating === '持有'
        ? {
            panelClass: 'bg-amber-500/10 border-amber-500/30',
            iconWrapClass: 'bg-amber-500/15 text-amber-500',
            badgeClass: 'bg-amber-500/15 text-amber-500',
            titleClass: 'text-amber-500',
            hint: '平衡观察策略',
          }
        : {
            panelClass: 'bg-slate-500/10 border-slate-500/30',
            iconWrapClass: 'bg-slate-500/15 text-slate-500',
            badgeClass: 'bg-slate-500/15 text-slate-500',
            titleClass: 'text-slate-500',
            hint: '等待明确信号',
          };

  return (
    <div className="h-full flex flex-col gap-2 p-2 overflow-auto">
      {/* 1. 财务数据卡片 */}
      <FinancialMetricsCard data={allData} />

      {/* 2. 市场趋势分析卡片 */}
      <MarketTrendCard data={fundamental?.market_trend || {}} />

      {/* 3. 季度数据趋势和明细卡片 */}
      <QuarterlyDataCard quarterlyData={quarterlyData} />

      {/* 3. 最新年报或季报卡片 */}
      <AnnualReportCard annualReport={annualReport} stockCode={stockCode} />

      {/* 投资建议 */}
      {recommendation && (
        <div className={`p-3 border ${recommendationUI.panelClass}`}>
          <div className="flex items-start justify-between gap-3 mb-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className={`w-7 h-7 flex items-center justify-center flex-shrink-0 ${recommendationUI.iconWrapClass}`}>
                {rating === '买入' ? (
                  <TrendingUp size={15} />
                ) : rating === '卖出' ? (
                  <TrendingDown size={15} />
                ) : rating === '持有' ? (
                  <Minus size={15} />
                ) : (
                  <AlertCircle size={15} />
                )}
              </div>
              <div className="min-w-0">
                <div className={`font-bold text-sm ${recommendationUI.titleClass}`}>投资建议: {rating}</div>
                <div className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>{recommendationUI.hint}</div>
              </div>
            </div>
            <span className={`text-[10px] px-1.5 py-0.5 font-semibold ${recommendationUI.badgeClass}`}>{rating}</span>
          </div>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            {recommendation.reason}
          </p>
          <div className="mt-2 h-px" style={{ backgroundColor: 'var(--border-color)' }} />
          <div className="pt-2 text-[10px]" style={{ color: 'var(--text-muted)' }}>
            仅作研究参考，不构成投资建议
          </div>
        </div>
      )}
    </div>
  );
}
