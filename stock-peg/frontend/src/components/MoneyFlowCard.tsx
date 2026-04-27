import { useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { marketApi } from '../services/api';
import { DollarSign, TrendingUp, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import CollapsibleCard from './CollapsibleCard';
import { useTheme } from '../contexts/ThemeContext';

export default function MoneyFlowCard() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const queryClient = useQueryClient();
  const [wsConnected, setWsConnected] = useState<boolean>(() => Boolean((window as any).__stockPegWsConnected));
  const lastInvalidateRef = useRef(0);

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
      if (now - lastInvalidateRef.current < 20000) return;
      lastInvalidateRef.current = now;
      queryClient.invalidateQueries({ queryKey: ['north-money-flow'] });
      queryClient.invalidateQueries({ queryKey: ['north-money-top10'] });
      queryClient.invalidateQueries({ queryKey: ['sector-fund-flow'] });
    };

    const onMessage = (event: Event) => {
      const message = (event as CustomEvent).detail;
      const messageType = message?.type;
      if (!messageType) return;
      if (messageType === 'market_data_updated' || messageType === 'quote' || messageType === 'quote_updated') {
        invalidate();
      }
    };

    window.addEventListener('websocket-message', onMessage);
    window.addEventListener('market-data-updated', invalidate);
    return () => {
      window.removeEventListener('websocket-message', onMessage);
      window.removeEventListener('market-data-updated', invalidate);
    };
  }, [queryClient]);

  const { data: northFlow, isLoading: loadingNorth } = useQuery({
    queryKey: ['north-money-flow'],
    queryFn: marketApi.getNorthMoneyFlow,
    refetchInterval: wsConnected ? false : 60000,
  });

  const { data: northTop10, isLoading: loadingTop10 } = useQuery({
    queryKey: ['north-money-top10'],
    queryFn: marketApi.getNorthMoneyTop10,
    refetchInterval: wsConnected ? false : 5 * 60000,
  });

  const { data: sectorFlow, isLoading: loadingSectorFlow } = useQuery({
    queryKey: ['sector-fund-flow'],
    queryFn: () => marketApi.getSectorFundFlow('行业'),
    refetchInterval: wsConnected ? false : 60000,
  });

  return (
    <div className="space-y-2">
      {/* 北向资金 */}
      <CollapsibleCard
        title="北向资金"
        icon={<DollarSign size={16} className="text-emerald-500" />}
        defaultOpen={true}
      >
        <div className="p-3">
          {loadingNorth ? (
            <div className="animate-pulse space-y-2">
              <div className={`h-12 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}></div>
              <div className={`h-6 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}></div>
            </div>
          ) : northFlow ? (
            <div className="space-y-3">
              {/* 当日净流入 */}
              <div className={`p-3 rounded border ${
                isDark 
                  ? 'bg-gradient-to-br from-blue-950/30 to-blue-900/20 border-blue-900/50' 
                  : 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200'
              }`}>
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-medium ${isDark ? 'text-blue-400' : 'text-blue-700'}`}>当日净流入</span>
                  <div className="flex items-center gap-1">
                    {(northFlow.net_inflow || 0) >= 0 ? (
                      <ArrowUpRight size={14} className="text-red-500" />
                    ) : (
                      <ArrowDownRight size={14} className="text-green-500" />
                    )}
                    <span className={`text-lg font-bold ${
                      (northFlow.net_inflow || 0) >= 0 ? 'text-red-500' : 'text-green-500'
                    }`}>
                      {northFlow.net_inflow >= 0 ? '+' : ''}{(northFlow.net_inflow / 100000000).toFixed(2)}亿
                    </span>
                  </div>
                </div>
                <div className={`mt-2 text-xs flex justify-between ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <span>资金余额: {(northFlow.balance / 100000000).toFixed(2)}亿</span>
                  <span>累计: {(northFlow.accumulate / 100000000).toFixed(2)}亿</span>
                </div>
              </div>
            </div>
          ) : (
            <div className={`text-center py-3 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>暂无北向资金数据</div>
          )}
        </div>
      </CollapsibleCard>

      {/* 北向持股前十 */}
      <CollapsibleCard
        title="北向持股 TOP10"
        icon={<TrendingUp size={16} className="text-orange-500" />}
        defaultOpen={false}
      >
        <div className="max-h-48 overflow-y-auto">
          {loadingTop10 ? (
            <div className="animate-pulse space-y-2 p-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className={`h-8 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}></div>
              ))}
            </div>
          ) : northTop10?.stocks && northTop10.stocks.length > 0 ? (
            <div className={`divide-y ${isDark ? 'divide-[#2a2a2a]' : 'divide-gray-100'}`}>
              {northTop10.stocks.slice(0, 10).map((stock: any, index: number) => (
                <div key={index} className={`p-2 transition-colors ${isDark ? 'hover:bg-[#1a1a1a]' : 'hover:bg-gray-50'}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-medium w-5 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{index + 1}</span>
                      <div>
                        <div className={`text-xs font-medium ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>{stock.name}</div>
                        <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{stock.code}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-xs font-bold ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>
                        {(stock.hold_value / 100000000).toFixed(2)}亿
                      </div>
                      <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        {stock.hold_pct?.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={`text-center py-3 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>暂无持股数据</div>
          )}
        </div>
      </CollapsibleCard>

      {/* 板块资金流向 */}
      <CollapsibleCard
        title="板块资金流向"
        icon={<DollarSign size={16} className="text-purple-500" />}
        defaultOpen={false}
      >
        <div className="max-h-48 overflow-y-auto">
          {loadingSectorFlow ? (
            <div className="animate-pulse space-y-2 p-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className={`h-10 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}></div>
              ))}
            </div>
          ) : sectorFlow?.flows && sectorFlow.flows.length > 0 ? (
            <div className={`divide-y ${isDark ? 'divide-[#2a2a2a]' : 'divide-gray-100'}`}>
              {sectorFlow.flows.slice(0, 10).map((flow: any, index: number) => (
                <div key={index} className={`p-2 transition-colors ${isDark ? 'hover:bg-[#1a1a1a]' : 'hover:bg-gray-50'}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className={`text-xs font-medium ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>{flow.name}</div>
                      <div className={`text-xs ${flow.change_pct >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                        {flow.change_pct >= 0 ? '+' : ''}{flow.change_pct?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-xs font-bold ${
                        (flow.main_net_inflow || 0) >= 0 ? 'text-red-500' : 'text-green-500'
                      }`}>
                        {(flow.main_net_inflow / 100000000).toFixed(2)}亿
                      </div>
                      <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        {flow.main_net_inflow_pct?.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={`text-center py-3 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>暂无资金流向数据</div>
          )}
        </div>
      </CollapsibleCard>
    </div>
  );
}
