import { useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { stocksApi, marketApi } from '../services/api';
import { Factory, TrendingUp, Activity, DollarSign, Info } from 'lucide-react';
import CollapsibleCard from './CollapsibleCard';
import { useTheme } from '../contexts/ThemeContext';
import SmartAnalysisTab from './SmartAnalysisTab';

interface IndustryMarketTabProps {
  sector: string | undefined;
  stockCode?: string | null;
}

interface SectorKlineItem {
  open: number;
  close: number;
  high: number;
  low: number;
}

const SECTOR_INDEX_MAP: Record<string, string> = {
  '白酒': 'BK0896',
  '新能源': 'BK0493',
  '半导体': 'BK0897',
  '医药': 'BK0727',
  '证券': 'BK0473',
  '汽车': 'BK0481',
  '银行': 'BK0477',
  '保险': 'BK0474',
  '地产': 'BK0451',
  '煤炭': 'BK0437',
  '钢铁': 'BK0479',
  '科技': 'BK0720',
  '通信': 'BK0448',
  '消费': 'BK0428',
  '铝': 'BK0478',
  '光伏': 'BK1031',
  '有色': 'BK0471',
  'AI': 'BK0800',
  '锂': 'BK1030',
  '芯片': 'BK0891',
  '算力': 'BK1135',
  '机器人': 'BK1090',
  '军工': 'BK0895',
  '电力': 'BK0426',
};

const SECTOR_KEYWORD_MAP: Array<{ keywords: string[]; indexCode: string }> = [
  { keywords: ['白酒', '酒'], indexCode: 'BK0896' },
  { keywords: ['新能源', '储能'], indexCode: 'BK0493' },
  { keywords: ['半导体', '芯片', '集成电路'], indexCode: 'BK0897' },
  { keywords: ['医药', '医疗', '生物'], indexCode: 'BK0727' },
  { keywords: ['证券', '券商'], indexCode: 'BK0473' },
  { keywords: ['汽车', '整车'], indexCode: 'BK0481' },
  { keywords: ['银行'], indexCode: 'BK0477' },
  { keywords: ['保险'], indexCode: 'BK0474' },
  { keywords: ['地产', '房地产'], indexCode: 'BK0451' },
  { keywords: ['煤炭', '煤化工'], indexCode: 'BK0437' },
  { keywords: ['钢铁'], indexCode: 'BK0479' },
  { keywords: ['科技', '计算机', '软件'], indexCode: 'BK0720' },
  { keywords: ['通信', '5g'], indexCode: 'BK0448' },
  { keywords: ['消费', '零售'], indexCode: 'BK0428' },
  { keywords: ['铝'], indexCode: 'BK0478' },
  { keywords: ['光伏', '太阳能'], indexCode: 'BK1031' },
  { keywords: ['有色', '铜', '黄金', '稀土'], indexCode: 'BK0471' },
  { keywords: ['ai', '人工智能'], indexCode: 'BK0800' },
  { keywords: ['锂', '锂电', '电池'], indexCode: 'BK1030' },
  { keywords: ['算力', '数据中心', '服务器'], indexCode: 'BK1135' },
  { keywords: ['机器人', '自动化'], indexCode: 'BK1090' },
  { keywords: ['军工', '国防', '航天'], indexCode: 'BK0895' },
  { keywords: ['电力', '电网', '公用事业'], indexCode: 'BK0426' },
];

const normalizeSectorName = (sector: string) =>
  sector.toLowerCase().replace(/[\s-_]/g, '').replace(/(板块|行业|概念|主题|指数)/g, '');

const resolveSectorIndexCode = (sector?: string) => {
  if (!sector) return null;
  const exactCode = SECTOR_INDEX_MAP[sector];
  if (exactCode) return exactCode;
  const normalizedSector = normalizeSectorName(sector);
  for (const [name, code] of Object.entries(SECTOR_INDEX_MAP)) {
    const normalizedName = normalizeSectorName(name);
    if (normalizedSector.includes(normalizedName) || normalizedName.includes(normalizedSector)) {
      return code;
    }
  }
  for (const item of SECTOR_KEYWORD_MAP) {
    if (item.keywords.some((keyword) => normalizedSector.includes(keyword.toLowerCase()))) {
      return item.indexCode;
    }
  }
  return null;
};

export default function IndustryMarketTab({ sector, stockCode }: IndustryMarketTabProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const queryClient = useQueryClient();
  const [wsConnected, setWsConnected] = useState<boolean>(() => Boolean((window as any).__stockPegWsConnected));
  const lastInvalidateRef = useRef(0);

  const resolvedSectorIndexCode = resolveSectorIndexCode(sector);

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
      if (sector) {
        queryClient.invalidateQueries({ queryKey: ['sector-index', sector] });
      }
      if (stockCode && !stockCode.startsWith('UNKNOWN')) {
        queryClient.invalidateQueries({ queryKey: ['fund-flow', stockCode] });
      }
    };

    const onMessage = (event: Event) => {
      const message = (event as CustomEvent).detail;
      const messageType = message?.type;
      if (!messageType) return;
      if (
        messageType === 'market_data_updated' ||
        messageType === 'sector_updated' ||
        messageType === 'quote' ||
        messageType === 'quote_updated'
      ) {
        invalidate();
      }
    };

    window.addEventListener('websocket-message', onMessage);
    window.addEventListener('market-data-updated', invalidate);
    return () => {
      window.removeEventListener('websocket-message', onMessage);
      window.removeEventListener('market-data-updated', invalidate);
    };
  }, [queryClient, resolvedSectorIndexCode, sector, stockCode]);
  
  // 使用专门的板块指数接口获取数据（不再调用通用quote接口，避免板块代码404错误）
  const { data: sectorIndexData, isLoading: loadingSectorIndexData } = useQuery({
    queryKey: ['sector-index', sector],
    queryFn: async () => {
      const response = await stocksApi.getSectorIndex(sector!);
      return response?.data || response;
    },
    enabled: !!sector,
    refetchInterval: wsConnected ? false : 45000,
  });

  const { data: fundFlow } = useQuery({
    queryKey: ['fund-flow', stockCode],
    queryFn: () => marketApi.getFundFlow(stockCode!),
    enabled: !!stockCode && !stockCode.startsWith('UNKNOWN'),
    refetchInterval: wsConnected ? false : 60000,
  });

  if (!sector) {
    return (
      <div className="h-full flex flex-col">
        <div className={`flex-1 flex items-center justify-center p-8 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
          <div className="text-center">
            <Factory size={32} className={`mx-auto mb-2 ${isDark ? 'text-gray-600' : 'text-gray-500'}`} />
            <p className="text-sm">选择股票后查看行业分析</p>
          </div>
        </div>
      </div>
    );
  }

  const sectorQuote = sectorIndexData?.quote || null;
  const sectorKline: SectorKlineItem[] = ((sectorIndexData?.klines) || []) as SectorKlineItem[];
  const loadingSectorQuote = loadingSectorIndexData;
  const loadingKline = loadingSectorIndexData;
  const displayIndexCode = sectorIndexData?.index_code || resolvedSectorIndexCode || null;

  const getTrend = () => {
    if (!sectorKline.length || sectorKline.length < 2) return null;
    const latest = sectorKline[sectorKline.length - 1];
    const prev = sectorKline[sectorKline.length - 2];
    const change = ((latest.close - prev.close) / prev.close) * 100;
    return {
      direction: change > 0 ? 'up' : change < 0 ? 'down' : 'flat',
      change: change.toFixed(2),
    };
  };

  const trend = getTrend();

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 min-h-0 overflow-auto">
        <div className="flex flex-col gap-2 p-2">
          <CollapsibleCard
            title={`${sector} 价格指数`}
            icon={<Factory size={16} className="text-indigo-500" />}
            defaultOpen={true}
          >
            <div className="p-2">
              {loadingSectorQuote ? (
                <div className="animate-pulse space-y-2">
                  <div className={`h-8 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
                  <div className={`h-4 rounded w-2/3 ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
                </div>
              ) : sectorQuote ? (
                <div className="space-y-2">
                  <div className="flex items-end justify-between">
                    <div>
                      <div className={`text-xl font-bold font-mono ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>
                        {sectorQuote.price?.toFixed(2) || '--'}
                      </div>
                      <div className={`text-xs font-medium ${sectorQuote.change_pct >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                        {sectorQuote.change_pct >= 0 ? '+' : ''}
                        {sectorQuote.change_pct?.toFixed(2) || '0.00'}%
                      </div>
                    </div>
                    <div className={`text-right text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                      <div>涨跌: {sectorQuote.change?.toFixed(2) || '--'}</div>
                      <div>昨收: {sectorQuote.pre_close?.toFixed(2) || '--'}</div>
                    </div>
                  </div>

                  {trend && (
                    <div className={`flex items-center gap-1 text-xs p-1.5 ${
                      trend.direction === 'up'
                        ? isDark ? 'bg-red-950/30 text-red-400' : 'bg-red-50 text-red-600'
                        : trend.direction === 'down'
                          ? isDark ? 'bg-green-950/30 text-green-400' : 'bg-green-50 text-green-600'
                          : isDark ? 'bg-[#2a2a2a] text-gray-400' : 'bg-gray-50 text-gray-600'
                    }`}>
                      <TrendingUp size={12} className={trend.direction === 'down' ? 'rotate-180' : ''} />
                      <span>近一日{trend.direction === 'up' ? '上涨' : trend.direction === 'down' ? '下跌' : '持平'} {trend.change}%</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className={`text-center py-3 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                  暂无行业指数数据 (指数代码: {displayIndexCode || '未配置'})
                </div>
              )}
            </div>
          </CollapsibleCard>

          {stockCode && fundFlow && (
            <CollapsibleCard
              title="资金流向"
              icon={<DollarSign size={16} className="text-emerald-500" />}
              defaultOpen={true}
            >
              <div className="p-2 space-y-2">
                <div className={`flex items-start gap-1.5 text-[11px] leading-4 p-1.5 rounded border ${
                  isDark ? 'bg-[#111111] border-[#2a2a2a] text-gray-400' : 'bg-blue-50 border-blue-100 text-gray-600'
                }`}>
                  <Info size={12} className="mt-0.5 flex-shrink-0 text-blue-500" />
                  <span title="主力净流入=大单资金净额，散户净流入=中小单资金净额；正值表示净买入，负值表示净卖出，占比仅反映当日强弱。">
                    主力净流入反映大单资金方向，散户净流入反映中小单方向；正负值仅代表当日净买卖结果。
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className={`p-2 rounded border ${
                    (fundFlow.main_net_inflow || 0) >= 0
                      ? isDark ? 'bg-red-950/30 border-red-900/50' : 'bg-red-50 border-red-200'
                      : isDark ? 'bg-green-950/30 border-green-900/50' : 'bg-green-50 border-green-200'
                  }`}>
                    <div className={`text-xs mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>主力净流入</div>
                    <div className={`text-sm font-bold ${(fundFlow.main_net_inflow || 0) >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                      {fundFlow.main_net_inflow >= 0 ? '+' : ''}{(fundFlow.main_net_inflow / 10000).toFixed(2)}万
                    </div>
                    <div className={`text-xs mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                      {fundFlow.main_net_inflow_pct?.toFixed(2)}%
                    </div>
                  </div>
                  <div className={`p-2 rounded border ${
                    (fundFlow.retail_net_inflow || 0) >= 0
                      ? isDark ? 'bg-red-950/30 border-red-900/50' : 'bg-red-50 border-red-200'
                      : isDark ? 'bg-green-950/30 border-green-900/50' : 'bg-green-50 border-green-200'
                  }`}>
                    <div className={`text-xs mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>散户净流入</div>
                    <div className={`text-sm font-bold ${(fundFlow.retail_net_inflow || 0) >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                      {fundFlow.retail_net_inflow >= 0 ? '+' : ''}{(fundFlow.retail_net_inflow / 10000).toFixed(2)}万
                    </div>
                    <div className={`text-xs mt-0.5 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                      {fundFlow.retail_net_inflow_pct?.toFixed(2)}%
                    </div>
                  </div>
                </div>
              </div>
            </CollapsibleCard>
          )}

          <CollapsibleCard
            title="板块走势概览"
            icon={<Activity size={16} className="text-purple-500" />}
            defaultOpen={false}
          >
            <div className="p-2">
              <div className={`flex items-start gap-1.5 text-[11px] leading-4 p-1.5 rounded border mb-2 ${
                isDark ? 'bg-[#111111] border-[#2a2a2a] text-gray-400' : 'bg-purple-50 border-purple-100 text-gray-600'
              }`}>
                <Info size={12} className="mt-0.5 flex-shrink-0 text-purple-500" />
                <span title="柱高按近10日高低区间归一化，仅用于观察强弱和节奏，不等同真实K线比例，也不构成交易建议。">
                  柱高是近10日相对位置的可视化，主要用于观察板块强弱节奏，不代表真实K线比例。
                </span>
              </div>
              {loadingKline ? (
                <div className={`animate-pulse h-20 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-100'}`}></div>
              ) : sectorKline && sectorKline.length > 0 ? (
                <div className="space-y-2">
                  <div className="flex items-end gap-1 h-16">
                    {sectorKline.slice(-10).map((k: SectorKlineItem, i: number) => {
                      const maxHigh = Math.max(...sectorKline.slice(-10).map((d: SectorKlineItem) => d.high));
                      const minLow = Math.min(...sectorKline.slice(-10).map((d: SectorKlineItem) => d.low));
                      const range = maxHigh - minLow || 1;
                      const height = ((k.close - minLow) / range) * 100;
                      const isUp = k.close >= k.open;

                      return (
                        <div
                          key={i}
                          className={`flex-1 rounded-t ${isUp ? 'bg-red-500' : 'bg-green-500'}`}
                          style={{ height: `${Math.max(height, 10)}%` }}
                        />
                      );
                    })}
                  </div>
                  <div className={`flex justify-between text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                    <span>10日前</span>
                    <span>今日</span>
                  </div>

                  <div className="grid grid-cols-3 gap-1.5 pt-1.5">
                    <div className={`p-1.5 text-center ${isDark ? 'bg-[#1a1a1a]' : 'bg-gray-50'}`}>
                      <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>最高</div>
                      <div className="text-xs font-mono font-bold text-red-500">
                        {Math.max(...sectorKline.slice(-10).map((d: SectorKlineItem) => d.high)).toFixed(2)}
                      </div>
                    </div>
                    <div className={`p-1.5 text-center ${isDark ? 'bg-[#1a1a1a]' : 'bg-gray-50'}`}>
                      <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>最低</div>
                      <div className="text-xs font-mono font-bold text-green-500">
                        {Math.min(...sectorKline.slice(-10).map((d: SectorKlineItem) => d.low)).toFixed(2)}
                      </div>
                    </div>
                    <div className={`p-1.5 text-center ${isDark ? 'bg-[#1a1a1a]' : 'bg-gray-50'}`}>
                      <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>振幅</div>
                      <div className={`text-sm font-mono font-bold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                        {(() => {
                          const high = Math.max(...sectorKline.slice(-5).map((d: SectorKlineItem) => d.high));
                          const low = Math.min(...sectorKline.slice(-5).map((d: SectorKlineItem) => d.low));
                          const lastClose = sectorKline[sectorKline.length - 6]?.close || low;
                          return ((high - low) / lastClose * 100).toFixed(1);
                        })()}%
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className={`text-center py-3 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                  暂无板块走势数据
                </div>
              )}
            </div>
          </CollapsibleCard>

          <SmartAnalysisTab
            stockCode={stockCode || null}
            stockSector={sector}
            mode="reportOnly"
            containerClassName="flex flex-col gap-2"
          />
        </div>
      </div>
    </div>
  );
}
