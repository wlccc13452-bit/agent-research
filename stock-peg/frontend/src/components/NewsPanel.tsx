import { useQuery } from '@tanstack/react-query';
import { newsApi } from '../services/api';
import { Newspaper, Clock, ExternalLink } from 'lucide-react';

interface NewsPanelProps {
  stockCode?: string;
  sectorName?: string;
  limit?: number;
  compact?: boolean;
  marketMode?: boolean;
  recentDays?: number;
  fallbackToHot?: boolean;
  fontScale?: number;
  isDark?: boolean;
  themeConfig?: {
    rowTheme: {
      light: {
        odd: string;
        even: string;
      };
      dark: {
        odd: string;
        even: string;
      };
    };
  };
}

export default function NewsPanel({
  stockCode,
  sectorName,
  limit = 10,
  compact = false,
  marketMode = false,
  recentDays = 7,
  fallbackToHot = true,
  fontScale = 1,
  isDark = false,
  themeConfig
}: NewsPanelProps) {
  const parsePublishDate = (item: any) => {
    const raw = item?.publish_time || item?.pub_time || item?.publishTime || item?.time;
    if (!raw) return null;
    const date = new Date(raw);
    if (!isNaN(date.getTime())) return date;
    if (typeof raw === 'number') {
      const asTimestamp = raw > 1e12 ? raw : raw * 1000;
      const fromNum = new Date(asTimestamp);
      return isNaN(fromNum.getTime()) ? null : fromNum;
    }
    return null;
  };

  const { data: newsData, isLoading } = useQuery({
    queryKey: ['news', stockCode, sectorName, limit, marketMode, recentDays, fallbackToHot],
    queryFn: async () => {
      if (marketMode) {
        if (sectorName) {
          const sectorResponse = await newsApi.getSectorNews(sectorName, Math.max(limit * 3, 30));
          const now = Date.now();
          const cutoff = now - recentDays * 24 * 60 * 60 * 1000;
          const recentSectorNews = (sectorResponse?.news || []).filter((item: any) => {
            const publishDate = parsePublishDate(item);
            return publishDate ? publishDate.getTime() >= cutoff : false;
          });
          if (recentSectorNews.length > 0) {
            return {
              ...sectorResponse,
              news: recentSectorNews.slice(0, limit),
              _mode: 'sector-week',
              _label: `近${recentDays}天 ${sectorName}板块`
            };
          }
        }
        if (fallbackToHot) {
          const hotResponse = await newsApi.getHotNews(limit);
          return {
            ...hotResponse,
            _mode: 'market-hot',
            _label: '全市场重大新闻'
          };
        }
        return { news: [] };
      }
      if (stockCode) {
        return newsApi.getStockNews(stockCode, limit);
      } else if (sectorName) {
        return newsApi.getSectorNews(sectorName, limit);
      } else {
        return newsApi.getHotNews(limit);
      }
    },
    refetchInterval: 5 * 60 * 1000,
  });

  const news = newsData?.news || [];
  const modeLabel = newsData?._label;
  const rowTheme = isDark ? themeConfig?.rowTheme?.dark : themeConfig?.rowTheme?.light;
  const oddRowColor = rowTheme?.odd || (isDark ? '#0d1522' : '#ffffff');
  const evenRowColor = rowTheme?.even || (isDark ? '#0a101a' : '#f8fafc');

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4 p-4 animate-pulse">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 bg-gray-100 dark:bg-gray-800"></div>
        ))}
      </div>
    );
  }

  if (!news || news.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-gray-400 dark:text-gray-500 gap-2">
        <Newspaper size={32} strokeWidth={1.5} />
        <p className="text-sm font-medium">暂无新闻资讯</p>
      </div>
    );
  }

  return (
    <div className={`h-full overflow-y-auto custom-scrollbar ${
      marketMode && isDark ? 'bg-[#0a101a]' : 'bg-transparent'
    }`}>
      <div>
        {modeLabel && (
          <div className={`px-3 py-1.5 text-[10px] font-bold tracking-wide border-b ${
            isDark ? 'text-blue-300 border-[#2f3d55] bg-[#121a26]' : 'text-blue-700 border-blue-100 bg-blue-50/70'
          }`}>
            {modeLabel}
          </div>
        )}
        {news.map((item: any, index: number) => {
          const publishTime = (() => {
            const date = parsePublishDate(item);
            return !date
              ? null
              : date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
          })();
          const rowBgColor = index % 2 === 0 ? oddRowColor : evenRowColor;
          const rowBorderColor = isDark ? '#334155' : '#cbd5e1';
          return (
            <a
              key={index}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className={`block group transition-colors ${compact ? 'px-3 py-2' : 'px-4 py-2.5'}`}
              style={{ backgroundColor: rowBgColor, borderLeft: `2px solid ${rowBorderColor}` }}
            >
              <div className="flex items-center justify-between gap-2 min-w-0">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <span className={`${isDark ? 'text-white' : 'text-slate-500'}`} title={item.source || '新闻来源'}>
                    <Newspaper size={11} />
                  </span>
                <p
                  className={`font-normal leading-snug line-clamp-1 ${
                    isDark ? 'text-white group-hover:text-white' : 'text-slate-800 group-hover:text-slate-900'
                  }`}
                  style={{ fontSize: `${Math.max(11, 13 * fontScale)}px` }}
                >
                  {item.title}
                </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {publishTime && (
                    <span
                      className={`${isDark ? 'text-slate-200' : 'text-slate-500'}`}
                      style={{ fontSize: `${Math.max(9, 10 * fontScale)}px` }}
                    >
                      <span className="inline-flex items-center gap-1">
                        <Clock size={10} />
                        {publishTime}
                      </span>
                    </span>
                  )}
                {item.sentiment && (
                  <span className={`text-[10px] font-medium ${
                    item.sentiment === 'positive'
                      ? 'text-red-500'
                      : item.sentiment === 'negative'
                        ? 'text-green-500'
                        : isDark
                          ? 'text-white'
                          : 'text-slate-600'
                  }`}>
                    {item.sentiment === 'positive' ? '看多' : item.sentiment === 'negative' ? '看空' : '中性'}
                  </span>
                )}
                <ExternalLink size={13} className={`${isDark ? 'text-slate-300 group-hover:text-white' : 'text-slate-400 group-hover:text-slate-700'}`} />
              </div>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
