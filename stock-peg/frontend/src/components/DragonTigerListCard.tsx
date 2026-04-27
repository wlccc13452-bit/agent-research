import { useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { marketApi } from '../services/api';
import { Award, Star } from 'lucide-react';
import CollapsibleCard from './CollapsibleCard';
import { useTheme } from '../contexts/ThemeContext';

export default function DragonTigerListCard() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [days, setDays] = useState(1);
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
      if (now - lastInvalidateRef.current < 30000) return;
      lastInvalidateRef.current = now;
      queryClient.invalidateQueries({ queryKey: ['lhb-detail', days] });
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
  }, [queryClient, days]);

  const { data: lhbData, isLoading } = useQuery({
    queryKey: ['lhb-detail', days],
    queryFn: () => marketApi.getLHBDetail(days),
    refetchInterval: wsConnected ? false : 5 * 60000,
  });

  return (
    <CollapsibleCard
      title="龙虎榜"
      icon={<Award size={16} className="text-yellow-500" />}
      defaultOpen={false}
    >
      <div className="p-0">
        {/* 天数选择 */}
        <div className={`flex items-center gap-2 p-3 border-b ${
          isDark 
            ? 'border-[#2a2a2a] bg-[#1a1a1a]' 
            : 'border-gray-200 bg-gray-50'
        }`}>
          <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>查询范围:</span>
          {[1, 3, 5, 7].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                days === d
                  ? 'bg-blue-600 text-white'
                  : isDark 
                    ? 'bg-[#2a2a2a] text-gray-400 hover:bg-[#3a3a3a] border border-[#3a3a3a]'
                    : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-300'
              }`}
            >
              {d === 1 ? '今日' : `近${d}日`}
            </button>
          ))}
        </div>

        {/* 龙虎榜列表 */}
        <div className="max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="animate-pulse space-y-2 p-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className={`h-20 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}></div>
              ))}
            </div>
          ) : lhbData?.details && lhbData.details.length > 0 ? (
            <div className={`divide-y ${isDark ? 'divide-[#2a2a2a]' : 'divide-gray-100'}`}>
              {lhbData.details.map((item: any, index: number) => (
                <div key={index} className={`p-3 transition-colors ${
                  isDark ? 'hover:bg-[#1a1a1a]' : 'hover:bg-gray-50'
                }`}>
                  {/* 股票信息 */}
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-bold ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>{item.name}</span>
                        <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{item.code}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>收盘: {item.price?.toFixed(2)}</span>
                        <span className={`text-xs font-bold ${
                          (item.change_pct || 0) >= 0 ? 'text-red-500' : 'text-green-500'
                        }`}>
                          {item.change_pct >= 0 ? '+' : ''}{item.change_pct?.toFixed(2)}%
                        </span>
                        <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>换手: {item.turnover_rate?.toFixed(2)}%</span>
                      </div>
                    </div>
                  </div>

                  {/* 净买额 */}
                  <div className={`p-2 rounded border mb-2 ${
                    isDark 
                      ? 'bg-gradient-to-r from-yellow-950/30 to-orange-950/30 border-yellow-900/50' 
                      : 'bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200'
                  }`}>
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-medium ${isDark ? 'text-yellow-500' : 'text-yellow-700'}`}>龙虎榜净买额</span>
                      <div className={`text-base font-bold ${
                        (item.net_buy || 0) >= 0 ? 'text-red-500' : 'text-green-500'
                      }`}>
                        {item.net_buy >= 0 ? '+' : ''}{(item.net_buy / 10000).toFixed(2)}万
                      </div>
                    </div>
                  </div>

                  {/* 买卖金额 */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className={`p-2 rounded border ${
                      isDark 
                        ? 'bg-red-950/30 border-red-900/50' 
                        : 'bg-red-50 border-red-100'
                    }`}>
                      <div className="text-xs text-red-500 mb-0.5">买入额</div>
                      <div className="text-sm font-bold text-red-500">
                        {(item.buy_amount / 10000).toFixed(2)}万
                      </div>
                    </div>
                    <div className={`p-2 rounded border ${
                      isDark 
                        ? 'bg-green-950/30 border-green-900/50' 
                        : 'bg-green-50 border-green-100'
                    }`}>
                      <div className="text-xs text-green-500 mb-0.5">卖出额</div>
                      <div className="text-sm font-bold text-green-500">
                        {(item.sell_amount / 10000).toFixed(2)}万
                      </div>
                    </div>
                  </div>

                  {/* 上榜原因 */}
                  {item.reason && (
                    <div className="mt-2 flex items-start gap-1">
                      <Star size={12} className="text-yellow-500 flex-shrink-0 mt-0.5" />
                      <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.reason}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className={`text-center py-8 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              <Award size={32} className={`mx-auto mb-2 ${isDark ? 'text-gray-600' : 'text-gray-300'}`} />
              <p>暂无龙虎榜数据</p>
            </div>
          )}
        </div>
      </div>
    </CollapsibleCard>
  );
}
