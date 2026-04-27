import { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { CheckCircle, Clock, Loader2, ChevronDown, ChevronRight } from 'lucide-react';
import { clientLogger } from '../services/clientLogger';

interface LoadingSubStep {
  id: string;
  name: string;
  status: 'pending' | 'loading' | 'completed';
  detail?: string;
  duration?: number;
}

interface LoadingStep {
  id: string;
  name: string;
  status: 'pending' | 'loading' | 'completed';
  duration?: number;
  startTime?: number;
  subSteps?: LoadingSubStep[];
  expanded?: boolean;
}

interface EnhancedLoadingScreenProps {
  onComplete: () => void;
  loadingStates?: {
    holdings?: boolean;
    quotes?: boolean;
    config?: boolean;
    websocket?: boolean;
    analysis?: boolean;
    serverPreload?: boolean;
    // 新增：详细的持仓加载信息
    holdingsDetail?: {
      totalSectors: number;
      currentSector: number;
      totalStocks: number;
      currentStock: number;
      currentSectorName: string;
      currentStockName: string;
    };
  };
}

export default function EnhancedLoadingScreen({ onComplete, loadingStates }: EnhancedLoadingScreenProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  
  // 记录初始化开始
  useEffect(() => {
    clientLogger.info('loading', '系统初始化开始', {
      startTime: new Date().toISOString(),
      loadingStates
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  
  const [steps, setSteps] = useState<LoadingStep[]>([
    { 
      id: 'websocket', 
      name: '建立服务器推送连接', 
      status: 'pending',
      expanded: false,
      subSteps: [
        { id: 'ws-init', name: '初始化通信协议', status: 'pending' },
        { id: 'ws-connect', name: '连接后台服务器', status: 'pending' },
        { id: 'ws-subscribe', name: '准备数据推送通道', status: 'pending' }
      ]
    },
    { 
      id: 'config', 
      name: '读取个性化布局配置', 
      status: 'pending',
      expanded: false,
      subSteps: [
        { id: 'cfg-read', name: '读取配置文件', status: 'pending' },
        { id: 'cfg-validate', name: '验证配置参数', status: 'pending' }
      ]
    },
    { 
      id: 'holdings', 
      name: '加载个人自持股票', 
      status: 'pending',
      expanded: true, // 默认展开自持股票加载详情
      subSteps: [
        { id: 'holdings-fetch', name: '获取自持股票列表', status: 'pending', detail: '从数据库读取自持配置' },
        { id: 'holdings-parse', name: '解析板块信息', status: 'pending', detail: '解析板块和股票数据' },
        { id: 'holdings-validate', name: '验证自持数据', status: 'pending', detail: '检查股票代码有效性' }
      ]
    },
    { 
      id: 'quotes', 
      name: '加载本地行情数据', 
      status: 'pending',
      expanded: false,
      subSteps: [
        { id: 'quotes-request', name: '请求本地行情数据', status: 'pending' },
        { id: 'quotes-parse', name: '解析行情数据', status: 'pending' },
        { id: 'quotes-merge', name: '准备本地数据视图', status: 'pending' }
      ]
    },
    { 
      id: 'analysis', 
      name: '初始化智能分析引擎', 
      status: 'pending',
      expanded: false,
      subSteps: [
        { id: 'analysis-load', name: '加载分析模型', status: 'pending' },
        { id: 'analysis-init', name: '初始化计算引擎', status: 'pending' }
      ]
    },
    { 
      id: 'ui', 
      name: '渲染可视化交互界面', 
      status: 'pending',
      expanded: false,
      subSteps: [
        { id: 'ui-components', name: '加载UI组件', status: 'pending' },
        { id: 'ui-layout', name: '计算布局位置', status: 'pending' },
        { id: 'ui-render', name: '渲染图表', status: 'pending' }
      ]
    },
  ]);

  const [isComplete, setIsComplete] = useState(false);
  const [totalTime, setTotalTime] = useState(0);
  const [startTime] = useState(Date.now());
  const [logs] = useState<string[]>(['正在启动系统核心...', '初始化环境参数...']);
  
  // 持仓详细进度
  const [holdingsProgress, setHoldingsProgress] = useState({
    totalSectors: 0,
    currentSector: 0,
    totalStocks: 0,
    currentStock: 0,
    currentSectorName: '',
    currentStockName: ''
  });
  
  // 最大加载时间（30秒）
  const MAX_LOADING_TIME = 30000;

  // 切换步骤展开状态
  const toggleStepExpanded = (stepId: string) => {
    setSteps(prev => prev.map(s => 
      s.id === stepId ? { ...s, expanded: !s.expanded } : s
    ));
  };

  // 当loadingStates变化时更新步骤状态
  useEffect(() => {
    if (!loadingStates || isComplete) return;
    
    setSteps(prev => {
      const websocketDone = !loadingStates.websocket;
      const holdingsDone = !loadingStates.holdings;
      const quotesDone = !loadingStates.quotes;
      const otherStepsDone = websocketDone && holdingsDone && quotesDone;
      
      // 更新持仓进度详情
      if (loadingStates.holdingsDetail) {
        setHoldingsProgress(loadingStates.holdingsDetail);
      }
      
      const nextSteps: LoadingStep[] = prev.map(s => {
        // WebSocket
        if (s.id === 'websocket') {
          if (websocketDone && s.status !== 'completed') {
            return { 
              ...s, 
              status: 'completed' as const, 
              duration: 450,
              subSteps: s.subSteps?.map(sub => ({ ...sub, status: 'completed' as const }))
            };
          } else if (!websocketDone && s.status === 'pending') {
            return { ...s, status: 'loading' as const };
          }
        }
        
        // 配置
        if (s.id === 'config' && s.status === 'pending') {
          return { 
            ...s, 
            status: 'completed' as const, 
            duration: 150,
            subSteps: s.subSteps?.map(sub => ({ ...sub, status: 'completed' as const }))
          };
        }
        
        // 持仓 - 关键优化：显示详细进度
        if (s.id === 'holdings') {
          const newSubSteps = s.subSteps?.map((sub, idx) => {
            if (holdingsDone) {
              return { ...sub, status: 'completed' as const };
            }
            // 模拟子步骤进度
            if (idx === 0 && s.status === 'loading') return { ...sub, status: 'completed' as const };
            if (idx === 1 && s.status === 'loading') {
              return { 
                ...sub, 
                status: 'loading' as const,
                detail: holdingsProgress.currentSectorName 
                  ? `正在加载: ${holdingsProgress.currentSectorName} (${holdingsProgress.currentSector}/${holdingsProgress.totalSectors})`
                  : '解析板块信息...'
              };
            }
            if (idx === 2 && s.status === 'loading' && holdingsProgress.currentStock > 0) {
              return { 
                ...sub, 
                status: 'loading' as const,
                detail: `验证: ${holdingsProgress.currentStockName || '...'} (${holdingsProgress.currentStock}/${holdingsProgress.totalStocks})`
              };
            }
            return sub;
          });
          
          if (holdingsDone && s.status !== 'completed') {
            return { 
              ...s, 
              status: 'completed' as const, 
              duration: 800,
              subSteps: newSubSteps
            };
          } else if (!holdingsDone && s.status === 'pending') {
            return { ...s, status: 'loading' as const, subSteps: newSubSteps };
          } else if (!holdingsDone && s.status === 'loading') {
            return { ...s, subSteps: newSubSteps };
          }
        }
        
        // 行情
        if (s.id === 'quotes') {
          if (quotesDone && s.status !== 'completed') {
            return { 
              ...s, 
              status: 'completed' as const, 
              duration: 600,
              subSteps: s.subSteps?.map(sub => ({ ...sub, status: 'completed' as const }))
            };
          } else if (holdingsDone && s.status === 'pending') {
            return { ...s, status: 'loading' as const };
          }
        }
        
        // 分析引擎
        if (s.id === 'analysis') {
          const isAnalysisDoneProp = loadingStates.analysis === false;
          const shouldAutoComplete = loadingStates.analysis === undefined && otherStepsDone;
          const canStartAnalysis = websocketDone && holdingsDone && quotesDone;
          
          if ((isAnalysisDoneProp || shouldAutoComplete) && s.status !== 'completed') {
            return { 
              ...s, 
              status: 'completed' as const, 
              duration: 1200,
              subSteps: s.subSteps?.map(sub => ({ ...sub, status: 'completed' as const }))
            };
          } else if (canStartAnalysis && s.status === 'pending') {
            return { ...s, status: 'loading' as const };
          }
        }
        
        // UI渲染
        if (s.id === 'ui') {
          const analysisDone = prev.find(p => p.id === 'analysis')?.status === 'completed';
          if (analysisDone && s.status !== 'completed') {
            return { 
              ...s, 
              status: 'completed' as const, 
              duration: 300,
              subSteps: s.subSteps?.map(sub => ({ ...sub, status: 'completed' as const }))
            };
          } else if (otherStepsDone && s.status === 'pending') {
            return { ...s, status: 'loading' as const };
          }
        }
        
        return s;
      });
      
      const hasChanged = JSON.stringify(nextSteps) !== JSON.stringify(prev);
      return hasChanged ? nextSteps : prev;
    });
  }, [loadingStates, isComplete, holdingsProgress]);

  // 检查是否全部完成
  useEffect(() => {
    if (isComplete) return;
    
    const allCompleted = steps.every(s => s.status === 'completed');
    const elapsed = Date.now() - startTime;
    
    // 超时保护：如果加载时间超过MAX_LOADING_TIME，强制完成
    if (elapsed > MAX_LOADING_TIME) {
      console.warn('⚠️ 加载超时，强制完成');
      
      // 记录超时日志
      clientLogger.warning('performance', '系统初始化超时，强制完成', {
        elapsedMs: elapsed,
        timeout: MAX_LOADING_TIME,
        incompleteSteps: steps.filter(s => s.status !== 'completed').map(s => ({
          id: s.id,
          name: s.name,
          status: s.status
        }))
      });
      
      setSteps(prev => prev.map(s => ({
        ...s,
        status: 'completed' as const,
        subSteps: s.subSteps?.map(sub => ({ ...sub, status: 'completed' as const }))
      })));
      setTotalTime(elapsed);
      setIsComplete(true);
      
      // 强制进入仪表盘
      const timer = setTimeout(() => {
        onComplete();
      }, 1500);
      
      return () => clearTimeout(timer);
    }
    
    if (allCompleted) {
      const totalDuration = Date.now() - startTime;
      setTotalTime(totalDuration);
      setIsComplete(true);
      
      // 记录加载时间到日志
      console.log(`✅ 系统初始化完成，总耗时: ${(totalDuration / 1000).toFixed(2)}秒`);
      clientLogger.info('performance', '系统初始化完成', {
        totalDurationMs: totalDuration,
        totalDurationSec: (totalDuration / 1000).toFixed(2),
        steps: steps.map(s => ({
          id: s.id,
          name: s.name,
          duration: s.duration
        }))
      });
      
      // 自动进入仪表盘，延迟1.5秒让用户看到完成状态
      const timer = setTimeout(() => {
        onComplete();
      }, 1500);
      
      return () => clearTimeout(timer);
    }
  }, [steps, isComplete, startTime, onComplete]);
  
  const completedCount = steps.filter(s => s.status === 'completed').length;
  const progress = (completedCount / steps.length) * 100;
  
  return (
    <div className={`fixed inset-0 flex items-center justify-center ${
      isDark 
        ? 'bg-gradient-to-br from-[#0a0a0a] via-[#1a1a1a] to-[#0a0a0a]' 
        : 'bg-gradient-to-br from-gray-50 via-white to-gray-100'
    }`}>
      <div className={`w-full max-w-3xl p-8 ${
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
        <div className="mb-6">
          <div className={`h-2 rounded-full ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}>
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                isComplete ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
        
        {/* 步骤列表 */}
        <div className="space-y-2 mb-6">
          {steps.map((step) => (
            <div key={step.id}>
              {/* 主步骤 */}
              <div 
                className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                  step.status === 'loading' 
                    ? isDark ? 'bg-blue-900/20' : 'bg-blue-50'
                    : isDark ? 'bg-[#0a0a0a]' : 'bg-gray-50'
                }`}
              >
                <div className="flex items-center gap-3 flex-1">
                  {/* 展开/收起按钮 */}
                  {step.subSteps && step.subSteps.length > 0 && (
                    <button
                      onClick={() => toggleStepExpanded(step.id)}
                      className={`p-1 rounded hover:bg-gray-700/30 ${
                        isDark ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      {step.expanded ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>
                  )}
                  
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
              
              {/* 子步骤 */}
              {step.expanded && step.subSteps && step.subSteps.length > 0 && (
                <div className={`ml-12 mt-2 space-y-1.5 ${
                  isDark ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  {step.subSteps.map((subStep) => (
                    <div 
                      key={subStep.id}
                      className={`flex items-start gap-2 p-2 rounded text-sm ${
                        subStep.status === 'loading'
                          ? isDark ? 'bg-blue-900/10' : 'bg-blue-50/50'
                          : ''
                      }`}
                    >
                      {/* 子步骤状态图标 */}
                      <div className={`mt-0.5 ${
                        subStep.status === 'completed' 
                          ? 'text-green-500'
                          : subStep.status === 'loading'
                            ? 'text-blue-500 animate-pulse'
                            : isDark ? 'text-gray-600' : 'text-gray-400'
                      }`}>
                        {subStep.status === 'completed' ? (
                          <CheckCircle className="w-4 h-4" />
                        ) : subStep.status === 'loading' ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <div className="w-4 h-4 rounded-full border border-current" />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <div className={subStep.status === 'pending' ? 'opacity-50' : ''}>
                          {subStep.name}
                        </div>
                        {subStep.detail && (
                          <div className={`text-xs mt-0.5 ${
                            isDark ? 'text-gray-400' : 'text-gray-500'
                          }`}>
                            {subStep.detail}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 实时日志输出 */}
        <div className={`p-4 rounded border font-mono text-xs h-32 overflow-hidden mb-6 ${
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
        
        {/* 自动进入提示 */}
        {isComplete && (
          <div className="text-center">
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              正在自动进入智能仪表盘...
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
