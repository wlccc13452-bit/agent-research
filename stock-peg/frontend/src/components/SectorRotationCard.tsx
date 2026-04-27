import { useQuery, useQueryClient } from '@tanstack/react-query';
import { marketApi, predictionApi } from '../services/api';
import { Layers, ChevronRight, TrendingUp, Sparkles } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import CollapsibleCard from './CollapsibleCard';
import { useTheme } from '../contexts/ThemeContext';

type TabType = 'industry' | 'concept' | 'prediction';

export default function SectorRotationCard() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const queryClient = useQueryClient();
  
  const [activeTab, setActiveTab] = useState<TabType>('industry');
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
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
      queryClient.invalidateQueries({ queryKey: ['industry-sectors'] });
      queryClient.invalidateQueries({ queryKey: ['concept-sectors'] });
      if (selectedSector) {
        queryClient.invalidateQueries({ queryKey: ['sector-stocks', selectedSector] });
      }
    };

    const onMessage = (event: Event) => {
      const message = (event as CustomEvent).detail;
      const messageType = message?.type;
      if (!messageType) return;
      if (
        messageType === 'sector_updated' ||
        messageType === 'market_data_updated' ||
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
  }, [queryClient, selectedSector]);

  const { data: industrySectors, isLoading: loadingIndustry } = useQuery({
    queryKey: ['industry-sectors'],
    queryFn: marketApi.getIndustrySectors,
    refetchInterval: wsConnected ? false : 60000,
  });

  const { data: conceptSectors, isLoading: loadingConcept } = useQuery({
    queryKey: ['concept-sectors'],
    queryFn: marketApi.getConceptSectors,
    refetchInterval: wsConnected ? false : 60000,
  });

  const { data: sectorStocks, isLoading: loadingStocks } = useQuery({
    queryKey: ['sector-stocks', selectedSector],
    queryFn: () => marketApi.getSectorStocks(selectedSector!),
    enabled: !!selectedSector,
    refetchInterval: wsConnected ? false : 60000,
  });

  const { data: rotationPrediction, isLoading: loadingPrediction } = useQuery({
    queryKey: ['sector-rotation-prediction'],
    queryFn: predictionApi.analyzeSectorRotation,
    refetchInterval: wsConnected ? false : 120000, // 2分钟更新一次
  });

  const sectors = activeTab === 'industry' ? industrySectors?.sectors : conceptSectors?.sectors;
  const isLoading = activeTab === 'industry' ? loadingIndustry : loadingConcept;

  return (
    <CollapsibleCard
      title="板块轮动"
      icon={<Layers size={16} className="text-indigo-500" />}
      defaultOpen={true}
    >
      <div className="p-0">
        {/* Tab切换 */}
        <div className={`flex border-b ${isDark ? 'border-[#2a2a2a]' : 'border-gray-200'}`}>
          <button
            onClick={() => {
              setActiveTab('industry');
              setSelectedSector(null);
            }}
            className={`flex-1 px-2 py-2 text-xs font-medium transition-colors ${
              activeTab === 'industry'
                ? 'text-blue-500 border-b-2 border-blue-500 ' + (isDark ? 'bg-blue-900/30' : 'bg-blue-50')
                : isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            行业板块
          </button>
          <button
            onClick={() => {
              setActiveTab('concept');
              setSelectedSector(null);
            }}
            className={`flex-1 px-2 py-2 text-xs font-medium transition-colors ${
              activeTab === 'concept'
                ? 'text-blue-500 border-b-2 border-blue-500 ' + (isDark ? 'bg-blue-900/30' : 'bg-blue-50')
                : isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            概念板块
          </button>
          <button
            onClick={() => setSelectedSector(null)}
            className={`flex-1 px-2 py-2 text-xs font-medium transition-colors flex items-center justify-center gap-1 ${
              activeTab === 'prediction'
                ? 'text-purple-500 border-b-2 border-purple-500 ' + (isDark ? 'bg-purple-900/30' : 'bg-purple-50')
                : isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Sparkles size={12} />
            预测
          </button>
        </div>

        {/* 板块列表或成分股列表 */}
        <div className="max-h-80 overflow-y-auto">
          {activeTab === 'prediction' ? (
            // 板块轮动预测
            <div className="p-3">
              {loadingPrediction ? (
                <div className="animate-pulse space-y-3">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className={`h-16 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}></div>
                  ))}
                </div>
              ) : rotationPrediction ? (
                <div className="space-y-3">
                  {/* 下一个热点板块预测 */}
                  {rotationPrediction.next_hotspot_prediction && (
                    <div className={`p-3 rounded-lg border-2 ${
                      isDark 
                        ? 'bg-gradient-to-r from-purple-900/30 to-pink-900/30 border-purple-500' 
                        : 'bg-gradient-to-r from-purple-50 to-pink-50 border-purple-300'
                    }`}>
                      <div className="flex items-center gap-2 mb-2">
                        <Sparkles size={14} className="text-purple-500" />
                        <span className={`text-xs font-bold ${isDark ? 'text-purple-300' : 'text-purple-700'}`}>
                          下一个热点板块
                        </span>
                      </div>
                      <div className={`text-lg font-bold ${isDark ? 'text-purple-200' : 'text-purple-900'}`}>
                        {rotationPrediction.next_hotspot_prediction}
                      </div>
                      <div className={`text-xs mt-1 ${isDark ? 'text-purple-400' : 'text-purple-600'}`}>
                        资金流入强度高,有望成为下一个热点
                      </div>
                    </div>
                  )}

                  {/* 当前热点板块 */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp size={14} className="text-orange-500" />
                      <span className={`text-xs font-bold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                        当前热点板块
                      </span>
                    </div>
                    <div className="space-y-2">
                      {rotationPrediction.hotspot_sectors?.map((sector: string, index: number) => {
                        const change = rotationPrediction.hotspot_changes?.[sector] || 0;
                        const flow = rotationPrediction.money_flow?.[sector] || 0;
                        const flowInYi = (flow / 10000).toFixed(2); // 转换为亿元
                        
                        return (
                          <div 
                            key={index}
                            className={`p-2 rounded ${
                              isDark ? 'bg-[#1a1a1a] hover:bg-[#2a2a2a]' : 'bg-gray-50 hover:bg-gray-100'
                            } transition-colors`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className={`text-xs font-bold w-5 h-5 rounded flex items-center justify-center ${
                                  index === 0
                                    ? isDark ? 'bg-orange-900/50 text-orange-400' : 'bg-orange-100 text-orange-600'
                                    : isDark ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-600'
                                }`}>
                                  {index + 1}
                                </span>
                                <span className={`text-xs font-medium ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>
                                  {sector}
                                </span>
                              </div>
                              <div className="text-right">
                                <div className={`text-xs font-bold ${
                                  change >= 0 ? 'text-red-500' : 'text-green-500'
                                }`}>
                                  {change >= 0 ? '+' : ''}{(change / 100).toFixed(2)}%
                                </div>
                                <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                                  {flow > 0 ? '+' : ''}{flowInYi}亿
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* 更新时间 */}
                  {rotationPrediction.timestamp && (
                    <div className={`text-xs text-center mt-3 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                      更新时间: {new Date(rotationPrediction.timestamp).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              ) : (
                <div className={`text-center py-6 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                  暂无预测数据
                </div>
              )}
            </div>
          ) : selectedSector ? (
            // 成分股列表
            <div>
              <div className={`sticky top-0 px-3 py-2 border-b flex items-center gap-2 ${
                isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-gray-50 border-gray-200'
              }`}>
                <button
                  onClick={() => setSelectedSector(null)}
                  className="text-blue-500 hover:text-blue-400 text-xs font-medium"
                >
                  ← 返回
                </button>
                <span className={`text-xs ${isDark ? 'text-gray-600' : 'text-gray-600'}`}>|</span>
                <span className={`text-xs font-medium ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>{selectedSector}</span>
              </div>

              {loadingStocks ? (
                <div className="animate-pulse space-y-2 p-3">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className={`h-12 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}></div>
                  ))}
                </div>
              ) : sectorStocks?.stocks && sectorStocks.stocks.length > 0 ? (
                <div className={`divide-y ${isDark ? 'divide-[#2a2a2a]' : 'divide-gray-100'}`}>
                  {sectorStocks.stocks.map((stock: any, index: number) => (
                    <div key={index} className={`p-2 transition-colors ${isDark ? 'hover:bg-[#1a1a1a]' : 'hover:bg-gray-50'}`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className={`text-xs font-medium ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>{stock.name}</div>
                          <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{stock.code}</div>
                        </div>
                        <div className="text-right">
                          <div className={`text-xs font-bold ${
                            (stock.change_pct || 0) >= 0 ? 'text-red-500' : 'text-green-500'
                          }`}>
                            {stock.change_pct >= 0 ? '+' : ''}{stock.change_pct?.toFixed(2)}%
                          </div>
                          {stock.price && (
                            <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{stock.price.toFixed(2)}</div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={`text-center py-6 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>暂无成分股数据</div>
              )}
            </div>
          ) : (
            // 板块列表
            <div>
              {isLoading ? (
                <div className="animate-pulse space-y-2 p-3">
                  {[...Array(8)].map((_, i) => (
                    <div key={i} className={`h-14 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}></div>
                  ))}
                </div>
              ) : sectors && sectors.length > 0 ? (
                <div className={`divide-y ${isDark ? 'divide-[#2a2a2a]' : 'divide-gray-100'}`}>
                  {sectors.slice(0, 20).map((sector: any, index: number) => (
                    <div
                      key={index}
                      onClick={() => setSelectedSector(sector.name)}
                      className={`p-2 transition-colors cursor-pointer ${isDark ? 'hover:bg-[#1a1a1a]' : 'hover:bg-gray-50'}`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs font-bold w-6 h-6 rounded flex items-center justify-center ${
                            (sector.change_pct || 0) >= 0 
                              ? isDark ? 'bg-red-900/50 text-red-400' : 'bg-red-100 text-red-600'
                              : isDark ? 'bg-green-900/50 text-green-400' : 'bg-green-100 text-green-600'
                          }`}>
                            {index + 1}
                          </span>
                          <div>
                            <div className={`text-xs font-medium ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>{sector.name}</div>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className={`text-xs ${
                                (sector.change_pct || 0) >= 0 ? 'text-red-500' : 'text-green-500'
                              }`}>
                                {sector.change_pct >= 0 ? '+' : ''}{sector.change_pct?.toFixed(2)}%
                              </span>
                              <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                                涨{sector.up_count || 0} 跌{sector.down_count || 0}
                              </span>
                            </div>
                          </div>
                        </div>
                        <ChevronRight size={14} className={isDark ? 'text-gray-600' : 'text-gray-300'} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={`text-center py-6 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>暂无板块数据</div>
              )}
            </div>
          )}
        </div>
      </div>
    </CollapsibleCard>
  );
}
