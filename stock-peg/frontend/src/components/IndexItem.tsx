import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface IndexItemProps {
  code: string;
  name: string;
  price?: number;
  change?: number;
  changePct?: number;
  type?: 'cn' | 'us' | 'vix' | 'sector' | 'asia';
  showDivider?: boolean;
  loading?: boolean;
  compact?: boolean;
}

export default function IndexItem({ 
  name, 
  price, 
  changePct = 0,
  showDivider = false,
  loading = false,
  compact = false
}: IndexItemProps) {
  const isUp = changePct > 0;
  const isDown = changePct < 0;

  if (loading) {
    return (
      <div 
        className={`flex items-center gap-1.5 px-2 py-1 animate-pulse ${compact ? 'min-w-[100px]' : 'min-w-[120px]'}`}
        style={{ backgroundColor: 'var(--bg-hover)' }}
      >
        <div className="h-4 w-16" style={{ backgroundColor: 'var(--border-color)' }}></div>
        <div className="h-4 w-12" style={{ backgroundColor: 'var(--border-color)' }}></div>
      </div>
    );
  }

  return (
    <div 
      className={`flex items-center gap-1.5 px-2 py-1 transition-colors cursor-default group ${compact ? 'min-w-[100px]' : 'min-w-[120px]'}`}
      style={{ 
        backgroundColor: 'var(--bg-hover)',
      }}
    >
      <span 
        className={`text-xs font-medium whitespace-nowrap ${compact ? 'max-w-[60px] truncate' : ''}`}
        style={{ color: 'var(--text-secondary)' }}
        title={name}
      >
        {name}
      </span>
      
      {price !== undefined && (
        <div className="flex items-center gap-0.5">
          <span 
            className={`text-xs font-bold font-mono ${compact ? 'text-[10px]' : ''}`}
            style={{ color: 'var(--text-primary)' }}
          >
            {price.toFixed(2)}
          </span>
          
          <div 
            className="flex items-center"
            style={{ 
              color: isUp ? 'var(--success-color)' : isDown ? 'var(--danger-color)' : 'var(--text-muted)'
            }}
          >
            {!compact && (
              <>
                {isUp ? (
                  <TrendingUp size={10} />
                ) : isDown ? (
                  <TrendingDown size={10} />
                ) : (
                  <Minus size={10} />
                )}
              </>
            )}
            <span className={`text-xs font-semibold ${compact ? 'text-[10px]' : ''}`}>
              {isUp ? '+' : ''}{changePct.toFixed(2)}%
            </span>
          </div>
        </div>
      )}
      
      {showDivider && (
        <div className="w-px h-5 ml-1" style={{ backgroundColor: 'var(--border-color)' }}></div>
      )}
    </div>
  );
}
