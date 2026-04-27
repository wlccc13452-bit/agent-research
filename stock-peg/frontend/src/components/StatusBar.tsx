import { useWebSocket } from '../hooks/useWebSocket';
import { useTheme } from '../contexts/ThemeContext';
import { Clock, Database, RefreshCw, Sun, Moon } from 'lucide-react';
import { useEffect, useState } from 'react';

interface BackgroundUpdateProgress {
  stage: 'init' | 'ready' | 'updating' | 'complete' | 'error';
  step?: string;
  total?: number;
  current?: number;
  success?: number;
  failed?: number;
  current_code?: string;
  elapsed?: number;
  error?: string;
}

interface StatusBarProps {
  className?: string;
}

export default function StatusBar({ className = '' }: StatusBarProps) {
  const { isConnected } = useWebSocket();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';
  
  // 后台更新进度
  const [backgroundProgress, setBackgroundProgress] = useState<BackgroundUpdateProgress | null>(null);
  
  // 监听后台更新进度
  useEffect(() => {
    const handleWebSocketMessage = (event: Event) => {
      const customEvent = event as CustomEvent;
      const message = customEvent.detail;
      
      if (message.type === 'background_update_progress' || message.type === 'startup_progress') {
        setBackgroundProgress(message.progress);
        
        // 如果完成或错误，5秒后清除进度显示
        if (message.progress?.stage === 'complete' || message.progress?.stage === 'error') {
          setTimeout(() => setBackgroundProgress(null), 5000);
        }
      }
    };
    
    window.addEventListener('websocket-message', handleWebSocketMessage);
    return () => window.removeEventListener('websocket-message', handleWebSocketMessage);
  }, []);
  
  const now = new Date();
  const formattedTime = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  return (
    <div 
      className={`h-7 flex items-center justify-between px-3 text-[11px] flex-shrink-0 transition-colors duration-300 border-t ${
        isDark 
          ? 'bg-[#0a0a0a] text-gray-500 border-[#1a1a1a]' 
          : 'bg-gray-50 text-gray-500 border-gray-200'
      } ${className}`}
    >
      {/* 左侧：连接状态 */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.5)]' : 'bg-red-500 shadow-[0_0_5px_rgba(239,68,68,0.5)]'}`} />
          <span className={isConnected ? 'text-green-500/80' : 'text-red-500/80'}>
            {isConnected ? '实时就绪' : '连接断开'}
          </span>
        </div>
        
        <div className="flex items-center gap-1.5 opacity-80">
          <Database size={10} />
          <span>多源数据(CN/US)</span>
        </div>
      </div>

      {/* 中间：系统消息 + 后台更新进度 */}
      <div className="flex-1 flex justify-center px-4">
        {backgroundProgress ? (
          <div className={`flex items-center gap-3 px-2 py-0.5 rounded transition-all ${
            isDark ? 'bg-blue-500/5' : 'bg-blue-50'
          }`}>
            <RefreshCw size={10} className={`${backgroundProgress.stage !== 'complete' && backgroundProgress.stage !== 'error' ? 'animate-spin' : ''} text-blue-500`} />
            
            <div className="flex items-center gap-2">
              <span className="font-medium text-blue-500/90 whitespace-nowrap">
                {backgroundProgress.stage === 'init' && (backgroundProgress.step || '初始化服务...')}
                {backgroundProgress.stage === 'ready' && '数据同步中...'}
                {backgroundProgress.stage === 'updating' && `更新进度: ${backgroundProgress.current}/${backgroundProgress.total}`}
                {backgroundProgress.stage === 'complete' && '数据已是最新'}
                {backgroundProgress.stage === 'error' && (backgroundProgress.error || '同步异常')}
              </span>

              {backgroundProgress.stage === 'updating' && backgroundProgress.total && (
                <div className={`w-24 h-1 rounded-full overflow-hidden ${isDark ? 'bg-gray-800' : 'bg-gray-200'}`}>
                  <div 
                    className="h-full bg-blue-500 transition-all duration-500"
                    style={{ width: `${((backgroundProgress.current || 0) / backgroundProgress.total) * 100}%` }}
                  />
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-gray-500/60">
            <RefreshCw size={10} className="animate-spin opacity-40" />
            <span>自动监测中...</span>
          </div>
        )}
      </div>

      {/* 右侧：更新时间和主题切换 */}
      <div className="flex items-center gap-4">
        <button
          onClick={toggleTheme}
          className={`flex items-center gap-1.5 transition-all hover:opacity-100 opacity-60 ${isDark ? 'hover:text-yellow-400' : 'hover:text-blue-600'}`}
          title={theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'}
        >
          {theme === 'dark' ? <Sun size={11} /> : <Moon size={11} />}
          <span>{theme === 'dark' ? '深色' : '浅色'}</span>
        </button>
        
        <div className="flex items-center gap-1.5 opacity-60">
          <Clock size={11} />
          <span>{formattedTime}</span>
        </div>
      </div>
    </div>
  );
}
