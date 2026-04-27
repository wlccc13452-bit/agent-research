import { useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { predictionApi, usMarketApi } from '../services/api';
import { Layers, ShoppingBag } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

export default function SectorTrendPanel() {
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
      if (now - lastInvalidateRef.current < 15000) return;
      lastInvalidateRef.current = now;
      queryClient.invalidateQueries({ queryKey: ['sector-rotation'] });
      queryClient.invalidateQueries({ queryKey: ['market-indices'] });
    };

    const onMessage = (event: Event) => {
      const message = (event as CustomEvent).detail;
      const messageType = message?.type;
      if (!messageType) return;
      if (
        messageType === 'market_data_updated' ||
        messageType === 'sector_updated' ||
        messageType === 'us_index_updated' ||
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
  }, [queryClient]);

  const { data: sectorRotation, isLoading: loadingRotation, error: rotationError } = useQuery({
    queryKey: ['sector-rotation'],
    queryFn: predictionApi.analyzeSectorRotation,
    refetchInterval: wsConnected ? false : 60000,
  });

  const { data: indicesResponse, isLoading: loadingIndices, error: indicesError } = useQuery({
    queryKey: ['market-indices'],
    queryFn: usMarketApi.getIndices,
    refetchInterval: wsConnected ? false : 60000,
  });

  // 提取实际数据（适配新的API格式）
  const indices = indicesResponse?.data || indicesResponse;

  if (loadingRotation || loadingIndices) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className={`h-48 animate-pulse ${isDark ? 'bg-[#1a1a1a]' : 'bg-gray-100'}`}></div>
        <div className={`h-48 animate-pulse ${isDark ? 'bg-[#1a1a1a]' : 'bg-gray-100'}`}></div>
      </div>
    );
  }

  const hotSectors = sectorRotation?.hotspot_sectors || [];
  const hotspotChanges = sectorRotation?.hotspot_changes || {};
  const moneyFlow = sectorRotation?.money_flow || {};
  const nextHotspot = sectorRotation?.next_hotspot_prediction;

  const industryProxies = [
    { symbol: 'AA', name: '铝业趋势', description: 'Alcoa Corp' },
    { symbol: 'XME', name: '有色金属', description: 'Metals ETF' },
    { symbol: 'TAN', name: '光伏新能源', description: 'Solar ETF' },
    { symbol: 'BOTZ', name: 'AI人工智能', description: 'AI & Robotics' }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* 行业板块轮动 */}
      <div className={`p-4 border shadow-sm ${isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-100'}`}>
        <div className={`flex items-center gap-2 mb-4 border-b pb-2 ${isDark ? 'border-[#2a2a2a]' : 'border-gray-50'}`}>
          <Layers size={16} className="text-purple-500" />
          <h3 className={`text-sm font-bold ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>行业板块热度</h3>
        </div>
        
        {rotationError ? (
          <div className="text-xs text-red-500 py-8 text-center">
            数据加载失败
          </div>
        ) : hotSectors.length === 0 ? (
          <div className={`text-xs py-8 text-center ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
            暂无板块数据
          </div>
        ) : (
          <div className="space-y-3">
            {hotSectors.map((sector: string) => {
              const changePct = typeof hotspotChanges[sector] === 'number' ? hotspotChanges[sector] : 0;
              const flow = typeof moneyFlow[sector] === 'number' ? moneyFlow[sector] : 0;
              const isUp = changePct >= 0;

              return (
                <div key={sector} className={`flex items-center justify-between group p-2 transition-colors ${
                  isDark ? 'hover:bg-[#2a2a2a]' : 'hover:bg-gray-50'
                }`}>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 ${isUp ? 'bg-red-500' : 'bg-green-500'}`} />
                    <span className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{sector}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className={`text-xs font-bold ${isUp ? 'text-red-500' : 'text-green-500'}`}>
                        {isUp ? '+' : ''}
                        {changePct.toFixed(2)}%
                      </div>
                      <div className={`text-[10px] font-mono ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        资金: {flow.toFixed(0)}w
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
            
            {nextHotspot && (
              <div className={`mt-4 pt-3 border-t border-dashed ${isDark ? 'border-[#2a2a2a]' : 'border-gray-100'}`}>
                <span className="text-[10px] font-bold text-purple-500 uppercase tracking-widest block mb-1">明日潜力预测</span>
                <div className={`text-sm font-bold flex items-center gap-2 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                  🚀 {nextHotspot} 板块
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 关联大宗商品/美股行业 */}
      <div className={`p-4 border shadow-sm ${isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-100'}`}>
        <div className={`flex items-center gap-2 mb-4 border-b pb-2 ${isDark ? 'border-[#2a2a2a]' : 'border-gray-50'}`}>
          <ShoppingBag size={16} className="text-orange-500" />
          <h3 className={`text-sm font-bold ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>关联市场动态</h3>
        </div>
        
        {indicesError ? (
          <div className="text-xs text-red-500 py-8 text-center">
            数据加载失败
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {industryProxies.map((proxy) => {
              const stockData = indices?.[proxy.symbol];
              const price = typeof stockData?.price === 'number' ? stockData.price : 0;
              const changePct = typeof stockData?.change_pct === 'number' ? stockData.change_pct : 0;
              const isUp = changePct >= 0;
              
              return (
                <div key={proxy.symbol} className={`p-3 transition-colors ${
                  isDark ? 'bg-[#0a0a0a] hover:bg-[#2a2a2a]' : 'bg-gray-50 hover:bg-gray-100'
                }`}>
                  <div className="flex justify-between items-start mb-1">
                    <div>
                      <div className={`text-[10px] font-bold uppercase ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{proxy.name}</div>
                      <div className={`text-xs font-bold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{proxy.symbol}</div>
                    </div>
                    {price > 0 ? (
                      <div className={`text-[10px] font-bold ${isUp ? 'text-red-500' : 'text-green-500'}`}>
                        {isUp ? '+' : ''}{changePct.toFixed(2)}%
                      </div>
                    ) : null}
                  </div>
                  {price > 0 ? (
                    <div className={`text-sm font-mono font-bold ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>
                      ${price.toFixed(2)}
                    </div>
                  ) : (
                    <div className={`text-[10px] mt-1 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      暂无实时数据
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
