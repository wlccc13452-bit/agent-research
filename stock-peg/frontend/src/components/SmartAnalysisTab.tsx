import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { predictionApi, usMarketApi, reportApi, holdingsApi } from '../services/api';
import { Globe, Zap, Target, FileText, TrendingUp, TrendingDown, Minus, ChevronRight, AlertTriangle, FilePlus, Loader2, Info } from 'lucide-react';
import CollapsibleCard from './CollapsibleCard';
import ReportModal from './ReportModal';
import { useTheme } from '../contexts/ThemeContext';
import { useMemo, useState, useEffect } from 'react';

interface SmartAnalysisTabProps {
  stockCode: string | null;
  stockSector?: string;
  mode?: 'full' | 'marketOnly' | 'reportOnly';
  containerClassName?: string;
}

export default function SmartAnalysisTab({
  stockCode,
  stockSector,
  mode = 'full',
  containerClassName = 'h-full flex flex-col gap-1 p-2 overflow-auto'
}: SmartAnalysisTabProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const showMarketModules = mode !== 'reportOnly';
  const showReportModule = mode !== 'marketOnly';
  const isValidSelectedStock = !!stockCode && !stockCode.startsWith('UNKNOWN');
  
  // 报告生成进度状态
  const [reportProgress, setReportProgress] = useState<{
    isGenerating: boolean;
    stage: string;
    progress: number;
    message: string;
  } | null>(null);
  
  // 最新生成的报告
  const [latestGeneratedReport, setLatestGeneratedReport] = useState<any>(null);
  
  // 监听 WebSocket 进度消息
  useEffect(() => {
    if (!showReportModule) return;

    const handleWebSocketMessage = (event: CustomEvent) => {
      const message = event.detail;
      
      if (message.type === 'report_progress' && message.stock_code === stockCode) {
        setReportProgress({
          isGenerating: true,
          stage: message.stage,
          progress: message.progress,
          message: message.message
        });
      }
      
      if (message.type === 'report_completed' && message.stock_code === stockCode) {
        setReportProgress(null);
        setLatestGeneratedReport(message);
        queryClient.invalidateQueries({ queryKey: ['latest-reports'] });
      }
      
      if (message.type === 'report_error' && message.stock_code === stockCode) {
        setReportProgress(null);
        alert(`生成报告失败: ${message.error}`);
      }
    };
    
    // 监听 WebSocket 消息
    window.addEventListener('websocket-message', handleWebSocketMessage as any);
    
    return () => {
      window.removeEventListener('websocket-message', handleWebSocketMessage as any);
    };
  }, [stockCode, queryClient, showReportModule]);

  // 先获取持仓数据，用于判断股票是否在持仓中
  const { data: holdings } = useQuery({
    queryKey: ['holdings'],
    queryFn: holdingsApi.getHoldings,
    enabled: showReportModule || showMarketModules,  // 同时启用，因为prediction和usAnalysis需要
  });

  // 获取当前股票详情（判断是否在持仓中）
  const stockDetail = useMemo(() => {
    if (!stockCode || !holdings?.sectors) return null;
    for (const sector of holdings.sectors) {
      const found = sector.stocks.find((s: any) => s.code === stockCode);
      if (found) return { ...found, sector: sector.name };
    }
    return null;
  }, [stockCode, holdings]);

  const { data: prediction, isLoading: loadingPrediction } = useQuery({
    queryKey: ['prediction', stockCode],
    queryFn: () => predictionApi.predict(stockCode!),
    enabled: showMarketModules && !!stockDetail,  // 只对持仓股票启用预测
    retry: false,
    staleTime: 60000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const { data: usAnalysis, isLoading: loadingUSAnalysis } = useQuery({
    queryKey: ['us-analysis', stockCode],
    queryFn: () => usMarketApi.getAnalysis(stockCode!),
    enabled: showMarketModules && !!stockDetail,  // 只对持仓股票启用美股分析
    retry: false,
    staleTime: 60000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const { data: sectorRotation, isLoading: loadingRotation } = useQuery({
    queryKey: ['sector-rotation'],
    queryFn: predictionApi.analyzeSectorRotation,
    enabled: showMarketModules,
  });

  const { data: latestReports, isLoading: loadingReports } = useQuery({
    queryKey: ['latest-reports'],
    queryFn: () => reportApi.getList({}),
    enabled: showReportModule,
  });

  // 获取LLM报告列表
  const { data: llmReports } = useQuery({
    queryKey: ['llm-reports', stockCode],
    queryFn: () => reportApi.getLLMList(stockCode || undefined),
    enabled: showReportModule && !!stockCode,
  });

  // LLM报告生成进度状态
  const [llmReportProgress, setLLMReportProgress] = useState<{
    isGenerating: boolean;
    stage: string;
    progress: number;
    message: string;
  } | null>(null);
  
  // 最新生成的LLM报告
  const [latestLLMReport, setLatestLLMReport] = useState<any>(null);
  
  // 报告模态弹窗状态
  const [reportModal, setReportModal] = useState<{
    isOpen: boolean;
    title: string;
    content: string;
    stockCode?: string;
    stockName?: string;
    reportDate?: string;
  }>({
    isOpen: false,
    title: '',
    content: ''
  });
  const [internationalMarketModalOpen, setInternationalMarketModalOpen] = useState(false);
  
  // 打开报告模态弹窗
  const openReportModal = async (fileName: string, stockName: string, reportDate?: string, stockCode?: string) => {
    try {
      const result = await reportApi.getLLMContent(fileName);
      setReportModal({
        isOpen: true,
        title: 'AI智能评估报告',
        content: result.content,
        stockCode,
        stockName,
        reportDate
      });
    } catch {
      alert('加载报告失败，请重试');
    }
  };
  
  // 关闭报告模态弹窗
  const closeReportModal = () => {
    setReportModal({
      isOpen: false,
      title: '',
      content: ''
    });
  };
  
  // 监听LLM报告WebSocket消息
  useEffect(() => {
    if (!showReportModule) return;

    const handleWebSocketMessage = (event: CustomEvent) => {
      const message = event.detail;
      
      if (message.type === 'llm_report_progress' && message.stock_code === stockCode) {
        setLLMReportProgress({
          isGenerating: true,
          stage: message.stage,
          progress: message.progress,
          message: message.message
        });
      }
      
      if (message.type === 'llm_report_completed' && message.stock_code === stockCode) {
        setLLMReportProgress(null);
        setLatestLLMReport(message);
        queryClient.invalidateQueries({ queryKey: ['llm-reports'] });
      }
      
      if (message.type === 'llm_report_error' && message.stock_code === stockCode) {
        setLLMReportProgress(null);
        alert(`生成LLM报告失败: ${message.error}`);
      }
    };
    
    // 监听 WebSocket 消息
    window.addEventListener('websocket-message', handleWebSocketMessage as any);
    
    return () => {
      window.removeEventListener('websocket-message', handleWebSocketMessage as any);
    };
  }, [stockCode, queryClient, showReportModule]);

  const generateReportMutation = useMutation({
    mutationFn: () => {
      if (!stockDetail) throw new Error('未找到股票信息');
      setReportProgress({
        isGenerating: true,
        stage: 'init',
        progress: 0,
        message: '初始化报告生成...'
      });
      return reportApi.generate({
        stock_code: stockDetail.code,
        stock_name: stockDetail.name,
        sector: stockDetail.sector,
        report_date: new Date().toISOString().split('T')[0]
      });
    },
    onSuccess: () => {
      // WebSocket 会处理进度更新，这里不需要额外处理
      queryClient.invalidateQueries({ queryKey: ['latest-reports'] });
    },
    onError: (error: any) => {
      setReportProgress(null);
      alert(`生成报告失败: ${error.message || '未知错误'}`);
    },
  });

  // LLM报告生成mutation
  const generateLLMReportMutation = useMutation({
    mutationFn: () => {
      if (!stockDetail) throw new Error('未找到股票信息');
      setLLMReportProgress({
        isGenerating: true,
        stage: 'init',
        progress: 0,
        message: '开始生成LLM智能评估报告...'
      });
      return reportApi.generateLLM({
        stock_code: stockDetail.code,
        stock_name: stockDetail.name,
        days: 20
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-reports'] });
    },
    onError: (error: any) => {
      setLLMReportProgress(null);
      alert(`生成LLM报告失败: ${error.message || '未知错误'}`);
    },
  });

  const predData = prediction?.prediction;
  const direction = predData?.direction;
  const probability = predData?.probability || 0;
  const isUp = direction === '上涨';
  const isDown = direction === '下跌';
  const predictionHeaderClass = isDark
    ? 'bg-gradient-to-r from-[#1b1830] via-[#141c33] to-[#10131f]'
    : 'bg-gradient-to-r from-violet-50 via-indigo-50 to-cyan-50';
  const predictionHintClass = isDark
    ? 'bg-[#11162a] border-[#2a3350] text-[#aeb9d6]'
    : 'bg-indigo-50/80 border-indigo-100 text-indigo-900/75';
  const predictionIconShellClass = isUp
    ? isDark ? 'bg-red-950/50 ring-1 ring-red-800/50' : 'bg-red-50 ring-1 ring-red-200'
    : isDown
      ? isDark ? 'bg-green-950/50 ring-1 ring-green-800/50' : 'bg-green-50 ring-1 ring-green-200'
      : isDark ? 'bg-[#23283b] ring-1 ring-[#37405f]' : 'bg-slate-100 ring-1 ring-slate-200';
  const predictionDirectionTextClass = isUp
    ? isDark ? 'text-red-400' : 'text-red-600'
    : isDown
      ? isDark ? 'text-green-400' : 'text-green-600'
      : isDark ? 'text-slate-300' : 'text-slate-600';
  const predictionBarTrackClass = isDark ? 'bg-[#232a40]' : 'bg-indigo-100/70';
  const predictionBarFillClass = isUp
    ? 'bg-gradient-to-r from-red-500 to-rose-400'
    : isDown
      ? 'bg-gradient-to-r from-emerald-500 to-green-400'
      : isDark ? 'bg-gradient-to-r from-slate-500 to-slate-400' : 'bg-gradient-to-r from-slate-400 to-slate-300';
  const predictionMetricCardClass = isDark ? 'bg-[#141a2d] border border-[#2b3654]' : 'bg-white border border-indigo-100';
  const predictionMetricTextClass = isDark ? 'text-[#97a5c8]' : 'text-indigo-700/70';
  const predictionMetricValueClass = isDark ? 'text-[#d9e2ff]' : 'text-indigo-950';
  const predictionScoreClass = isDark ? 'text-amber-400' : 'text-amber-600';

  const relatedUSStocks = useMemo(() => usAnalysis?.related_stocks || {}, [usAnalysis]);
  const usAnalysisData = useMemo(() => usAnalysis?.analysis || {}, [usAnalysis]);
  const usMarketData = useMemo(() => usAnalysis?.us_data || {}, [usAnalysis]);
  const usLeaderStocks = relatedUSStocks.industry_leaders || [];

  const internationalLinkData = useMemo(() => {
    const normalize = (value: string) =>
      value.toLowerCase().replace(/[\s-_]/g, '').replace(/(板块|行业|概念|主题|指数)/g, '');
    const context = normalize(`${stockSector || stockDetail?.sector || ''}${stockDetail?.name || ''}`);

    const fallbackProfiles = [
      {
        keywords: ['石油', '油气', '能源', '煤炭', '航运'],
        items: [
          { symbol: 'BZ=F', name: '布伦特原油', correlation: '国际能源基准', category: '能源', relevance_score: 0.95 },
          { symbol: 'CL=F', name: 'WTI原油', correlation: '原油联动', category: '能源', relevance_score: 0.9 },
          { symbol: 'NG=F', name: 'NYMEX天然气', correlation: '燃料成本', category: '能源', relevance_score: 0.8 }
        ]
      },
      {
        keywords: ['有色', '铜', '铝', '黄金', '钢铁', '稀土', '金属'],
        items: [
          { symbol: 'HG=F', name: 'COMEX铜', correlation: '工业金属景气', category: '金属', relevance_score: 0.9 },
          { symbol: 'ALI', name: 'LME铝', correlation: '铝价成本传导', category: '金属', relevance_score: 0.88 },
          { symbol: 'GC=F', name: 'COMEX黄金', correlation: '金属风险偏好', category: '金属', relevance_score: 0.72 }
        ]
      },
      {
        keywords: ['化工', '化学', '橡胶', '塑料', '磷化工', '煤化工'],
        items: [
          { symbol: 'DBA', name: '农业化工原料ETF', correlation: '化工原料链', category: '化工', relevance_score: 0.75 },
          { symbol: 'BNO', name: '布伦特原油ETF', correlation: '化工成本锚', category: '化工', relevance_score: 0.86 },
          { symbol: 'UAN', name: '氮肥价格代理', correlation: '化工品景气', category: '化工', relevance_score: 0.7 }
        ]
      },
      {
        keywords: ['新能源', '光伏', '电池', '锂', '电力'],
        items: [
          { symbol: 'BZ=F', name: '布伦特原油', correlation: '替代能源比较', category: '能源', relevance_score: 0.6 },
          { symbol: 'SI=F', name: '工业硅', correlation: '光伏上游材料', category: '化工', relevance_score: 0.82 },
          { symbol: 'LIT', name: '锂电产业ETF', correlation: '电池材料景气', category: '金属', relevance_score: 0.8 }
        ]
      }
    ];

    const categoryMap: Record<string, string> = {
      commodities: '大宗',
      energy: '能源',
      metals: '金属',
      chemicals: '化工'
    };

    const merged = [
      ...(relatedUSStocks.commodities || []).map((item: any) => ({ ...item, category: categoryMap.commodities, source: 'analysis' })),
      ...(relatedUSStocks.energy || []).map((item: any) => ({ ...item, category: categoryMap.energy, source: 'analysis' })),
      ...(relatedUSStocks.metals || []).map((item: any) => ({ ...item, category: categoryMap.metals, source: 'analysis' })),
      ...(relatedUSStocks.chemicals || []).map((item: any) => ({ ...item, category: categoryMap.chemicals, source: 'analysis' }))
    ];

    const fallback = fallbackProfiles
      .filter((profile) => profile.keywords.some((keyword) => context.includes(keyword)))
      .flatMap((profile) => profile.items)
      .map((item) => ({ ...item, source: 'fallback' }));

    const normalizedMerged = [...merged, ...fallback].map((item) => ({
      symbol: item.symbol || '',
      name: item.name || item.symbol || '--',
      correlation: item.correlation || '联动参考',
      category: item.category || '大宗',
      relevance_score: typeof item.relevance_score === 'number' ? item.relevance_score : 0.65,
      source: item.source || 'fallback'
    }));

    const uniqueItems = normalizedMerged.filter(
      (item, index, array) =>
        array.findIndex((candidate) => candidate.symbol === item.symbol && candidate.name === item.name) === index
    );

    const sortedItems = uniqueItems.sort((a, b) => b.relevance_score - a.relevance_score).slice(0, 6);
    const sourceLabel = sortedItems.some((item) => item.source === 'analysis') ? 'LLM识别' : '规则兜底';
    return { items: sortedItems, sourceLabel };
  }, [relatedUSStocks, stockSector, stockDetail]);

  return (
    <>
      {showReportModule && (
        <ReportModal
          isOpen={reportModal.isOpen}
          onClose={closeReportModal}
          title={reportModal.title}
          content={reportModal.content}
          stockCode={reportModal.stockCode}
          stockName={reportModal.stockName}
          reportDate={reportModal.reportDate}
        />
      )}
      {showMarketModules && internationalMarketModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
          onClick={() => setInternationalMarketModalOpen(false)}
        >
          <div
            className={`w-full max-w-3xl max-h-[85vh] overflow-hidden ${isDark ? 'bg-[#111111] border border-[#2a2a2a]' : 'bg-white border border-gray-200'}`}
            onClick={(event) => event.stopPropagation()}
          >
            <div className={`px-4 py-3 border-b flex items-center justify-between ${isDark ? 'border-[#2a2a2a]' : 'border-gray-200'}`}>
              <div className="flex items-center gap-2">
                <Globe size={16} className="text-blue-500" />
                <span className={`text-sm font-bold ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>国际市场联动分析</span>
              </div>
              <button
                onClick={() => setInternationalMarketModalOpen(false)}
                className={`text-xs px-2 py-1 ${isDark ? 'bg-[#1f2937] text-gray-300 hover:bg-[#273449]' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
              >
                关闭
              </button>
            </div>
            <div className="p-4 space-y-4 overflow-y-auto max-h-[calc(85vh-56px)]">
              <div className={`p-3 border ${isDark ? 'border-[#2a2a2a] bg-[#151515]' : 'border-gray-200 bg-gray-50'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs font-bold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>美股联动分析</span>
                  <button
                    onClick={() => navigate('/us-market')}
                    className="text-xs text-blue-500 hover:text-blue-400 flex items-center"
                  >
                    详情 <ChevronRight size={12} />
                  </button>
                </div>
                <div className="space-y-2">
                  {loadingUSAnalysis ? (
                    <div className="animate-pulse space-y-2">
                      <div className={`h-12 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
                      <div className={`h-12 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
                    </div>
                  ) : usAnalysis && usLeaderStocks.length > 0 ? (
                    usLeaderStocks.map((stock: any) => {
                      const analysis = usAnalysisData[stock.symbol];
                      return (
                        <div key={stock.symbol} className={`p-2 ${isDark ? 'bg-[#1a1a1a]' : 'bg-white border border-gray-100'}`}>
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2 min-w-0">
                              <span className={`text-xs font-bold ${isDark ? 'text-gray-200' : ''}`}>{stock.symbol}</span>
                              <span className={`text-xs truncate ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{stock.name}</span>
                            </div>
                            <span className={`text-xs px-1.5 py-0.5 ${isDark ? 'bg-blue-900/50 text-blue-400' : 'bg-blue-100 text-blue-700'}`}>龙头</span>
                          </div>
                          {analysis && (
                            <div className="flex items-center gap-2 text-xs">
                              <span className={`font-medium ${
                                analysis.impact === '正面' ? 'text-red-500' :
                                analysis.impact === '负面' ? 'text-green-500' : isDark ? 'text-gray-400' : 'text-gray-600'
                              }`}>
                                {analysis.impact}
                              </span>
                              <span className={isDark ? 'text-gray-600' : 'text-gray-400'}>·</span>
                              <span className={`truncate ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{analysis.recommendation}</span>
                            </div>
                          )}
                        </div>
                      );
                    })
                  ) : (
                    <div className={`text-center py-3 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      选择股票查看美股联动
                    </div>
                  )}
                </div>
              </div>
              <div className={`p-3 border ${isDark ? 'border-[#2a2a2a] bg-[#151515]' : 'border-gray-200 bg-gray-50'}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs font-bold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>国际大宗联动</span>
                  <span className={`text-[11px] px-1.5 py-0.5 ${isDark ? 'bg-emerald-900/50 text-emerald-300' : 'bg-emerald-100 text-emerald-700'}`}>
                    {internationalLinkData.sourceLabel}
                  </span>
                </div>
                <div className="space-y-2">
                  {loadingUSAnalysis ? (
                    <div className="animate-pulse space-y-2">
                      <div className={`h-10 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
                      <div className={`h-10 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
                    </div>
                  ) : internationalLinkData.items.length > 0 ? (
                    internationalLinkData.items.map((item) => {
                      const marketData = usMarketData[item.symbol];
                      const changePct = typeof marketData?.change_pct === 'number' ? marketData.change_pct : null;
                      return (
                        <div key={`${item.symbol}-${item.name}`} className={`p-2 ${isDark ? 'bg-[#1a1a1a]' : 'bg-white border border-gray-100'}`}>
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <div className="flex items-center gap-2 min-w-0">
                              <span className={`text-xs font-bold ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>{item.symbol}</span>
                              <span className={`text-xs truncate ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.name}</span>
                            </div>
                            <span className={`text-[11px] px-1.5 py-0.5 ${isDark ? 'bg-[#253042] text-[#9fb4d1]' : 'bg-blue-100 text-blue-700'}`}>
                              {item.category}
                            </span>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className={`truncate ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.correlation}</span>
                            <span className={`font-medium ${
                              changePct === null
                                ? isDark ? 'text-gray-500' : 'text-gray-500'
                                : changePct >= 0
                                  ? 'text-red-500'
                                  : 'text-green-500'
                            }`}>
                              {changePct === null ? '--' : `${changePct >= 0 ? '+' : ''}${changePct.toFixed(2)}%`}
                            </span>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className={`text-center py-3 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      选择股票后展示国际大宗与能源金属化工联动
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div className={containerClassName}>
      {showMarketModules && (
      <CollapsibleCard 
        title="明日预测" 
        icon={<Target size={16} className="text-purple-500" />}
        defaultOpen={true}
        className={mode === 'marketOnly' ? 'order-last' : ''}
        action={
          <span
            className="inline-flex"
            title="预测原因：基于历史行情、量价结构、波动特征、市场联动和近期趋势信号综合判断。"
          >
            <Info size={12} className="text-purple-500" />
          </span>
        }
        headerClassName={predictionHeaderClass}
      >
        <div className="p-3">
          {loadingPrediction ? (
            <div className="animate-pulse space-y-2">
              <div className={`h-8 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
              <div className={`h-4 rounded w-2/3 ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
            </div>
          ) : predData ? (
            <div className="space-y-3">
              <div className={`p-2 text-[11px] border space-y-1 ${
                predictionHintClass
              }`}>
                <div className="flex items-start gap-1.5">
                  <Info size={12} className="mt-0.5 flex-shrink-0 text-purple-500" />
                  <span title="数据来源：历史行情、技术指标、行情结构与市场上下文。">数据来源：历史行情、技术指标、行情结构与市场上下文。</span>
                </div>
                <div className="flex items-start gap-1.5">
                  <Info size={12} className="mt-0.5 flex-shrink-0 text-purple-500" />
                  <span title="分析依据：模型综合趋势、波动、量价配合与相关市场联动信号。">分析依据：模型综合趋势、波动、量价配合与相关市场联动信号。</span>
                </div>
                <div className="flex items-start gap-1.5">
                  <Info size={12} className="mt-0.5 flex-shrink-0 text-purple-500" />
                  <span title="数据意义：用于辅助观察次日方向概率，不构成投资建议。">数据意义：用于辅助观察次日方向概率，不构成投资建议。</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 flex items-center justify-center ${predictionIconShellClass}`}>
                  {isUp ? (
                    <TrendingUp size={20} className="text-red-500" />
                  ) : isDown ? (
                    <TrendingDown size={20} className="text-green-500" />
                  ) : (
                    <Minus size={20} className={isDark ? 'text-gray-400' : 'text-gray-600'} />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-lg font-bold ${predictionDirectionTextClass}`}>
                      {direction}
                    </span>
                    <span className={`text-xs ${predictionMetricTextClass}`}>
                      概率 {(probability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className={`w-full h-1.5 mt-1 rounded-full overflow-hidden ${predictionBarTrackClass}`}>
                    <div 
                      className={`h-1.5 ${predictionBarFillClass}`}
                      style={{ width: `${probability * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className={`p-2 text-center ${predictionMetricCardClass}`}>
                  <div className={`flex items-center justify-center gap-1 ${predictionMetricTextClass}`}>
                    <span>置信度</span>
                    <span title="表示模型对方向判断稳定性的主观分级，不等于实际命中率。">
                      <Info size={11} className="text-purple-500" />
                    </span>
                  </div>
                  <div className={`font-bold ${predictionMetricValueClass}`}>{predData.confidence || '中'}</div>
                </div>
                <div className={`p-2 text-center ${predictionMetricCardClass}`}>
                  <div className={`flex items-center justify-center gap-1 ${predictionMetricTextClass}`}>
                    <span>风险</span>
                    <span title="表示预测场景下潜在波动与不确定性等级，等级越高需更谨慎。">
                      <Info size={11} className="text-purple-500" />
                    </span>
                  </div>
                  <div className={`font-bold ${predictionMetricValueClass}`}>{predData.risk_level || '中'}</div>
                </div>
                <div className={`p-2 text-center ${predictionMetricCardClass}`}>
                  <div className={`flex items-center justify-center gap-1 ${predictionMetricTextClass}`}>
                    <span>评分</span>
                    <span title="综合评分聚合趋势、强弱、风险与上下文信号，仅用于横向比较。">
                      <Info size={11} className="text-purple-500" />
                    </span>
                  </div>
                  <div className={`font-bold ${predictionScoreClass}`}>{prediction?.overall_score?.toFixed(1) || '--'}</div>
                </div>
              </div>
            </div>
          ) : (
            <div className={`text-center py-4 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              选择股票查看预测
            </div>
          )}
        </div>
      </CollapsibleCard>
      )}

      {showMarketModules && (
      <CollapsibleCard 
        title="国际市场联动分析"
        icon={<Globe size={16} className="text-blue-500" />}
        defaultOpen={false}
        action={
          <button 
            onClick={() => setInternationalMarketModalOpen(true)}
            className="text-xs text-blue-500 hover:text-blue-400 flex items-center"
          >
            详情 <ChevronRight size={12} />
          </button>
        }
      >
        <div className="p-2 space-y-2">
          <div className={`p-2 border ${isDark ? 'bg-[#111111] border-[#2a2a2a]' : 'bg-blue-50 border-blue-100'}`}>
            <div className="flex items-center justify-between mb-1">
              <span className={`text-xs font-bold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>美股联动分析</span>
              <span className={`text-[11px] ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>龙头影响</span>
            </div>
            {loadingUSAnalysis ? (
              <div className="animate-pulse space-y-1">
                <div className={`h-8 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
              </div>
            ) : usAnalysis && usLeaderStocks.length > 0 ? (
              usLeaderStocks.slice(0, 2).map((stock: any) => {
                const analysis = usAnalysisData[stock.symbol];
                return (
                  <div key={stock.symbol} className="flex items-center justify-between text-xs py-0.5">
                    <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>{stock.symbol}</span>
                    <span className={`truncate max-w-[70%] ${
                      analysis?.impact === '正面' ? 'text-red-500' :
                      analysis?.impact === '负面' ? 'text-green-500' : isDark ? 'text-gray-500' : 'text-gray-500'
                    }`}>
                      {analysis?.recommendation || '联动观察中'}
                    </span>
                  </div>
                );
              })
            ) : (
              <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                选择股票查看美股联动
              </div>
            )}
          </div>
          <div className={`p-2 border ${isDark ? 'bg-[#111111] border-[#2a2a2a]' : 'bg-emerald-50 border-emerald-100'}`}>
            <div className="flex items-center justify-between mb-1">
              <span className={`text-xs font-bold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>国际大宗联动</span>
              <span className={`text-[11px] px-1.5 py-0.5 ${isDark ? 'bg-emerald-900/50 text-emerald-300' : 'bg-emerald-100 text-emerald-700'}`}>
                {internationalLinkData.sourceLabel}
              </span>
            </div>
            {loadingUSAnalysis ? (
              <div className="animate-pulse space-y-1">
                <div className={`h-8 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
              </div>
            ) : internationalLinkData.items.length > 0 ? (
              internationalLinkData.items.slice(0, 2).map((item) => {
                const marketData = usMarketData[item.symbol];
                const changePct = typeof marketData?.change_pct === 'number' ? marketData.change_pct : null;
                return (
                  <div key={`${item.symbol}-${item.name}`} className="flex items-center justify-between text-xs py-0.5">
                    <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>{item.symbol}</span>
                    <span className={`font-medium ${
                      changePct === null ? (isDark ? 'text-gray-500' : 'text-gray-500') : changePct >= 0 ? 'text-red-500' : 'text-green-500'
                    }`}>
                      {changePct === null ? '--' : `${changePct >= 0 ? '+' : ''}${changePct.toFixed(2)}%`}
                    </span>
                  </div>
                );
              })
            ) : (
              <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                选择股票后展示国际大宗联动
              </div>
            )}
          </div>
        </div>
      </CollapsibleCard>
      )}

      {showMarketModules && (
      <CollapsibleCard 
        title="板块轮动预测" 
        icon={<Zap size={16} className="text-indigo-500" />}
        defaultOpen={false}
        action={
          <span
            className="inline-flex"
            title="预测原因：结合当前热点持续性、资金切换节奏、板块强弱变化与近期市场风格推断。"
          >
            <Info size={12} className="text-indigo-500" />
          </span>
        }
      >
        <div className="p-2 space-y-2">
          {loadingRotation ? (
            <div className="animate-pulse space-y-2">
              <div className={`h-16 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
              <div className={`h-12 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
            </div>
          ) : sectorRotation ? (
            <>
              <div className={`p-2 ${isDark ? 'bg-indigo-950/30' : 'bg-indigo-50'}`}>
                <div className={`text-xs mb-1.5 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>当前热点板块</div>
                <div className="flex flex-wrap gap-1">
                  {sectorRotation.hotspot_sectors?.slice(0, 3).map((sector: string) => (
                    <span key={sector} className={`text-xs px-2 py-0.5 font-medium ${isDark ? 'bg-indigo-900/50 text-indigo-400' : 'bg-indigo-100 text-indigo-700'}`}>
                      {sector}
                    </span>
                  ))}
                </div>
              </div>

              {sectorRotation.next_hotspot_prediction && (
                <div className={`p-2 border ${
                  isDark 
                    ? 'bg-gradient-to-r from-orange-950/30 to-yellow-950/30 border-orange-900/50' 
                    : 'bg-gradient-to-r from-orange-50 to-yellow-50 border-orange-200'
                }`}>
                  <div className={`text-xs mb-1 flex items-center gap-1 ${isDark ? 'text-orange-400' : 'text-orange-700'}`}>
                    <AlertTriangle size={10} />
                    下一个热点预测
                    <span
                      className="inline-flex"
                      title="该预测综合近期板块热度、轮动速度、相对强弱与成交活跃度，不代表确定结果。"
                    >
                      <Info size={10} className={isDark ? 'text-orange-400' : 'text-orange-600'} />
                    </span>
                  </div>
                  <div className={`text-sm font-bold ${isDark ? 'text-orange-400' : 'text-orange-800'}`}>
                    {sectorRotation.next_hotspot_prediction}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className={`text-center py-3 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              暂无板块轮动数据
            </div>
          )}
        </div>
      </CollapsibleCard>
      )}

      {showReportModule && (
      <CollapsibleCard 
        title="分析报告" 
        icon={<FileText size={16} className="text-orange-500" />}
        defaultOpen={true}
        action={
          <div className="flex items-center gap-2">
            {stockCode && !reportProgress?.isGenerating && (
              <>
                <button 
                  onClick={() => generateReportMutation.mutate()}
                  disabled={generateReportMutation.isPending}
                  className="text-xs text-blue-500 hover:text-blue-400 flex items-center gap-1 disabled:opacity-50"
                  title="为当前股票生成分析报告"
                >
                  <FilePlus size={12} />
                  生成报告
                </button>
                <button 
                  onClick={() => generateLLMReportMutation.mutate()}
                  disabled={generateLLMReportMutation.isPending}
                  className="text-xs text-purple-500 hover:text-purple-400 flex items-center gap-1 disabled:opacity-50"
                  title="生成LLM智能评估报告（包含技术面、基本面、消息面分析及买卖点建议）"
                >
                  <Zap size={12} />
                  AI评估
                </button>
              </>
            )}
            <button 
              onClick={() => navigate('/reports')}
              className="text-xs text-blue-500 hover:text-blue-400 flex items-center"
            >
              全部 <ChevronRight size={12} />
            </button>
          </div>
        }
      >
        <div className="p-2 space-y-2 max-h-80 overflow-y-auto">
          {/* 进度显示 */}
          {reportProgress?.isGenerating && (
            <div className={`p-3 border ${
              isDark 
                ? 'bg-blue-950/30 border-blue-900/50' 
                : 'bg-blue-50 border-blue-200'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                <Loader2 size={14} className="animate-spin text-blue-500" />
                <span className={`text-xs font-medium ${isDark ? 'text-blue-400' : 'text-blue-700'}`}>
                  {reportProgress.message}
                </span>
              </div>
              <div className={`w-full h-2 ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}>
                <div 
                  className="h-2 bg-blue-500 transition-all duration-300"
                  style={{ width: `${reportProgress.progress}%` }}
                />
              </div>
              <div className={`text-xs mt-1 text-right ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                {reportProgress.progress}%
              </div>
            </div>
          )}
          
          {/* LLM报告生成进度 */}
          {llmReportProgress?.isGenerating && (
            <div className={`p-3 border ${
              isDark 
                ? 'bg-purple-950/30 border-purple-900/50' 
                : 'bg-purple-50 border-purple-200'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                <Loader2 size={14} className="animate-spin text-purple-500" />
                <span className={`text-xs font-medium ${isDark ? 'text-purple-400' : 'text-purple-700'}`}>
                  {llmReportProgress.message}
                </span>
              </div>
              <div className={`w-full h-2 ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}>
                <div 
                  className="h-2 bg-purple-500 transition-all duration-300"
                  style={{ width: `${llmReportProgress.progress}%` }}
                />
              </div>
              <div className={`text-xs mt-1 text-right ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                {llmReportProgress.progress}%
              </div>
            </div>
          )}
          
          {/* 最新生成的LLM报告 */}
          {latestLLMReport && !llmReportProgress?.isGenerating && (
            <div className={`p-3 border ${
              isDark 
                ? 'bg-gradient-to-r from-purple-950/30 to-transparent border-purple-900/50' 
                : 'bg-gradient-to-r from-purple-50 to-white border-purple-200'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-bold ${isDark ? 'text-purple-400' : 'text-purple-700'}`}>
                    AI智能评估报告
                  </span>
                  <Zap size={12} className="text-purple-500" />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                <div className={`p-2 ${isDark ? 'bg-[#1a1a1a]' : 'bg-white'}`}>
                  <div className={isDark ? 'text-gray-500' : 'text-gray-500'}>股票</div>
                  <div className={`font-bold ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>
                    {latestLLMReport.stock_name}
                  </div>
                </div>
                <div className={`p-2 ${isDark ? 'bg-[#1a1a1a]' : 'bg-white'}`}>
                  <div className={isDark ? 'text-gray-500' : 'text-gray-500'}>状态</div>
                  <div className={`font-bold ${isDark ? 'text-purple-400' : 'text-purple-700'}`}>
                    已完成
                  </div>
                </div>
              </div>
              
              {latestLLMReport.markdown && (
                <div className={`p-2 mt-2 text-xs ${isDark ? 'bg-[#1a1a1a] text-gray-300' : 'bg-white text-gray-700'} max-h-60 overflow-y-auto`}>
                  <div className={`font-medium mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    报告摘要
                  </div>
                  <div className="whitespace-pre-wrap">
                    {latestLLMReport.markdown.substring(0, 300)}...
                  </div>
                </div>
              )}
              
              <button
                onClick={() => {
                  if (latestLLMReport.report_path) {
                    const fileName = latestLLMReport.report_path.split('/').pop() || latestLLMReport.report_path.split('\\').pop();
                    if (fileName) {
                      openReportModal(
                        fileName,
                        latestLLMReport.stock_name,
                        latestLLMReport.report_date,
                        latestLLMReport.stock_code
                      );
                    }
                  }
                }}
                className={`w-full mt-2 text-xs py-1.5 ${
                  isDark 
                    ? 'bg-purple-900/50 hover:bg-purple-900/70 text-purple-400' 
                    : 'bg-purple-100 hover:bg-purple-200 text-purple-700'
                }`}
              >
                查看完整报告
              </button>
            </div>
          )}
          
          {/* 报告列表 */}
          {latestGeneratedReport && !reportProgress?.isGenerating && (
            <div className={`p-3 border ${
              isDark 
                ? 'bg-gradient-to-r from-green-950/30 to-transparent border-green-900/50' 
                : 'bg-gradient-to-r from-green-50 to-white border-green-200'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-bold ${isDark ? 'text-green-400' : 'text-green-700'}`}>
                    ✅ 报告生成成功
                  </span>
                </div>
                <span className={`text-xs font-bold ${
                  latestGeneratedReport.predict_direction === '上涨' ? 'text-red-500' : 
                  latestGeneratedReport.predict_direction === '下跌' ? 'text-green-500' : isDark ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  {latestGeneratedReport.predict_direction}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                <div className={`p-2 ${isDark ? 'bg-[#1a1a1a]' : 'bg-white'}`}>
                  <div className={isDark ? 'text-gray-500' : 'text-gray-500'}>股票</div>
                  <div className={`font-bold ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>
                    {latestGeneratedReport.stock_name}
                  </div>
                </div>
                <div className={`p-2 ${isDark ? 'bg-[#1a1a1a]' : 'bg-white'}`}>
                  <div className={isDark ? 'text-gray-500' : 'text-gray-500'}>综合评分</div>
                  <div className="font-bold text-orange-500">
                    {latestGeneratedReport.overall_score?.toFixed(1)}
                  </div>
                </div>
              </div>
              
              {latestGeneratedReport.summary && (
                <div className={`p-2 mt-2 text-xs ${isDark ? 'bg-[#1a1a1a] text-gray-300' : 'bg-white text-gray-700'}`}>
                  <div className={`font-medium mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    智能分析摘要
                  </div>
                  <div className="whitespace-pre-wrap line-clamp-4">
                    {latestGeneratedReport.summary.substring(0, 200)}...
                  </div>
                </div>
              )}
              
              <button
                onClick={() => navigate('/reports')}
                className={`w-full mt-2 text-xs py-1.5 ${
                  isDark 
                    ? 'bg-blue-900/50 hover:bg-blue-900/70 text-blue-400' 
                    : 'bg-blue-100 hover:bg-blue-200 text-blue-700'
                }`}
              >
                查看完整报告
              </button>
            </div>
          )}
          
          {/* 报告列表 */}
          {loadingReports ? (
            <div className="animate-pulse space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className={`h-12 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
              ))}
            </div>
          ) : latestReports?.reports && latestReports.reports.length > 0 ? (
            latestReports.reports
              .filter((report: any) => 
                !latestGeneratedReport || 
                report.stock_code !== latestGeneratedReport.stock_code ||
                report.report_date !== latestGeneratedReport.report_date
              )
              .slice(0, 2)
              .map((report: any) => (
              <div 
                key={report.id} 
                className={`p-2 cursor-pointer transition-colors ${isDark ? 'bg-[#1a1a1a] hover:bg-[#2a2a2a]' : 'bg-gray-50 hover:bg-gray-100'}`}
                onClick={() => navigate('/reports')}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>{report.stock_name}</span>
                    <span className={`text-xs font-mono ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{report.stock_code}</span>
                  </div>
                  <span className={`text-xs font-bold ${
                    report.predict_direction === '上涨' ? 'text-red-500' : 
                    report.predict_direction === '下跌' ? 'text-green-500' : isDark ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    {report.predict_direction}
                  </span>
                </div>
                <div className={`flex items-center justify-between text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                  <span>{report.report_date}</span>
                  <span>评分: <span className="font-bold text-orange-500">{report.overall_score?.toFixed(1)}</span></span>
                </div>
              </div>
            ))
          ) : (
            <div className={`text-center py-3 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              {stockCode ? '暂无分析报告，点击"生成报告"按钮创建' : '选择股票后生成分析报告'}
            </div>
          )}
          
          {/* LLM报告列表 */}
          {llmReports?.reports && llmReports.reports.length > 0 && (
            <div className="mt-3">
              <div className={`text-xs font-medium mb-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                AI智能评估报告
              </div>
              {llmReports.reports.slice(0, 2).map((report: any, index: number) => (
                <div 
                  key={index} 
                  className={`p-2 mb-1 cursor-pointer transition-colors ${
                    isDark ? 'bg-[#1a1a1a] hover:bg-[#2a2a2a]' : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                  onClick={() => openReportModal(
                    report.file_name,
                    report.stock_name,
                    report.date,
                    report.stock_code
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Zap size={12} className="text-purple-500" />
                      <span className={`text-xs font-bold ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                        {report.stock_name}
                      </span>
                    </div>
                    <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      {report.date}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CollapsibleCard>
      )}
      </div>
    </>
  );
}
