import { useTheme } from '../contexts/ThemeContext';
import FinancialTab from './FinancialTab';
import IndustryMarketTab from './IndustryMarketTab';
import BotChatTabEnhanced from './BotChatTabEnhanced';

type TabValue = 'financial' | 'industry' | 'bot';

interface RightPanelProps {
  activeTab: TabValue;
  onTabChange: (tab: TabValue) => void;
  selectedStockCode: string | null;
  selectedStockSector?: string;
  isResizing?: boolean;
}

export default function RightPanel({
  activeTab,
  onTabChange,
  selectedStockCode,
  selectedStockSector,
  isResizing = false
}: RightPanelProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className="h-full w-full overflow-hidden flex flex-col">
      <div className={`h-full shadow-sm overflow-hidden flex flex-col transition-colors duration-300 ${isResizing ? 'transition-none duration-0' : ''} rounded-lg ${
        isDark ? 'bg-[#1a1a1a] border border-[#2a2a2a]' : 'bg-white border border-gray-200'
      }`}>
        {/* TAB导航 */}
        <div className={`flex items-center gap-1 px-2 py-1 border-b flex-shrink-0 transition-colors duration-300 ${
          isDark ? 'border-[#2a2a2a] bg-[#1a1a1a]' : 'border-gray-100 bg-gray-50/50'
        }`}>
          <button
            onClick={() => onTabChange('financial')}
            className={`min-w-[100px] px-6 py-1.5 text-[11px] font-bold transition-all ${
              activeTab === 'financial'
                ? `bg-blue-600 text-white shadow-sm`
                : isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            📊 财务
          </button>
          <button
            onClick={() => onTabChange('industry')}
            className={`min-w-[100px] px-6 py-1.5 text-[11px] font-bold transition-all ${
              activeTab === 'industry'
                ? `bg-blue-600 text-white shadow-sm`
                : isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            🏭 行业
          </button>
          <button
            onClick={() => onTabChange('bot')}
            className={`min-w-[100px] px-6 py-1.5 text-[11px] font-bold transition-all ${
              activeTab === 'bot'
                ? `bg-blue-600 text-white shadow-sm`
                : isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            🤖 Bot
          </button>
        </div>

        {/* TAB内容 - 确保内容区域可滚动 */}
        <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden">
          {activeTab === 'financial' && (
            <FinancialTab stockCode={selectedStockCode} />
          )}
          {activeTab === 'industry' && (
            <IndustryMarketTab sector={selectedStockSector} stockCode={selectedStockCode} />
          )}
          {activeTab === 'bot' && (
            <BotChatTabEnhanced />
          )}
        </div>
      </div>
    </div>
  );
}
