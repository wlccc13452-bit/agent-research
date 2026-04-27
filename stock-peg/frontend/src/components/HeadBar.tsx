import { useState, useRef, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { usMarketApi, stocksApi } from '../services/api';
import IndexItem from './IndexItem';
import ApiStatusIndicator from './ApiStatusIndicator';
import DataUpdateIndicator from './DataUpdateIndicator';
import StockLoadingIndicator from './StockLoadingIndicator';
import { Activity, TrendingUp, MoreHorizontal } from 'lucide-react';

interface HeadBarIndexItem {
  code: string;
  name: string;
  price?: number;
  change?: number;
  changePct?: number;
  type: 'cn' | 'us' | 'vix' | 'asia';
  loading?: boolean;
}

// A股指数配置
const CN_INDICES = [
  { code: '000001', requestCode: 'sh000001', name: '上证指数' },
  { code: '399001', requestCode: 'sz399001', name: '深证指数' },
  { code: '399006', requestCode: 'sz399006', name: '创业板指' },
];

// 主区域显示的指数数量
const VISIBLE_INDEX_COUNT = 6;

export default function HeadBar() {
  const [showMoreModal, setShowMoreModal] = useState(false);
  const [modalPosition, setModalPosition] = useState({ left: 0, top: 0 });
  const moreButtonRef = useRef<HTMLButtonElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  
  // 获取美股指数
  const { data: usIndicesResponse, isLoading: loadingUS } = useQuery<any>({
    queryKey: ['us-indices'],
    queryFn: usMarketApi.getIndices,
    refetchInterval: 60000,
  });
  
  // 监听美股指数更新事件
  useEffect(() => {
    const handleUSIndexUpdate = () => {
      console.log('📢 收到美股指数更新通知，刷新数据');
      queryClient.invalidateQueries({ queryKey: ['us-indices'] });
    };
    
    window.addEventListener('us-index-updated', handleUSIndexUpdate);
    
    return () => {
      window.removeEventListener('us-index-updated', handleUSIndexUpdate);
    };
  }, [queryClient]);
  
  // 监听A股指数更新事件
  useEffect(() => {
    const handleMarketDataUpdate = () => {
      console.log('📢 收到市场数据更新通知，刷新A股指数');
      queryClient.invalidateQueries({ queryKey: ['cn-indices'] });
    };
    
    window.addEventListener('market-data-updated', handleMarketDataUpdate);
    
    return () => {
      window.removeEventListener('market-data-updated', handleMarketDataUpdate);
    };
  }, [queryClient]);

  // 提取实际数据（适配新的API格式）
  const usIndices = usIndicesResponse?.data || usIndicesResponse;

  // 获取A股指数 - 使用现有API
  const { data: cnIndicesResponse, isLoading: loadingCN } = useQuery<any>({
    queryKey: ['cn-indices'],
    queryFn: async () => {
      const response = await stocksApi.getCNIndices();
      return response?.data || response;
    },
    refetchInterval: 30000,
  });

  // 提取实际数据（适配新的API格式）
  const cnIndices = cnIndicesResponse?.indices || cnIndicesResponse;

  // 处理A股指数数据 - 通过code精确匹配（改进版）
  const cnIndexData: HeadBarIndexItem[] = CN_INDICES.map((config) => {
    const quote = cnIndices?.find((q: any) => {
      const dbCode = String(q?.code || '');
      return (
        dbCode === config.code ||
        dbCode === `sh${config.code}` ||
        dbCode === `sz${config.code}` ||
        dbCode === `${config.code}.SH` ||
        dbCode === `${config.code}.SZ` ||
        dbCode.replace(/^(sh|sz)/i, '') === config.code ||
        dbCode.replace(/\.(SH|SZ)$/i, '') === config.code
      );
    });
    
    return {
      code: config.code,
      name: config.name,
      price: quote?.price ?? undefined,
      change: quote?.change ?? undefined,
      changePct: quote?.change_pct ?? undefined,
      type: 'cn' as const,
      loading: loadingCN
    };
  });

  const getIndexByAnyKey = (indicesData: Record<string, any> | undefined, keys: string[]) => {
    if (!indicesData) return undefined;
    for (const key of keys) {
      if (indicesData[key]) return indicesData[key];
    }
    return undefined;
  };

  // 处理美股指数数据
  const sp500 = getIndexByAnyKey(usIndices, ['标普500', '^GSPC', 'SPX']);
  const nasdaq = getIndexByAnyKey(usIndices, ['纳斯达克', '^IXIC', 'NDX']);
  const dow = getIndexByAnyKey(usIndices, ['道琼斯', '^DJI', 'DJI']);
  const vix = getIndexByAnyKey(usIndices, ['VIX恐慌指数', '^VIX', 'VIX']);
  const nikkei = getIndexByAnyKey(usIndices, ['日经225', '^N225', 'N225', 'NIKKEI225']);
  const kospi = getIndexByAnyKey(usIndices, ['韩国综合', '^KS11', 'KS11', 'KOSPI']);
  const getDisplayPrice = (indexData: any): number | undefined => {
    return indexData?.price ?? indexData?.previous_close ?? undefined;
  };

  const isLoading = loadingUS || loadingCN;

  // 所有指数数据
  const allIndices: HeadBarIndexItem[] = [
    // A股指数
    ...cnIndexData,
    // 美股指数
    {
      code: 'SPX',
      name: '标普500',
      price: getDisplayPrice(sp500),
      change: sp500?.change ?? undefined,
      changePct: sp500?.change_pct ?? undefined,
      type: 'us' as const,
      loading: loadingUS
    },
    {
      code: 'NDX',
      name: '纳斯达克',
      price: getDisplayPrice(nasdaq),
      change: nasdaq?.change ?? undefined,
      changePct: nasdaq?.change_pct ?? undefined,
      type: 'us' as const,
      loading: loadingUS
    },
    {
      code: 'DJI',
      name: '道琼斯',
      price: getDisplayPrice(dow),
      change: dow?.change ?? undefined,
      changePct: dow?.change_pct ?? undefined,
      type: 'us' as const,
      loading: loadingUS
    },
    {
      code: 'VIX',
      name: 'VIX恐慌指数',
      price: getDisplayPrice(vix),
      change: vix?.change ?? undefined,
      changePct: vix?.change_pct ?? undefined,
      type: 'vix' as const,
      loading: loadingUS
    },
    // 日韩指数
    {
      code: 'N225',
      name: '日经225',
      price: getDisplayPrice(nikkei),
      change: nikkei?.change ?? undefined,
      changePct: nikkei?.change_pct ?? undefined,
      type: 'asia' as const,
      loading: loadingUS
    },
    {
      code: 'KS11',
      name: '韩国综合',
      price: getDisplayPrice(kospi),
      change: kospi?.change ?? undefined,
      changePct: kospi?.change_pct ?? undefined,
      type: 'asia' as const,
      loading: loadingUS
    },
  ];

  // 主区域显示的指数
  const visibleIndices = allIndices.slice(0, VISIBLE_INDEX_COUNT);
  const hasMore = allIndices.length > VISIBLE_INDEX_COUNT;

  // 更新弹窗位置
  const updateModalPosition = () => {
    if (moreButtonRef.current) {
      const rect = moreButtonRef.current.getBoundingClientRect();
      const headBar = moreButtonRef.current.closest('.headbar-container');
      const headBarRect = headBar?.getBoundingClientRect();
      
      if (headBarRect) {
        setModalPosition({
          left: rect.left - headBarRect.left,
          top: headBarRect.height
        });
      }
    }
  };

  // 打开弹窗时更新位置
  useEffect(() => {
    if (showMoreModal) {
      updateModalPosition();
    }
  }, [showMoreModal]);

  // 点击外部关闭弹窗
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (modalRef.current && !modalRef.current.contains(event.target as Node) &&
          moreButtonRef.current && !moreButtonRef.current.contains(event.target as Node)) {
        setShowMoreModal(false);
      }
    }
    
    if (showMoreModal) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showMoreModal]);

  return (
    <div 
      className="h-12 px-3 flex items-center justify-between gap-2 flex-shrink-0 relative headbar-container"
      style={{ 
        backgroundColor: 'var(--bg-card)', 
        borderBottom: '1px solid var(--border-color)'
      }}
    >
      {/* 左侧：Logo + 指数 */}
      <div className="flex items-center gap-1.5 flex-1">
        {/* Logo */}
        <div 
          className="flex items-center gap-2 pr-3 flex-shrink-0"
          style={{ borderRight: '1px solid var(--border-color)' }}
        >
          <div 
            className="w-7 h-7 flex items-center justify-center"
            style={{ backgroundColor: 'var(--primary-color)' }}
          >
            <TrendingUp size={16} className="text-white" />
          </div>
          <div className="hidden md:block">
            <h1 className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>Stock PEG</h1>
          </div>
        </div>

        {/* 指数显示区域 + 更多按钮 */}
        <div className="flex items-center gap-0.5 flex-1">
          {visibleIndices.map((index) => (
            <div key={index.code} className="flex-shrink-0">
              <IndexItem
                code={index.code}
                name={index.name}
                price={index.price}
                change={index.change}
                changePct={index.changePct}
                type={index.type}
                loading={Boolean(index.loading) || isLoading}
                compact
              />
            </div>
          ))}
          
          {/* 更多按钮 - 紧跟指数后面 */}
          {hasMore && (
            <button
              ref={moreButtonRef}
              onClick={() => setShowMoreModal(!showMoreModal)}
              className="flex items-center gap-0.5 px-2 py-1 rounded transition-colors flex-shrink-0"
              style={{ 
                backgroundColor: showMoreModal ? 'var(--bg-hover)' : 'var(--bg-hover)',
                color: 'var(--text-secondary)',
                marginLeft: '2px'
              }}
              title="查看所有指数"
            >
              <MoreHorizontal size={14} />
              <span className="text-xs font-semibold">+{allIndices.length - VISIBLE_INDEX_COUNT}</span>
            </button>
          )}
        </div>

      </div>

      {/* 右侧：导航菜单 + API状态 + 设置按钮 */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        {/* 导航菜单 */}
        <nav className="flex items-center gap-1 mr-2">
          <Link
            to="/"
            className="flex items-center gap-1 px-3 py-1.5 transition-colors text-xs font-medium rounded nav-link"
          >
            <Activity size={14} />
            <span className="hidden lg:inline">仪表盘</span>
          </Link>
        </nav>
        
        {/* 股票加载进度指示器 */}
        <StockLoadingIndicator />
        
        <DataUpdateIndicator />
        <ApiStatusIndicator />
      </div>

      {/* 更多指数弹窗 - 紧邻更多按钮下方 */}
      {showMoreModal && (
        <div 
          ref={modalRef}
          className="absolute z-50 p-3 rounded-lg shadow-xl"
          style={{ 
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            minWidth: '400px',
            maxWidth: '500px',
            left: `${modalPosition.left}px`,
            top: `${modalPosition.top}px`,
            marginTop: '2px'
          }}
        >
          <div className="flex items-center justify-between mb-2 pb-2" style={{ borderBottom: '1px solid var(--border-color)' }}>
            <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>全球市场指数</span>
            <button 
              onClick={() => setShowMoreModal(false)}
              className="p-1 rounded hover:bg-opacity-50"
              style={{ color: 'var(--text-muted)' }}
            >
              ✕
            </button>
          </div>
          
          {/* 分组显示 */}
          <div className="space-y-3">
            {/* A股指数 */}
            <div>
              <div className="text-xs font-medium mb-1.5" style={{ color: 'var(--text-muted)' }}>A股指数</div>
              <div className="grid grid-cols-3 gap-2">
                {cnIndexData.map((index) => (
                  <IndexItem
                    key={index.code}
                    code={index.code}
                    name={index.name}
                    price={index.price}
                    change={index.change}
                    changePct={index.changePct}
                    type="cn"
                    loading={isLoading}
                  />
                ))}
              </div>
            </div>

            {/* 美股指数 */}
            <div>
              <div className="text-xs font-medium mb-1.5" style={{ color: 'var(--text-muted)' }}>美股指数</div>
              <div className="grid grid-cols-3 gap-2">
                <IndexItem code="SPX" name="标普500" price={getDisplayPrice(sp500)} change={sp500?.change} changePct={sp500?.change_pct} type="us" loading={loadingUS} />
                <IndexItem code="NDX" name="纳斯达克" price={getDisplayPrice(nasdaq)} change={nasdaq?.change} changePct={nasdaq?.change_pct} type="us" loading={loadingUS} />
                <IndexItem code="DJI" name="道琼斯" price={getDisplayPrice(dow)} change={dow?.change} changePct={dow?.change_pct} type="us" loading={loadingUS} />
              </div>
            </div>

            {/* VIX + 日韩指数 */}
            <div>
              <div className="text-xs font-medium mb-1.5" style={{ color: 'var(--text-muted)' }}>其他指数</div>
              <div className="grid grid-cols-3 gap-2">
                <IndexItem code="VIX" name="VIX恐慌指数" price={getDisplayPrice(vix)} change={vix?.change} changePct={vix?.change_pct} type="vix" loading={loadingUS} />
                <IndexItem code="N225" name="日经225" price={getDisplayPrice(nikkei)} change={nikkei?.change} changePct={nikkei?.change_pct} type="asia" loading={loadingUS} />
                <IndexItem code="KS11" name="韩国综合" price={getDisplayPrice(kospi)} change={kospi?.change} changePct={kospi?.change_pct} type="asia" loading={loadingUS} />
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .nav-link {
          color: var(--text-secondary);
          background-color: transparent;
        }
        .nav-link:hover {
          background-color: var(--bg-hover);
          color: var(--text-primary);
        }
      `}</style>
    </div>
  );
}
