/**
 * Bot对话标签页 - 增强版
 * 功能：
 * 1. 快捷指令按钮
 * 2. 消息搜索与过滤
 * 3. 实时行情卡片
 * 4. 命令历史
 * 5. 数据导出
 */
import { useEffect, useState, useRef, useMemo } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { feishuChatApi } from '../services/api';
import { useTheme } from '../contexts/ThemeContext';
import {
  Bot, User, RefreshCw, MessageCircle, Search, X, Send,
  TrendingUp, TrendingDown, HelpCircle, Download, Clock, Trash2
} from 'lucide-react';

// 快捷指令配置
const QUICK_COMMANDS = [
  { label: '查询', icon: TrendingUp, command: '查询 ', placeholder: '股票名称或代码' },
  { label: '买入', icon: TrendingDown, command: '买入 ', placeholder: '股票代码' },
  { label: '帮助', icon: HelpCircle, command: '帮助', placeholder: '' },
];

export default function BotChatTabEnhanced() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [wsConnected, setWsConnected] = useState<boolean>(() => Boolean((window as any).__stockPegWsConnected));
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [inputMessage, setInputMessage] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const [showQuickCommands, setShowQuickCommands] = useState(true);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);

  // WebSocket连接状态监听
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

  // WebSocket消息监听 - 实时更新对话
  useEffect(() => {
    const onMessage = (event: Event) => {
      const message = (event as CustomEvent).detail;
      console.log('[BotChatTabEnhanced] WebSocket message received:', message);
      if (!message?.type) return;
      if (
        message.type === 'feishu_chat_message' ||
        message.type === 'feishu-chat-message' ||
        message.type === 'feishu-card-message' ||
        message.type === 'feishu-chat-cleared'
      ) {
        console.log('[BotChatTabEnhanced] Invalidating queries for Feishu message');
        queryClient.invalidateQueries({ queryKey: ['feishu-chat', 'recent'] });
      }
    };

    console.log('[BotChatTabEnhanced] Setting up WebSocket message listener');
    window.addEventListener('websocket-message', onMessage);
    return () => {
      console.log('[BotChatTabEnhanced] Cleaning up WebSocket message listener');
      window.removeEventListener('websocket-message', onMessage);
    };
  }, [queryClient]);

  // 获取最近对话记录
  const { data: messages, isLoading, error, refetch } = useQuery({
    queryKey: ['feishu-chat', 'recent'],
    queryFn: () => feishuChatApi.getRecent(50),
    refetchInterval: wsConnected ? false : 60000,
  });

  // 自动滚动到底部
  useEffect(() => {
    if (messages && messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // 自动激活功能 - 首次加载且无消息时推送菜单卡片
  const hasAutoActivated = useRef(false);
  useEffect(() => {
    // 只在首次加载、加载完成、无消息时触发
    if (!isLoading && messages && messages.length === 0 && !hasAutoActivated.current) {
      hasAutoActivated.current = true;
      console.log('[BotChatTabEnhanced] No messages, auto-activating menu...');
      
      // 自动推送 STOCK_RESEARCH_START 卡片
      feishuChatApi.pushEvent('STOCK_RESEARCH_START')
        .then(result => {
          console.log('[BotChatTabEnhanced] Auto-activation result:', result);
          if (result.status === 'ok') {
            // 刷新消息列表
            queryClient.invalidateQueries({ queryKey: ['feishu-chat', 'recent'] });
          }
        })
        .catch(error => {
          console.warn('[BotChatTabEnhanced] Auto-activation failed:', error);
          // 可能是因为没有 chat_id（用户从未与 Bot 对话过）
        });
    }
  }, [isLoading, messages, queryClient]);

  // 自动聚焦搜索框
  useEffect(() => {
    if (showSearch && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [showSearch]);

  // 过滤消息（搜索功能）
  const filteredMessages = useMemo(() => {
    if (!messages) return [];
    if (!searchQuery.trim()) return messages;

    const query = searchQuery.toLowerCase();
    return messages.filter(msg =>
      msg.content.toLowerCase().includes(query) ||
      msg.sender_name?.toLowerCase().includes(query) ||
      msg.message_id.includes(query)
    );
  }, [messages, searchQuery]);

  // 发送消息mutation
  const sendMessageMutation = useMutation({
    mutationFn: (message: string) => feishuChatApi.sendMessage(message),
    onSuccess: (_data, message) => {
      setInputMessage('');
      // 添加到命令历史
      if (message.startsWith('查询') || message.startsWith('买入')) {
        setCommandHistory(prev => {
          const newHistory = [message, ...prev.filter(cmd => cmd !== message)].slice(0, 10);
          return newHistory;
        });
      }
      // 刷新对话列表
      queryClient.invalidateQueries({ queryKey: ['feishu-chat', 'recent'] });
    },
    onError: (error) => {
      console.error('Failed to send message:', error);
      const detail = (error as { detail?: string })?.detail;
      alert(detail || '发送失败，请检查是否有飞书对话记录');
    },
  });

  const clearHistoryMutation = useMutation({
    mutationFn: () => feishuChatApi.clearHistory(),
    onSuccess: (data) => {
      console.log('[BotChatTabEnhanced] Clear history success:', data);
      // 刷新对话列表
      queryClient.invalidateQueries({ queryKey: ['feishu-chat', 'recent'] });
      refetch();
      // 显示成功消息
      if (data.deleted_rows > 0 || data.deleted_files > 0) {
        alert(`清理成功！删除了 ${data.deleted_rows} 条消息记录和 ${data.deleted_files} 个日志文件`);
      } else {
        alert('清理完成！没有找到需要清理的记录');
      }
    },
    onError: (error) => {
      console.error('[BotChatTabEnhanced] Clear history error:', error);
      const detail = (error as { detail?: string })?.detail;
      alert(detail || '清理失败，请稍后重试');
    },
  });

  // 快捷指令点击
  const handleQuickCommand = (command: string, placeholder: string) => {
    if (placeholder) {
      // 需要输入参数
      const value = prompt(`请输入${placeholder}:`);
      if (value) {
        const fullCommand = command + value;
        setInputMessage(fullCommand);
        inputRef.current?.focus();
      }
    } else {
      // 直接发送
      sendMessageMutation.mutate(command);
    }
  };

  // 导出对话记录
  const handleExport = () => {
    if (!messages || messages.length === 0) {
      alert('没有对话记录可导出');
      return;
    }

    const exportData = messages.map(msg => ({
      时间: new Date(msg.send_time).toLocaleString('zh-CN'),
      发送者: msg.sender_type === 'bot' ? 'Bot' : msg.sender_name || '用户',
      内容: msg.content,
    }));

    const csvContent = [
      Object.keys(exportData[0]).join(','),
      ...exportData.map(row => Object.values(row).map(v => `"${v}"`).join(','))
    ].join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `bot-chat-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  // 格式化时间
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  };

  // 解析消息内容（增强Markdown格式）
  const parseContent = (content: string) => {
    return content
      .split('\n')
      .map((line, i) => {
        if (!line.trim()) {
          return <br key={i} />;
        }

        const parseInlineElements = (text: string): React.ReactNode[] => {
          const elements: React.ReactNode[] = [];
          let remaining = text;
          let keyIndex = 0;

          while (remaining.length > 0) {
            // 股票代码 (6位数字) - 转换为可点击链接
            const stockCodeMatch = remaining.match(/\((\d{6})\)|(\d{6})/);
            if (stockCodeMatch && (stockCodeMatch[1] || stockCodeMatch[2])) {
              const code = stockCodeMatch[1] || stockCodeMatch[2];
              const matchIndex = remaining.indexOf(stockCodeMatch[0]);

              if (matchIndex > 0) {
                elements.push(<span key={keyIndex++}>{remaining.substring(0, matchIndex)}</span>);
              }

              elements.push(
                <span
                  key={keyIndex++}
                  className="text-blue-500 hover:text-blue-600 cursor-pointer underline font-medium"
                  onClick={() => {
                    window.dispatchEvent(new CustomEvent('search-stock', { detail: code }));
                  }}
                  title={`点击查看 ${code}`}
                >
                  {stockCodeMatch[0]}
                </span>
              );

              remaining = remaining.substring(matchIndex + stockCodeMatch[0].length);
              continue;
            }

            // 涨跌幅（正数显示红色，负数显示绿色）
            const percentMatch = remaining.match(/([+-])(\d+\.?\d*)%/);
            if (percentMatch) {
              const matchIndex = remaining.indexOf(percentMatch[0]);

              if (matchIndex > 0) {
                elements.push(<span key={keyIndex++}>{remaining.substring(0, matchIndex)}</span>);
              }

              const isPositive = percentMatch[1] === '+';
              elements.push(
                <span
                  key={keyIndex++}
                  className={`font-medium ${isPositive ? 'text-red-500' : 'text-green-500'}`}
                >
                  {percentMatch[0]}
                </span>
              );

              remaining = remaining.substring(matchIndex + percentMatch[0].length);
              continue;
            }

            // 加粗文本 **text**
            const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
            if (boldMatch) {
              const matchIndex = remaining.indexOf(boldMatch[0]);

              if (matchIndex > 0) {
                elements.push(<span key={keyIndex++}>{remaining.substring(0, matchIndex)}</span>);
              }

              elements.push(
                <strong key={keyIndex++} className="font-bold">
                  {boldMatch[1]}
                </strong>
              );

              remaining = remaining.substring(matchIndex + boldMatch[0].length);
              continue;
            }

            // 价格数字（包含小数点）- 高亮显示
            const priceMatch = remaining.match(/(\d+\.\d{2,2})/);
            if (priceMatch) {
              const matchIndex = remaining.indexOf(priceMatch[0]);

              if (matchIndex > 0) {
                elements.push(<span key={keyIndex++}>{remaining.substring(0, matchIndex)}</span>);
              }

              elements.push(
                <span key={keyIndex++} className="text-orange-500 font-medium">
                  {priceMatch[0]}
                </span>
              );

              remaining = remaining.substring(matchIndex + priceMatch[0].length);
              continue;
            }

            elements.push(<span key={keyIndex++}>{remaining}</span>);
            break;
          }

          return elements;
        };

        // 标题行（**text** 整行）
        if (line.startsWith('**') && line.endsWith('**')) {
          return (
            <div key={i} className="font-bold text-sm mb-1">
              {line.slice(2, -2)}
            </div>
          );
        }

        // 列表项
        if (line.startsWith('- ')) {
          return (
            <div key={i} className="ml-2 flex items-start">
              <span className="mr-1">•</span>
              <span>{parseInlineElements(line.slice(2))}</span>
            </div>
          );
        }

        // 数字列表
        const listMatch = line.match(/^(\d+\.)\s(.+)/);
        if (listMatch) {
          return (
            <div key={i} className="ml-2">
              <span className="text-gray-500">{listMatch[1]}</span>{' '}
              {parseInlineElements(listMatch[2])}
            </div>
          );
        }

        // 普通文本
        return <div key={i}>{parseInlineElements(line)}</div>;
      });
  };

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center h-64 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
        <RefreshCw className="w-5 h-5 animate-spin mr-2" />
        <span>加载对话记录...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex flex-col items-center justify-center h-64 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
        <MessageCircle className="w-8 h-8 mb-2 opacity-50" />
        <span>加载失败</span>
        <button
          onClick={() => refetch()}
          className={`mt-2 px-3 py-1 text-sm rounded ${
            isDark ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'
          }`}
        >
          重试
        </button>
      </div>
    );
  }

  if (!filteredMessages || filteredMessages.length === 0) {
    return (
      <div className="flex flex-col h-full">
        {showSearch && (
          <div className={`px-3 py-2 border-b ${
            isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-gray-50'
          }`}>
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索股票名称、代码或内容..."
                className={`flex-1 text-sm px-2 py-1 rounded border-none outline-none ${
                  isDark ? 'bg-gray-700 text-gray-100 placeholder-gray-400' : 'bg-white text-gray-800 placeholder-gray-500'
                }`}
              />
              <button
                onClick={() => {
                  setSearchQuery('');
                  setShowSearch(false);
                }}
                className="p-1 hover:opacity-70"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        <div className={`flex flex-col items-center justify-center flex-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
          <MessageCircle className="w-8 h-8 mb-2 opacity-50" />
          <span>{searchQuery ? '未找到匹配的对话' : '暂无对话记录'}</span>
          <span className="text-xs mt-1 opacity-60">
            {searchQuery ? '尝试其他搜索关键词' : '在飞书中与Bot对话后会显示在这里'}
          </span>
          {!searchQuery && (
            <button
              onClick={() => {
                const ok = window.confirm('确认清理全部对话记录吗？该操作不可恢复。');
                if (ok && !clearHistoryMutation.isPending) {
                  clearHistoryMutation.mutate();
                }
              }}
              className={`mt-3 px-3 py-1.5 text-xs rounded flex items-center gap-1 ${
                isDark
                  ? 'bg-red-900/40 text-red-300 hover:bg-red-900/60'
                  : 'bg-red-50 text-red-600 border border-red-200 hover:bg-red-100'
              }`}
            >
              <Trash2 className="w-3 h-3" />
              {clearHistoryMutation.isPending ? '清理中...' : '清理对话'}
            </button>
          )}
        </div>
      </div>
    );
  }

  const sortedMessages = [...filteredMessages].reverse();

  return (
    <div className="flex flex-col h-full">
      {/* 头部 */}
      <div className={`flex items-center justify-between px-3 py-2 border-b ${
        isDark ? 'border-gray-700 bg-gray-800/50' : 'border-gray-200 bg-gray-50'
      }`}>
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-blue-500" />
          <span className="text-sm font-medium">飞书Bot对话</span>
          {wsConnected && (
            <span className="w-2 h-2 rounded-full bg-green-500" title="实时连接" />
          )}
          {searchQuery && (
            <span className={`text-xs px-2 py-0.5 rounded ${
              isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700'
            }`}>
              {filteredMessages.length}条匹配
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowSearch(!showSearch)}
            className={`p-1 rounded hover:bg-opacity-80 ${
              showSearch
                ? isDark ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700'
                : isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-200'
            }`}
            title="搜索"
          >
            <Search className="w-4 h-4" />
          </button>
          <button
            onClick={handleExport}
            className={`p-1 rounded hover:bg-opacity-80 ${
              isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-200'
            }`}
            title="导出对话"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              const ok = window.confirm('确认清理全部对话记录吗？该操作不可恢复。');
              if (ok && !clearHistoryMutation.isPending) {
                clearHistoryMutation.mutate();
              }
            }}
            className={`p-1 rounded hover:bg-opacity-80 ${
              isDark ? 'hover:bg-red-900/40 text-red-400' : 'hover:bg-red-100 text-red-600'
            }`}
            title="清理对话"
          >
            {clearHistoryMutation.isPending ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
          </button>
          <button
            onClick={() => refetch()}
            className={`p-1 rounded hover:bg-opacity-80 ${
              isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-200'
            }`}
            title="刷新"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 搜索栏 */}
      {showSearch && (
        <div className={`px-3 py-2 border-b ${
          isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-gray-50'
        }`}>
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-gray-400" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索股票名称、代码或内容..."
              className={`flex-1 text-sm px-2 py-1 rounded border-none outline-none ${
                isDark ? 'bg-gray-700 text-gray-100 placeholder-gray-400' : 'bg-white text-gray-800 placeholder-gray-500'
              }`}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="p-1 hover:opacity-70"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* 快捷指令栏 */}
      {showQuickCommands && (
        <div className={`px-3 py-2 border-b ${
          isDark ? 'border-gray-700 bg-gray-800/50' : 'border-gray-200 bg-gray-50'
        }`}>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-gray-500">快捷指令:</span>
            {QUICK_COMMANDS.map((cmd, index) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={index}
                  onClick={() => handleQuickCommand(cmd.command, cmd.placeholder)}
                  className={`px-2 py-1 text-xs rounded flex items-center gap-1 transition-colors ${
                    isDark
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                      : 'bg-white hover:bg-gray-100 text-gray-700 border border-gray-300'
                  }`}
                >
                  <Icon className="w-3 h-3" />
                  {cmd.label}
                </button>
              );
            })}
            <button
              onClick={() => setShowQuickCommands(false)}
              className="ml-auto text-xs text-gray-400 hover:text-gray-500"
            >
              隐藏
            </button>
          </div>
        </div>
      )}

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {sortedMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.sender_type === 'bot' ? 'justify-start' : 'justify-end'}`}
          >
            <div className={`flex gap-2 max-w-[85%] ${msg.sender_type === 'bot' ? 'flex-row' : 'flex-row-reverse'}`}>
              {/* 头像 */}
              <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
                msg.sender_type === 'bot'
                  ? 'bg-blue-500 text-white'
                  : isDark ? 'bg-gray-600 text-gray-200' : 'bg-gray-300 text-gray-700'
              }`}>
                {msg.sender_type === 'bot' ? (
                  <Bot className="w-4 h-4" />
                ) : (
                  <User className="w-4 h-4" />
                )}
              </div>

              {/* 消息内容 */}
              <div className={`flex flex-col min-w-[33.333%] ${msg.sender_type === 'bot' ? 'items-start' : 'items-end'}`}>
                <div className={`px-3 py-2 rounded-lg text-sm w-full ${
                  msg.sender_type === 'bot'
                    ? isDark ? 'bg-sky-900 text-sky-50' : 'bg-sky-100 text-sky-900'
                    : isDark ? 'bg-emerald-800 text-emerald-50' : 'bg-emerald-100 text-emerald-900'
                }`}>
                  <div className="whitespace-pre-wrap break-words">
                    {parseContent(msg.content)}
                  </div>
                </div>
                <span className={`text-[10px] mt-1 ${
                  isDark ? 'text-gray-500' : 'text-gray-400'
                }`}>
                  {formatTime(msg.send_time)}
                </span>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 命令历史（最近5条） */}
      {commandHistory.length > 0 && (
        <div className={`px-3 py-1 border-t ${
          isDark ? 'border-gray-700 bg-gray-800/30' : 'border-gray-200 bg-gray-50/50'
        }`}>
          <div className="flex items-center gap-2 overflow-x-auto">
            <Clock className="w-3 h-3 text-gray-400 flex-shrink-0" />
            <span className="text-xs text-gray-400 flex-shrink-0">历史:</span>
            {commandHistory.slice(0, 5).map((cmd, index) => (
              <button
                key={index}
                onClick={() => setInputMessage(cmd)}
                className={`px-2 py-0.5 text-xs rounded whitespace-nowrap ${
                  isDark ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' : 'bg-white hover:bg-gray-100 text-gray-600 border'
                }`}
              >
                {cmd.length > 20 ? cmd.substring(0, 20) + '...' : cmd}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 底部输入框 */}
      <div className={`px-3 py-2 border-t ${
        isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-gray-50'
      }`}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (inputMessage.trim() && !sendMessageMutation.isPending) {
              sendMessageMutation.mutate(inputMessage.trim());
            }
          }}
          className="flex items-center gap-2"
        >
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="输入消息发送给飞书Bot..."
            disabled={sendMessageMutation.isPending}
            className={`flex-1 text-sm px-3 py-2 rounded-lg border outline-none transition-colors ${
              isDark
                ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400 focus:border-blue-500'
                : 'bg-white border-gray-300 text-gray-800 placeholder-gray-500 focus:border-blue-500'
            } ${sendMessageMutation.isPending ? 'opacity-50 cursor-not-allowed' : ''}`}
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || sendMessageMutation.isPending}
            className={`p-2 rounded-lg transition-colors ${
              inputMessage.trim() && !sendMessageMutation.isPending
                ? 'bg-blue-500 hover:bg-blue-600 text-white'
                : isDark
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
            title="发送消息"
          >
            {sendMessageMutation.isPending ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>
        <div className={`text-[10px] mt-1 text-center ${
          isDark ? 'text-gray-500' : 'text-gray-400'
        }`}>
          消息会发送到最近的飞书对话
        </div>
      </div>
    </div>
  );
}
