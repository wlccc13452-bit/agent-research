import { useState, type ReactNode } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface CollapsibleCardProps {
  title: string;
  icon?: ReactNode;
  defaultOpen?: boolean;
  children: ReactNode;
  className?: string;
  headerClassName?: string;
  badge?: ReactNode;
  action?: ReactNode;
}

export default function CollapsibleCard({
  title,
  icon,
  defaultOpen = false,
  children,
  className = '',
  headerClassName = '',
  badge,
  action,
}: CollapsibleCardProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div 
      className={`shadow-sm overflow-hidden ${className}`}
      style={{ 
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-color)'
      }}
    >
      <div 
        className={`flex items-center justify-between px-4 py-3 cursor-pointer transition-colors ${headerClassName}`}
        style={{ backgroundColor: 'transparent' }}
        onClick={() => setIsOpen(!isOpen)}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-hover)'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {icon}
          <h3 
            className="text-sm font-bold truncate"
            style={{ color: 'var(--text-primary)' }}
          >
            {title}
          </h3>
          {badge}
        </div>
        <div className="flex items-center gap-2">
          {action && (
            <div onClick={(e) => e.stopPropagation()}>
              {action}
            </div>
          )}
          {isOpen ? (
            <ChevronDown size={16} className="flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
          ) : (
            <ChevronRight size={16} className="flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
          )}
        </div>
      </div>
      {isOpen && (
        <div className="animate-in fade-in duration-200">
          {children}
        </div>
      )}
    </div>
  );
}
