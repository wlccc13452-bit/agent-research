import { Activity, ChevronDown } from 'lucide-react';

interface IndicesPanelHeaderProps {
  count: number;
  isDark: boolean;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export default function IndicesPanelHeader({
  count,
  isDark,
  collapsed = false,
  onToggleCollapse,
}: IndicesPanelHeaderProps) {
  return (
    <div className={`flex items-center justify-between px-3 py-2 border-b flex-shrink-0 ${
      isDark ? 'border-[#2a2a2a]' : 'border-gray-200'
    }`}>
      <button
        type="button"
        onClick={onToggleCollapse}
        className={`flex items-center gap-2 min-w-0 text-left transition-colors ${
          isDark ? 'hover:text-white' : 'hover:text-gray-900'
        }`}
      >
        <span className={`w-6 h-6 flex items-center justify-center rounded ${
          isDark ? 'bg-blue-900/30 text-blue-300' : 'bg-blue-50 text-blue-600'
        }`}>
          <Activity size={13} />
        </span>
        <div>
          <h3 className={`font-bold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>市场指数</h3>
          <p className="text-xs text-gray-500">共 {count} 个指数</p>
        </div>
      </button>
      <button
        type="button"
        onClick={onToggleCollapse}
        className={`p-1 transition-colors ${
          isDark ? 'text-gray-500 hover:text-gray-300 hover:bg-[#2a2a2a]' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
        }`}
        title={collapsed ? '展开市场指数' : '折叠市场指数'}
      >
        <ChevronDown size={14} className={`transition-transform ${collapsed ? '-rotate-90' : 'rotate-0'}`} />
      </button>
    </div>
  );
}
