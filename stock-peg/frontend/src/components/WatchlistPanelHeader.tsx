import type { ReactNode } from 'react';
import { ChevronDown, Star } from 'lucide-react';

interface WatchlistPanelHeaderProps {
  count: number;
  isDark: boolean;
  actions?: ReactNode;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export default function WatchlistPanelHeader({
  count,
  isDark,
  actions,
  collapsed = false,
  onToggleCollapse,
}: WatchlistPanelHeaderProps) {
  return (
    <div className={`flex items-center justify-between px-3 py-2 border-b flex-shrink-0 ${
      isDark ? 'border-[#2a2a2a]' : 'border-gray-200'
    }`}>
      <div className="flex items-center gap-2 min-w-0">
        <button
          type="button"
          onClick={onToggleCollapse}
          className={`flex items-center gap-2 min-w-0 text-left transition-colors ${
            isDark ? 'hover:text-white' : 'hover:text-gray-900'
          }`}
        >
          <span className={`w-6 h-6 flex items-center justify-center rounded ${
            isDark ? 'bg-amber-900/30 text-amber-300' : 'bg-amber-50 text-amber-600'
          }`}>
            <Star size={13} />
          </span>
          <div>
            <h3 className={`font-bold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>动态关注股票</h3>
            <p className="text-xs text-gray-500">共 {count} 只</p>
          </div>
        </button>
      </div>
      <div className="flex items-center gap-1">
        {actions}
        <button
          type="button"
          onClick={onToggleCollapse}
          className={`p-1 transition-colors ${
            isDark ? 'text-gray-500 hover:text-gray-300 hover:bg-[#2a2a2a]' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
          }`}
          title={collapsed ? '展开动态关注股票' : '折叠动态关注股票'}
        >
          <ChevronDown size={14} className={`transition-transform ${collapsed ? '-rotate-90' : 'rotate-0'}`} />
        </button>
      </div>
    </div>
  );
}
