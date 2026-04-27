/**
 * Bot对话标签页 - 显示与飞书的对话记录
 */
import { useEffect, useState, useRef, useMemo } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { feishuChatApi } from '../services/api';
import { useTheme } from '../contexts/ThemeContext';
import { Bot, User, RefreshCw, MessageCircle, Search, X, Send } from 'lucide-react';

export default function BotChatTab() {
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
      if (!message?.type) return;
      if (
        message.type === 'feishu_chat_message' ||
        message.type === 'feishu-chat-message' ||
        message.type === 'feishu-card-message'
      ) {
        console.log('[BotChatTab] Received Feishu message, refreshing...');
        queryClient.invalidateQueries({ queryKey: ['feishu-chat', 'recent'] });
      }
    };

    // 监听来自useWebSocket的消息事件
    const onFeishuMessage = (event: Event) => {
      const data = (event as CustomEvent).detail;
      console.log('[BotChatTab] Feishu message received:', data);
      queryClient.invalidateQueries({ queryKey: ['feishu-chat', 'recent'] });
    };

    window.addEventListener('websocket-message', onMessage);
    window.addEventListener('feishu-chat-message-received', onFeishuMessage);

    return () => {
      window.removeEventListener('websocket-message', onMessage);
      window.removeEventListener('feishu-chat-message-received', onFeishuMessage);
    };
  }, [queryClient]);

  // 获取最近对话记录
  const { data: messages, isLoading, error, refetch } = useQuery({
    queryKey: ['feishu-chat', 'recent'],
    queryFn: () => feishuChatApi.getRecent(50),
    refetchInterval: 10000,
  });

  // 自动滚动到底部
  useEffect(() => {
    if (messages && messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

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
    onSuccess: () => {
      setInputMessage('');
      // 刷新对话列表
      queryClient.invalidateQueries({ queryKey: ['feishu-chat', 'recent'] });
    },
    onError: (error) => {
      console.error('Failed to send message:', error);
      alert('发送失败，请检查是否有飞书对话记录');
    },
  });

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

  // Emoji短代码映射表
  const emojiMap: Record<string, string> = {
    ':smile:': '😊',
    ':laugh:': '😂',
    ':wink:': '😉',
    ':heart:': '❤️',
    ':star:': '⭐',
    ':fire:': '🔥',
    ':chart_up:': '📈',
    ':chart_down:': '📉',
    ':money:': '💰',
    ':dollar:': '💵',
    ':check:': '✅',
    ':cross:': '❌',
    ':warning:': '⚠️',
    ':info:': 'ℹ️',
    ':bulb:': '💡',
    ':rocket:': '🚀',
    ':thumbsup:': '👍',
    ':thumbsdown:': '👎',
    ':thinking:': '🤔',
    ':tada:': '🎉',
    ':sob:': '😭',
    ':angry:': '😠',
    ':cool:': '😎',
    ':love:': '😍',
    ':ok:': '👌',
    ':pray:': '🙏',
    ':muscle:': '💪',
    ':chart:': '📊',
    ':calendar:': '📅',
    ':clock:': '🕐',
    ':bell:': '🔔',
    ':exclamation:': '❗',
    ':question:': '❓',
    ':arrow_up:': '⬆️',
    ':arrow_down:': '⬇️',
    ':arrow_right:': '➡️',
    ':arrow_left:': '⬅️',
    ':up:': '🔴',
    ':down:': '🟢',
  };

  // 解析emoji短代码
  const parseEmoji = (text: string): string => {
    let result = text;
    for (const [shortcode, emoji] of Object.entries(emojiMap)) {
      result = result.split(shortcode).join(emoji);
    }
    return result;
  };

  // 解析消息内容（增强Markdown格式）
  const parseContent = (content: string) => {
    return content
      .split('\n')
      .map((line, i) => {
        // 空行
        if (!line.trim()) {
          return <br key={i} />;
        }

        // 解析行内元素
        const parseInlineElements = (text: string): React.ReactNode[] => {
          const elements: React.ReactNode[] = [];
          let remaining = text;
          let keyIndex = 0;

          while (remaining.length > 0) {
            // Emoji短代码解析
            const emojiMatch = remaining.match(/:[a-z_]+:/);
            if (emojiMatch && emojiMap[emojiMatch[0]]) {
              const matchIndex = remaining.indexOf(emojiMatch[0]);
              
              if (matchIndex > 0) {
                elements.push(<span key={keyIndex++}>{parseEmoji(remaining.substring(0, matchIndex))}</span>);
              }
              
              elements.push(
                <span key={keyIndex++} className="text-base">
                  {emojiMap[emojiMatch[0]]}
                </span>
              );
              
              remaining = remaining.substring(matchIndex + emojiMatch[0].length);
              continue;
            }

            // 股票代码 (6位数字) - 转换为可点击链接
            const stockCodeMatch = remaining.match(/\((\d{6})\)|(\d{6})/);
            if (stockCodeMatch && (stockCodeMatch[1] || stockCodeMatch[2])) {
              const code = stockCodeMatch[1] || stockCodeMatch[2];
              const matchIndex = remaining.indexOf(stockCodeMatch[0]);
              
              // 添加前面的文本
              if (matchIndex > 0) {
                elements.push(<span key={keyIndex++}>{parseEmoji(remaining.substring(0, matchIndex))}</span>);
              }
              
              // 添加股票代码链接
              elements.push(
                <span
                  key={keyIndex++}
                  className="text-blue-500 hover:text-blue-600 cursor-pointer underline font-medium"
                  onClick={() => {
                    // 触发股票搜索事件
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
                elements.push(<span key={keyIndex++}>{parseEmoji(remaining.substring(0, matchIndex))}</span>);
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
                elements.push(<span key={keyIndex++}>{parseEmoji(remaining.substring(0, matchIndex))}</span>);
              }
              
              elements.push(
                <strong key={keyIndex++} className="font-bold">
                  {parseEmoji(boldMatch[1])}
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
                elements.push(<span key={keyIndex++}>{parseEmoji(remaining.substring(0, matchIndex))}</span>);
              }
              
              elements.push(
                <span key={keyIndex++} className="text-orange-500 font-medium">
                  {priceMatch[0]}
                </span>
              );
              
              remaining = remaining.substring(matchIndex + priceMatch[0].length);
              continue;
            }

            // 没有匹配，添加剩余文本（解析emoji）
            elements.push(<span key={keyIndex++}>{parseEmoji(remaining)}</span>);
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
            {searchQuery ? '尝试其他搜索关键词' : '在飞书中与PegBot对话后会显示在这里'}
          </span>
        </div>
      </div>
    );
  }

  // 按时间正序排列（最早的在上面）
  const sortedMessages = [...filteredMessages].reverse();

  return (
    <div className="flex flex-col h-full">
      {/* 头部 */}
      <div className={`flex items-center justify-between px-3 py-2 border-b ${
        isDark ? 'border-gray-700 bg-gray-800/50' : 'border-gray-200 bg-gray-50'
      }`}>
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-blue-500" />
          <span className="text-sm font-medium">PegBot 对话</span>
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
            placeholder="输入消息发送给PegBot..."
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
