import { memo, useState, useCallback } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { BarChart2, Target, TrendingUp, Newspaper, ChevronRight, SlidersHorizontal } from 'lucide-react';
import KLineChartPanel from './KLineChartPanel';
import IntradayChartPanel from './IntradayChartPanel';
import NewsPanel from './NewsPanel';
import MarketSentimentCard from './MarketSentimentCard';
import SmartAnalysisTab from './SmartAnalysisTab';
import CollapsibleCard from './CollapsibleCard';
import marketNewsThemeRaw from '../config/marketNewsTheme.json?raw';

type ChartType = 'kline' | 'intraday';

interface MainGroupProps {
  selectedStock: any;
  selectedStockCode: string | null;
  selectedStockSector?: string;
  chartType: ChartType;
  onChartTypeChange: (type: ChartType) => void;
  klineData: any[] | undefined;
  loadingKline: boolean;
  intradayData: any;
  loadingIntraday: boolean;
  isResizing?: boolean;
}

interface MarketNewsThemeConfig {
  fontScale: {
    default: number;
    min: number;
    max: number;
    step: number;
  };
  rowTheme: {
    light: {
      odd: string;
      even: string;
    };
    dark: {
      odd: string;
      even: string;
    };
  };
}

const defaultMarketNewsThemeConfig: MarketNewsThemeConfig = {
  fontScale: {
    default: 0.9,
    min: 0.75,
    max: 1.05,
    step: 0.05
  },
  rowTheme: {
    light: {
      odd: '#ffffff',
      even: '#f8fafc'
    },
    dark: {
      odd: '#1a1a1a',
      even: '#141414'
    }
  }
};

const marketNewsThemeConfig: MarketNewsThemeConfig = (() => {
  try {
    const parsed = JSON.parse(marketNewsThemeRaw) as Partial<MarketNewsThemeConfig>;
    return {
      fontScale: {
        ...defaultMarketNewsThemeConfig.fontScale,
        ...parsed.fontScale
      },
      rowTheme: {
        light: {
          ...defaultMarketNewsThemeConfig.rowTheme.light,
          ...parsed.rowTheme?.light
        },
        dark: {
          ...defaultMarketNewsThemeConfig.rowTheme.dark,
          ...parsed.rowTheme?.dark
        }
      }
    };
  } catch {
    return defaultMarketNewsThemeConfig;
  }
})();

const MainGroup = memo(({
  selectedStock,
  selectedStockCode,
  selectedStockSector,
  chartType,
  onChartTypeChange,
  klineData,
  loadingKline,
  intradayData,
  loadingIntraday,
  isResizing = false
}: MainGroupProps) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const [trendMode, setTrendMode] = useState<boolean>(false);
  const [compactLineMode, setCompactLineMode] = useState<boolean>(false);
  const [goToLatestTrigger, setGoToLatestTrigger] = useState<number>(0);
  const [showNews, setShowNews] = useState<boolean>(true);
  const [newsFontScale, setNewsFontScale] = useState<number>(marketNewsThemeConfig.fontScale.min);

  const handleGoToLatest = useCallback(() => {
    setGoToLatestTrigger(prev => prev + 1);
  }, []);

  const toolbarContainerClass = isDark
    ? 'flex items-center gap-1.5 px-1.5 py-1 border border-[#2f3d55] bg-[#121a26]'
    : 'flex items-center gap-1.5 px-1.5 py-1 border border-blue-100 bg-blue-50/70';
  const iconButtonBaseClass = isDark
    ? 'p-1.5 transition-all text-[#9fb4d1] hover:bg-[#1d2a3d] hover:text-[#dce8ff] active:scale-95'
    : 'p-1.5 transition-all text-[#4a6b96] hover:bg-white hover:text-[#1f4f8a] active:scale-95';
  const activeIconButtonClass = 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-sm';
  const chartSwitchContainerClass = isDark
    ? 'flex p-1 border border-[#2f3d55] bg-[#121a26]'
    : 'flex p-1 border border-blue-100 bg-blue-50/70';
  const chartSwitchButtonClass = 'px-3 py-1 text-xs font-bold transition-all active:scale-95';
  const chartSwitchActiveClass = 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-sm';
  const chartSwitchInactiveClass = isDark
    ? 'text-[#9fb4d1] hover:bg-[#1d2a3d] hover:text-[#dce8ff]'
    : 'text-[#4a6b96] hover:bg-white hover:text-[#1f4f8a]';

  return (
    <div className="h-full w-full min-w-0 overflow-hidden flex flex-col">
      <div className={`h-full min-w-0 shadow-sm overflow-hidden flex flex-col transition-colors duration-300 rounded-lg ${
        isDark ? 'bg-[#1a1a1a] border border-[#2a2a2a]' : 'bg-white border border-gray-200'
      }`}>
        {/* 头部 */}
        <div className={`flex items-center justify-between px-4 py-2.5 border-b flex-shrink-0 transition-colors duration-300 ${
          isDark 
            ? 'border-[#2a2a2a] bg-[#1a1a1a]' 
            : 'border-gray-100 bg-white'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 flex items-center justify-center rounded-lg transition-colors ${
              isDark ? 'bg-blue-500/10 text-blue-400' : 'bg-blue-50 text-blue-600'
            }`}>
              <BarChart2 size={20} />
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <h3 className={`text-lg font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  {selectedStock?.name || '选择股票'} 
                </h3>
                <span className={`px-4 py-2 rounded-xl text-sm font-mono font-black tracking-[0.14em] shadow-md ${
                  isDark ? 'bg-blue-500/30 text-blue-50' : 'bg-blue-100 text-blue-900'
                }`}>
                  {selectedStockCode || '--'}
                </span>
              </div>
              {selectedStock && (
                <div className="flex items-center gap-2 min-w-[120px]">
                  <div className={`text-xl font-mono font-bold leading-none ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    {selectedStock?.price?.toFixed(2) || '--'}
                  </div>
                  <div className={`text-[12px] font-bold leading-none ${
                    (selectedStock?.change_pct || 0) >= 0 ? 'text-red-500' : 'text-green-500'
                  }`}>
                    {(selectedStock?.change_pct || 0) >= 0 ? '▲' : '▼'}
                    {Math.abs(selectedStock?.change_pct || 0).toFixed(2)}%
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className={toolbarContainerClass}>
              <button
                onClick={() => setShowNews(!showNews)}
                aria-label={showNews ? '收起市场动态' : '展开市场动态'}
                aria-pressed={showNews}
                title={showNews ? "收起市场动态" : "展开市场动态"}
                className={`${iconButtonBaseClass} ${
                  showNews
                    ? activeIconButtonClass
                    : ''
                }`}
              >
                <Newspaper size={16} />
              </button>

              <div className={`w-px h-4 mx-1 ${isDark ? 'bg-[#2f3d55]' : 'bg-blue-200'}`} />

              {chartType === 'kline' && (
                <>
                  <button
                    onClick={handleGoToLatest}
                    aria-label="回到最新"
                    title="回到最新"
                    className={iconButtonBaseClass}
                  >
                    <Target size={16} />
                  </button>
                  <button
                    onClick={() => setTrendMode(!trendMode)}
                    aria-label="切换趋势模式"
                    aria-pressed={trendMode}
                    title="趋势模式 (EMA21/MA21)"
                    className={`${iconButtonBaseClass} ${
                      trendMode
                        ? activeIconButtonClass
                        : ''
                    }`}
                  >
                    <TrendingUp size={16} />
                  </button>
                  <button
                    onClick={() => setCompactLineMode(!compactLineMode)}
                    aria-label="切换精简曲线"
                    aria-pressed={compactLineMode}
                    title="精简曲线 (EMA9/EMA21/MA21/MA120)"
                    className={`${iconButtonBaseClass} ${
                      compactLineMode
                        ? activeIconButtonClass
                        : ''
                    }`}
                  >
                    <SlidersHorizontal size={16} />
                  </button>
                </>
              )}
            </div>

            <div className={chartSwitchContainerClass}>
              <button
                onClick={() => onChartTypeChange('kline')}
                className={`${chartSwitchButtonClass} ${
                  chartType === 'kline'
                    ? chartSwitchActiveClass
                    : chartSwitchInactiveClass
                }`}
              >
                K线
              </button>
              <button
                onClick={() => onChartTypeChange('intraday')}
                className={`${chartSwitchButtonClass} ${
                  chartType === 'intraday'
                    ? chartSwitchActiveClass
                    : chartSwitchInactiveClass
                }`}
              >
                分时
              </button>
            </div>

          </div>
        </div>
        
        {/* 图表与市场动态区域 */}
        <div className="flex-1 min-w-0 flex overflow-hidden relative">
          {/* 图表区域 */}
          <div className={`flex-1 min-w-0 relative overflow-hidden transition-all duration-300 ease-in-out ${isResizing ? 'transition-none duration-0' : ''} ${isDark ? 'bg-[#0a0a0a]' : 'bg-white'}`}>
            {chartType === 'kline' ? (
              <KLineChartPanel 
                loading={loadingKline}
                data={klineData}
                stockCode={selectedStockCode!}
                stockName={selectedStock?.name || ''}
                trendMode={trendMode}
                compactLineMode={compactLineMode}
                goToLatestTrigger={goToLatestTrigger}
              />
            ) : (
              <IntradayChartPanel 
                loading={loadingIntraday}
                data={intradayData?.data}
                stockCode={selectedStockCode!}
                stockName={selectedStock?.name || ''}
                avgPrice={intradayData?.avg_price}
                preClose={intradayData?.pre_close}
              />
            )}
          </div>

          {/* 市场动态侧边栏 - 增加平滑过渡和遮罩 */}
          <div className={`flex-shrink-0 transition-all duration-300 ease-in-out border-l overflow-hidden flex flex-col ${isResizing ? 'transition-none duration-0' : ''} ${
            showNews ? 'w-80 opacity-100' : 'w-0 opacity-0 border-transparent'
          } ${
            isDark ? 'border-[#2a2a2a] bg-[#1a1a1a]' : 'border-gray-100 bg-gray-50'
          }`}>
            <div className="w-80 flex flex-col h-full"> {/* 固定宽度防止过渡时内容抖动 */}
              <div className={`px-4 py-2 border-b flex items-center justify-between flex-shrink-0 ${isDark ? 'border-[#2a2a2a]' : 'border-gray-100'}`}>
                <div className="flex items-center gap-2">
                  <Newspaper size={14} className="text-blue-500" />
                  <span className={`text-xs font-bold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>市场动态</span>
                </div>
                <button 
                  onClick={() => setShowNews(false)}
                  aria-label="收起市场动态侧栏"
                  title="收起市场动态侧栏"
                  className={`p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors`}
                >
                  <ChevronRight size={14} className="opacity-60" />
                </button>
              </div>
              <div className="flex-1 min-h-0 overflow-y-auto p-2 space-y-2">
                <MarketSentimentCard />

                <CollapsibleCard
                  title="市场新闻"
                  icon={<Newspaper size={14} className="text-blue-500" />}
                  defaultOpen={true}
                  action={
                    <div className={`flex items-center gap-1.5 px-1.5 py-1 rounded-lg border ${
                      isDark ? 'border-[#2f3d55] bg-[#121a26]' : 'border-blue-100 bg-blue-50/70'
                    }`}>
                      <span className={`text-[10px] ${isDark ? 'text-[#9fb4d1]' : 'text-[#4a6b96]'}`}>字号</span>
                      <input
                        type="range"
                        min={marketNewsThemeConfig.fontScale.min}
                        max={marketNewsThemeConfig.fontScale.max}
                        step={marketNewsThemeConfig.fontScale.step}
                        value={newsFontScale}
                        onChange={(e) => setNewsFontScale(Number(e.target.value))}
                        className={`news-font-scale-slider w-10 h-1.5 rounded-full appearance-none ${
                          isDark ? 'bg-[#2a3a52]' : 'bg-blue-200'
                        }`}
                        style={{ accentColor: isDark ? '#38bdf8' : '#2563eb' }}
                        title="调节市场新闻字体大小"
                      />
                    </div>
                  }
                >
                  <div className="p-2">
                    <div className="min-h-[320px] h-[52vh] overflow-hidden relative">
                      <NewsPanel 
                        key={`${selectedStockSector || 'market'}-${selectedStockCode || 'none'}`}
                        sectorName={selectedStockSector}
                        marketMode={true}
                        recentDays={7}
                        fallbackToHot={true}
                        limit={20}
                        compact={true}
                        fontScale={newsFontScale}
                        isDark={isDark}
                        themeConfig={marketNewsThemeConfig}
                      />
                    </div>
                  </div>
                </CollapsibleCard>

                <SmartAnalysisTab
                  stockCode={selectedStockCode}
                  stockSector={selectedStockSector}
                  mode="marketOnly"
                  containerClassName="flex flex-col gap-2"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

export default MainGroup;
