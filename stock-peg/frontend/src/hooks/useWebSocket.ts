/**
 * WebSocket Hook - 实时行情推送
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { clientLogger } from '../services/clientLogger';

const getWsUrl = () => {
  const configured = import.meta.env.VITE_WS_URL;
  if (configured && configured.trim()) {
    return configured;
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws`;
};

const normalizeStockCode = (code?: string) => {
  if (!code) return '';
  return code
    .replace(/^(sh|sz)/i, '')
    .replace(/\.(SH|SZ)$/i, '')
    .trim();
};

interface QuoteData {
  code: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  timestamp: string;
}

interface AlertData {
  id: string;
  stock_code: string;
  stock_name: string;
  alert_type: string;
  threshold: number;
  triggered_at: string;
  current_price: number;
  current_change_pct: number;
}

interface StartupProgress {
  stage: 'init' | 'check' | 'updating' | 'background' | 'complete' | 'error';
  total?: number;
  current?: number;
  success?: number;
  failed?: number;
  timeout?: number;
  current_code?: string;
  elapsed?: number;
  error?: string;
  updated?: number;
}

interface WebSocketMessage {
  type: 'quote' | 'quote_updated' | 'alert' | 'prediction' | 'subscription' | 'pong' | 'holdings_updated' | 'startup_progress' | 'initial_sync_error' | 'kline_updated' | 'financial_updated' | 'us_index_updated' | 'background_update_progress' | 'pmr_precompute_start' | 'pmr_precompute_progress' | 'pmr_precompute_complete' | 'market_sentiment_updated' | 'market_data_updated' | 'sector_updated' | 'stock_code_updated' | 'feishu-chat-message' | 'feishu_chat_message' | 'feishu-card-message' | 'feishu-chat-cleared';
  stock_code?: string;
  symbol?: string;
  data?: QuoteData | AlertData | any;
  action?: 'subscribed' | 'unsubscribed';
  message?: string;
  progress?: StartupProgress;
  old_code?: string;
  new_code?: string;
  stock_name?: string;
  stock_id?: number;
  timestamp: string;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [quotes, setQuotes] = useState<Map<string, QuoteData>>(new Map());
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isIntentionalDisconnectRef = useRef(false);
  const isConnectingRef = useRef(false);

  // 连接WebSocket
  const connect = useCallback(() => {
    if (isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    isIntentionalDisconnectRef.current = false;
    isConnectingRef.current = true;
    const ws = new WebSocket(getWsUrl());

    ws.onopen = () => {
      isConnectingRef.current = false;
      console.log('WebSocket connected');
      setIsConnected(true);
      (window as any).__stockPegWsConnected = true;
      
      // 设置客户端日志的WebSocket连接
      clientLogger.setWebSocket(ws, true);
      
      // 触发连接事件
      window.dispatchEvent(new CustomEvent('websocket-connected'));
      
      // 开始心跳
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'ping' }));
        }
      }, 30000); // 30秒一次心跳
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        // 派发自定义事件，让其他组件可以监听
        window.dispatchEvent(new CustomEvent('websocket-message', { 
          detail: message 
        }));

        switch (message.type) {
          case 'quote':
            // 更新行情数据
            if (message.data) {
              const quote = message.data as QuoteData;
              const normalizedCode = normalizeStockCode(quote.code);
              setQuotes(prevQuotes => {
                const newQuotes = new Map(prevQuotes);
                if (quote.code) {
                  newQuotes.set(quote.code, quote);
                }
                if (normalizedCode) {
                  newQuotes.set(normalizedCode, { ...quote, code: normalizedCode });
                }
                return newQuotes;
              });
            }
            break;

          case 'alert':
            // 新增预警
            if (message.data) {
              const alert = message.data as AlertData;
              setAlerts(prev => [alert, ...prev].slice(0, 50)); // 保留最近50条
              console.log('Alert triggered:', alert);
            }
            break;

          case 'prediction':
            // 预测更新处理（可根据需要添加状态存储）
            console.log('Prediction updated:', message.data);
            break;

          case 'holdings_updated':
            // 持仓数据更新通知
            console.log('Holdings updated:', message.data);
            // 触发页面刷新（通过自定义事件）
            window.dispatchEvent(new CustomEvent('holdings-updated', { 
              detail: message.data 
            }));
            break;

          case 'financial_updated':
            // 财务数据更新通知
            if (message.stock_code && !message.stock_code.startsWith('UNKNOWN')) {
              console.log('Financial data updated:', message.stock_code);
              // 派发特定事件通知组件刷新财务数据
              window.dispatchEvent(new CustomEvent('financial-updated', { 
                detail: { stockCode: message.stock_code } 
              }));
            }
            break;

          case 'stock_code_updated':
            // 股票代码更新通知（UNKNOWN代码解析成功）
            if (message.old_code && message.new_code) {
              console.log(`Stock code updated: ${message.old_code} -> ${message.new_code}`);
              // 派发事件通知组件更新股票代码
              window.dispatchEvent(new CustomEvent('stock-code-updated', { 
                detail: {
                  oldCode: message.old_code,
                  newCode: message.new_code,
                  stockName: message.stock_name,
                  stockId: message.stock_id
                }
              }));
            }
            break;

          case 'kline_updated':
            // K线数据更新通知
            if (message.stock_code && !message.stock_code.startsWith('UNKNOWN')) {
              console.log('K-line data updated:', message.stock_code);
              // 派发特定事件通知组件刷新K线数据
              window.dispatchEvent(new CustomEvent('kline-updated', { 
                detail: { stockCode: message.stock_code } 
              }));
            }
            break;

          case 'us_index_updated':
            // 美股指数数据更新通知
            if (message.symbol) {
              console.log('US index data updated:', message.symbol);
              // 派发特定事件
              window.dispatchEvent(new CustomEvent('us-index-updated', { 
                detail: { symbol: message.symbol } 
              }));
            }
            break;

          case 'background_update_progress':
            // 后台更新进度通知
            if (message.progress) {
              console.log('Background update progress:', message.progress);
            }
            break;

          case 'pmr_precompute_start':
          case 'pmr_precompute_progress':
          case 'pmr_precompute_complete':
            // PMR 预计算通知
            console.log(`PMR precompute ${message.type}:`, message.message);
            break;

          case 'market_sentiment_updated':
            window.dispatchEvent(new CustomEvent('market-sentiment-updated', {
              detail: message.data
            }));
            break;

          case 'market_data_updated':
          case 'sector_updated':
            window.dispatchEvent(new CustomEvent('market-data-updated', {
              detail: message.data
            }));
            break;

          case 'subscription':
            console.log(`Stock ${message.stock_code} ${message.action}`);
            break;

          case 'pong':
            // 收到心跳响应，无需特殊操作
            break;

          case 'feishu-chat-message':
          case 'feishu_chat_message':
          case 'feishu-card-message':
            // 飞书Bot消息 - 通过自定义事件通知BotChatTab
            console.log('Feishu chat message received:', message.data);
            window.dispatchEvent(new CustomEvent('feishu-chat-message-received', {
              detail: message.data
            }));
            break;

          case 'feishu-chat-cleared':
            // 飞书对话清空通知
            console.log('Feishu chat cleared:', message.data);
            window.dispatchEvent(new CustomEvent('feishu-chat-cleared', {
              detail: message.data
            }));
            break;
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      isConnectingRef.current = false;
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      isConnectingRef.current = false;
      console.log('WebSocket disconnected');
      setIsConnected(false);
      (window as any).__stockPegWsConnected = false;
      
      // 更新客户端日志的WebSocket状态
      clientLogger.setWebSocket(null, false);
      
      // 触发断开事件
      window.dispatchEvent(new CustomEvent('websocket-disconnected'));
      
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      
      // 如果不是故意断开的，则自动重连
      if (!isIntentionalDisconnectRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Reconnecting...');
          connect();
        }, 3000);
      }
    };

    wsRef.current = ws;
  }, []);

  // 断开连接
  const disconnect = useCallback(() => {
    isIntentionalDisconnectRef.current = true;
    isConnectingRef.current = false;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    if (wsRef.current) {
      const ws = wsRef.current;
      wsRef.current = null;
      
      // 清除所有事件处理器，避免触发任何回调（解决竞态条件）
      ws.onopen = null;
      ws.onmessage = null;
      ws.onerror = null;
      ws.onclose = null;
      
      // 只有在 OPEN 状态才需要正常关闭
      if (ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'Intentional disconnect');
      }
      // CONNECTING 状态不需要调用 close()，让浏览器自动处理
      // 这样避免了 "WebSocket is closed before the connection is established" 错误
    }
    setIsConnected(false);
    (window as any).__stockPegWsConnected = false;
  }, []);

  // 订阅股票
  const subscribe = useCallback((stockCodes: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      stockCodes.forEach(stockCode => {
        wsRef.current?.send(JSON.stringify({
          action: 'subscribe',
          stock_code: stockCode,
        }));
      });
    }
  }, []);

  // 取消订阅
  const unsubscribe = useCallback((stockCodes: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      stockCodes.forEach(stockCode => {
        wsRef.current?.send(JSON.stringify({
          action: 'unsubscribe',
          stock_code: stockCode,
        }));
      });
    }
  }, []);

  // 组件挂载时自动连接
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    quotes,
    alerts,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
  };
}
