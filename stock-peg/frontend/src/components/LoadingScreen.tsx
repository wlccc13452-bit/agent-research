import { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { CheckCircle, Clock, Loader2 } from 'lucide-react';
import { clientLogger } from '../services/clientLogger';

interface LoadingStep {
  id: string;
  name: string;
  status: 'pending' | 'loading' | 'completed';
  duration?: number;
  startTime?: number;
}

interface LoadingScreenProps {
  onComplete: () => void;
  loadingStates?: {
    holdings?: boolean;
    quotes?: boolean;
    config?: boolean;
    websocket?: boolean;
    analysis?: boolean;
    serverPreload?: boolean; // 保留但不使用
  };
}

export default function LoadingScreen({ onComplete, loadingStates }: LoadingScreenProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  
  // 记录初始化开始
  useEffect(() => {
    clientLogger.info('loading', '正在初始化智能仪表盘', { 
      userAgent: navigator.userAgent,
      url: window.location.href 
    });
    console.log('📊 [客户端日志] 正在初始化智能仪表盘');
  }, []);
  
  const [steps, setSteps] = useState<LoadingStep[]>([
    { id: 'websocket', name: '建立服务器推送连接', status: 'pending' },
    { id: 'config', name: '读取个性化布局配置', status: 'pending' },
    { id: 'holdings', name: '加载个人持仓数据', status: 'pending' },
    { id: 'quotes', name: '加载本地行情数据', status: 'pending' },
    { id: 'analysis', name: '初始化智能分析引擎', status: 'pending' },
    { id: 'ui', name: '渲染可视化交互界面', status: 'pending' },
  ]);

  const [isComplete, setIsComplete] = useState(false);
  const [totalTime, setTotalTime] = useState(0);
  const [startTime] = useState(Date.now());
  const [logs, setLogs] = useState<string[]>(['正在启动系统核心...', '初始化环境参数...']);
  
  // 详细的进度统计
  const [detailedProgress, setDetailedProgress] = useState<{
    total: number;
    current: number;
    success: number;
    failed: number;
    currentCode: string;
    elapsed: number;
  }>({
    total: 0,
    current: 0,
    success: 0,
    failed: 0,
    currentCode: '',
    elapsed: 0
  });

  // 监听服务端进度消息（后台更新进度，不再阻塞加载）
  useEffect(() => {
    const handleWebSocketMessage = (event: Event) => {
      const customEvent = event as CustomEvent;
      const message = customEvent.detail;

      if (message.type === 'startup_progress' || message.type === 'background_update_progress') {
        if (message.progress) {
          setDetailedProgress({
            total: message.progress.total || 0,
            current: message.progress.current || 0,
            success: message.progress.success || 0,
            failed: message.progress.failed || 0,
            currentCode: message.progress.current_code || '',
            elapsed: message.progress.elapsed || 0
          });
          clientLogger.info('loading', '服务端预加载进度更新', {
            stage: message.progress.stage,
            total: message.progress.total || 0,
            current: message.progress.current || 0,
            success: message.progress.success || 0,
            failed: message.progress.failed || 0,
            currentCode: message.progress.current_code || '',
            elapsed: message.progress.elapsed || 0
          }, undefined, message.progress.current_code || undefined);
        }
        
        if (message.message) {
          addLog(`[服务端] ${message.message}`);
          clientLogger.info('loading', `服务端消息: ${message.message}`, {
            stage: message.progress?.stage,
            currentCode: message.progress?.current_code || ''
          }, undefined, message.progress?.current_code || undefined);
        }
      }
    };

    window.addEventListener('websocket-message', handleWebSocketMessage);
    return () => window.removeEventListener('websocket-message', handleWebSocketMessage);
  }, []);
  
  // 添加日志
  const addLog = (msg: string) => {
    setLogs(prev => [msg, ...prev.slice(0, 4)]);
  };

  // 根据加载状态添加日志
  useEffect(() => {
    if (!loadingStates) return;
    
    // 只有在状态发生变化时才记录日志
    const logsToAdd: string[] = [];
    
    if (loadingStates.websocket === false) {
      logsToAdd.push('WebSocket 连接成功，实时行情频道已开启');
      clientLogger.info('loading', 'WebSocket连接成功', { step: 'websocket' });
    } else if (loadingStates.websocket === true) {
      logsToAdd.push('正在尝试建立 WebSocket 实时连接...');
      clientLogger.info('loading', '正在建立WebSocket连接', { step: 'websocket' });
    }
    
    if (loadingStates.holdings === false) {
      logsToAdd.push('持仓数据加载完成，共解析多个板块');
      clientLogger.info('loading', '持仓数据加载完成', { step: 'holdings' });
    } else if (loadingStates.holdings === true) {
      addLog('正在从后端获取持仓数据...');
      clientLogger.info('loading', '正在加载持仓数据', { step: 'holdings' });
    }
    
    if (loadingStates.quotes === false) {
      logsToAdd.push('本地行情数据加载完成');
      clientLogger.info('loading', '本地行情加载完成', { step: 'quotes' });
    } else if (loadingStates.quotes === true) {
      logsToAdd.push('正在从本地读取行情数据...');
      clientLogger.info('loading', '正在加载本地行情', { step: 'quotes' });
    }

    // 避免重复记录相同的日志（简单的去重）
    logsToAdd.forEach(msg => {
      setLogs(prev => {
        if (prev[0] === msg) return prev;
        return [msg, ...prev.slice(0, 4)];
      });
    });
    
    // 手动刷新日志
    clientLogger.manualFlush();
  }, [loadingStates?.websocket, loadingStates?.holdings, loadingStates?.quotes]);

  // 当没有提供 loadingStates 时，运行模拟加载序列
  useEffect(() => {
    if (loadingStates) return;
    
    let mounted = true;
    const loadSequence = async () => {
      for (let i = 0; i < steps.length; i++) {
        if (!mounted) break;
        
        const stepStartTime = Date.now();
        setSteps(prev => prev.map((s, idx) => 
          idx === i ? { ...s, status: 'loading' } : s
        ));
        
        // 增加服务端同步的模拟时间
        const delay = steps[i].id === 'server_preload' ? 2000 : 800 + Math.random() * 600;
        await new Promise(resolve => setTimeout(resolve, delay));
        
        if (!mounted) break;
        const duration = Date.now() - stepStartTime;
        setSteps(prev => prev.map((s, idx) => 
          idx === i ? { ...s, status: 'completed', duration } : s
        ));
      }
    };
    
    loadSequence();
    return () => { mounted = false; };
  }, [loadingStates === undefined]); // 仅在没有 loadingStates 时运行一次

  // 当loadingStates变化时更新步骤状态
  useEffect(() => {
    if (!loadingStates || isComplete) return;
    
    setSteps(prev => {
      // 检查当前状态，避免无效更新触发重绘
      const websocketDone = !loadingStates.websocket;
      const holdingsDone = !loadingStates.holdings;
      const quotesDone = !loadingStates.quotes;
      const otherStepsDone = websocketDone && holdingsDone && quotesDone;
      
      const nextSteps: LoadingStep[] = prev.map(s => {
        // 1. WebSocket
        if (s.id === 'websocket') {
          if (websocketDone && s.status !== 'completed') {
            clientLogger.logLoadingComplete('建立实时行情连接', 450, true);
            return { ...s, status: 'completed' as const, duration: 450 };
          } else if (!websocketDone && s.status === 'pending') {
            clientLogger.logLoadingStart('建立实时行情连接');
            return { ...s, status: 'loading' as const };
          }
        }
        
        // 2. 配置 (总是瞬间完成)
        if (s.id === 'config' && s.status === 'pending') {
          clientLogger.logLoadingComplete('读取个性化布局配置', 150, true);
          return { ...s, status: 'completed' as const, duration: 150 };
        }
        
        // 3. 持仓
        if (s.id === 'holdings') {
          if (holdingsDone && s.status !== 'completed') {
            clientLogger.logLoadingComplete('加载个人持仓数据', 800, true);
            return { ...s, status: 'completed' as const, duration: 800 };
          } else if (!holdingsDone && s.status === 'pending') {
            clientLogger.logLoadingStart('加载个人持仓数据');
            return { ...s, status: 'loading' as const };
          }
        }
        
        // 4. 行情
        if (s.id === 'quotes') {
          if (quotesDone && s.status !== 'completed') {
            clientLogger.logLoadingComplete('加载本地行情数据', 600, true);
            return { ...s, status: 'completed' as const, duration: 600 };
          } else if (holdingsDone && s.status === 'pending') {
            clientLogger.logLoadingStart('加载本地行情数据');
            return { ...s, status: 'loading' as const };
          }
        }
        
        // 5. 分析引擎
        if (s.id === 'analysis') {
          const isAnalysisDoneProp = loadingStates.analysis === false;
          const shouldAutoComplete = loadingStates.analysis === undefined && otherStepsDone;
          const canStartAnalysis = websocketDone && holdingsDone && quotesDone;
          
          if ((isAnalysisDoneProp || shouldAutoComplete) && s.status !== 'completed') {
            clientLogger.logLoadingComplete('初始化智能分析引擎', 1200, true);
            return { ...s, status: 'completed' as const, duration: 1200 };
          } else if (canStartAnalysis && s.status === 'pending') {
            clientLogger.logLoadingStart('初始化智能分析引擎');
            return { ...s, status: 'loading' as const };
          }
        }
        
        // 6. UI渲染
        if (s.id === 'ui') {
          const analysisDone = prev.find(p => p.id === 'analysis')?.status === 'completed';
          if (analysisDone && s.status !== 'completed') {
            clientLogger.logLoadingComplete('渲染可视化交互界面', 300, true);
            return { ...s, status: 'completed' as const, duration: 300 };
          } else if (otherStepsDone && s.status === 'pending') {
            clientLogger.logLoadingStart('渲染可视化交互界面');
            return { ...s, status: 'loading' as const };
          }
        }
        
        return s;
      });
      
      // 只有在真正发生变化时才返回新数组，防止无限循环
      const hasChanged = JSON.stringify(nextSteps) !== JSON.stringify(prev);
      
      // 手动刷新日志
      if (hasChanged) {
        clientLogger.manualFlush();
      }
      
      return hasChanged ? nextSteps : prev;
    });
  }, [loadingStates, isComplete]);

  // 单独检查是否全部完成
  useEffect(() => {
    if (isComplete) return;
    
    const allCompleted = steps.every(s => s.status === 'completed');
    if (allCompleted) {
      const totalDuration = Date.now() - startTime;
      setTotalTime(totalDuration);
      setIsComplete(true);
      
      // 记录初始化完成
      clientLogger.info('loading', '智能仪表盘初始化完成', { 
        totalDuration,
        steps: steps.length 
      });
      
      // 手动刷新日志
      clientLogger.manualFlush();
      
      console.log(`📊 [客户端日志] 初始化完成，总耗时: ${(totalDuration / 1000).toFixed(2)}s`);
    }
  }, [steps, isComplete, startTime]);
  
  const completedCount = steps.filter(s => s.status === 'completed').length;
  const progress = (completedCount / steps.length) * 100;
  
  return (
    <div className={`fixed inset-0 flex items-center justify-center ${
      isDark 
        ? 'bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0a0a0a]' 
        : 'bg-gradient-to-br from-gray-50 via-white to-gray-100'
    }`}>
      <div className={`w-full max-w-2xl p-8 ${
        isDark 
          ? 'bg-[#1a1a1a] border border-[#2a2a2a] shadow-2xl' 
          : 'bg-white border border-gray-200 shadow-xl'
      } rounded-lg`}>
        
        {/* 标题 */}
        <div className="text-center mb-8">
          <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${
            isDark ? 'bg-blue-900/30' : 'bg-blue-50'
          }`}>
            {isComplete ? (
              <CheckCircle className="w-8 h-8 text-green-500" />
            ) : (
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            )}
          </div>
          <h1 className={`text-2xl font-bold mb-2 ${
            isDark ? 'text-white' : 'text-gray-900'
          }`}>
            {isComplete ? '初始化完成' : '正在初始化智能仪表盘...'}
          </h1>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            {isComplete 
              ? `总耗时: ${(totalTime / 1000).toFixed(2)}秒` 
              : `进度: ${completedCount}/${steps.length}`
            }
          </p>
        </div>
        
        {/* 进度条 */}
        <div className="space-y-3 mb-8">
          {/* 主进度条 */}
          <div className={`h-2 rounded-full ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}>
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                isComplete ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
          
          {/* 详细进度（仅在服务端预加载阶段显示） */}
          {detailedProgress.total > 0 && !isComplete && (
            <div className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">数据更新进度</span>
                <span className="font-mono">
                  {detailedProgress.current} / {detailedProgress.total}
                </span>
              </div>
              
              {/* 详细进度条 */}
              <div className={`h-3 rounded-full overflow-hidden ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}>
                <div className="h-full flex">
                  {/* 成功部分 */}
                  {detailedProgress.success > 0 && (
                    <div 
                      className="bg-green-500 transition-all duration-300"
                      style={{ width: `${(detailedProgress.success / detailedProgress.total) * 100}%` }}
                      title={`成功: ${detailedProgress.success}`}
                    />
                  )}
                  {/* 失败部分 */}
                  {detailedProgress.failed > 0 && (
                    <div 
                      className="bg-red-500 transition-all duration-300"
                      style={{ width: `${(detailedProgress.failed / detailedProgress.total) * 100}%` }}
                      title={`失败: ${detailedProgress.failed}`}
                    />
                  )}
                </div>
              </div>
              
              {/* 当前正在更新的股票 */}
              {detailedProgress.currentCode && (
                <div className="flex items-center justify-between mt-2 text-xs">
                  <span className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    当前: {detailedProgress.currentCode}
                  </span>
                  <span className={`font-mono ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    耗时: {detailedProgress.elapsed.toFixed(1)}s
                  </span>
                </div>
              )}
              
              {/* 统计信息 */}
              <div className="flex items-center gap-4 mt-2 text-xs">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  成功: {detailedProgress.success}
                </span>
                {detailedProgress.failed > 0 && (
                  <span className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-red-500" />
                    失败: {detailedProgress.failed}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
        
        {/* 步骤列表 */}
        <div className="space-y-3 mb-8">
          {steps.map((step) => (
            <div 
              key={step.id}
              className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                step.status === 'loading' 
                  ? isDark ? 'bg-blue-900/20' : 'bg-blue-50'
                  : isDark ? 'bg-[#0a0a0a]' : 'bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-3">
                {/* 状态图标 */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  step.status === 'completed' 
                    ? 'bg-green-500/20'
                    : step.status === 'loading'
                      ? 'bg-blue-500/20'
                      : isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'
                }`}>
                  {step.status === 'completed' ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : step.status === 'loading' ? (
                    <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                  ) : (
                    <Clock className={`w-5 h-5 ${
                      isDark ? 'text-gray-600' : 'text-gray-400'
                    }`} />
                  )}
                </div>
                
                {/* 步骤名称 */}
                <span className={`font-medium ${
                  step.status === 'pending' 
                    ? isDark ? 'text-gray-600' : 'text-gray-400'
                    : isDark ? 'text-white' : 'text-gray-900'
                }`}>
                  {step.name}
                </span>
              </div>
              
              {/* 耗时 */}
              {step.duration && (
                <span className={`text-sm font-mono ${
                  isDark ? 'text-gray-500' : 'text-gray-600'
                }`}>
                  {(step.duration / 1000).toFixed(2)}s
                </span>
              )}
            </div>
          ))}
        </div>

        {/* 实时日志输出 */}
        <div className={`p-4 rounded border font-mono text-xs h-32 overflow-hidden mb-8 ${
          isDark 
            ? 'bg-[#0a0a0a] border-[#2a2a2a] text-blue-400/80' 
            : 'bg-gray-50 border-gray-200 text-blue-600/80'
        }`}>
          <div className="flex flex-col gap-1">
            {logs.map((log, i) => (
              <div key={i} className={i === 0 ? 'animate-pulse' : 'opacity-60'}>
                <span className="mr-2">[{new Date().toLocaleTimeString()}]</span>
                {log}
              </div>
            ))}
          </div>
        </div>
        
        {/* 完成按钮 */}
        {isComplete && (
          <div className="text-center">
            <button
              onClick={onComplete}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              进入智能仪表盘
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

