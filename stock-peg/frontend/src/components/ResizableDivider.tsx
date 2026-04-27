import { useState, useRef, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';

interface ResizableDividerProps {
  onResize: (newSize: number) => void;
  onResizeStart?: () => void;
  onResizeEnd?: () => void;
  direction?: 'left' | 'right';
  minSize?: number;
  maxSize?: number;
  currentSize?: number;
  className?: string;
}

export default function ResizableDivider({ 
  onResize, 
  onResizeStart,
  onResizeEnd,
  direction = 'right',
  minSize = 10,
  maxSize = 40,
  currentSize = 20,
  className = ''
}: ResizableDividerProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  
  const [isDragging, setIsDragging] = useState(false);
  const [isAtLimit, setIsAtLimit] = useState(false);
  const startXRef = useRef(0);
  const startSizeRef = useRef(0);
  const containerWidthRef = useRef(0);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      
      // 停止事件冒泡和默认行为，防止干扰其他组件
      e.stopPropagation();
      e.preventDefault();

      if (e.buttons !== 1) {
        setIsDragging(false);
        setIsAtLimit(false);
        onResizeEnd?.();
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        return;
      }
      
      const deltaX = e.clientX - startXRef.current;
      if (containerWidthRef.current <= 0) return;
      
      // 更加精确的百分比计算，考虑到容器内可能的边距
      // 实际上 deltaX / containerWidth 是最基础的转换
      const deltaPercent = (deltaX / containerWidthRef.current) * 100;
      
      const newSize = direction === 'left' 
        ? Math.max(minSize, Math.min(maxSize, startSizeRef.current + deltaPercent))
        : Math.max(minSize, Math.min(maxSize, startSizeRef.current - deltaPercent));
      
      // 检查是否到达边界（用于显示视觉反馈）
      const atLimit = (newSize >= maxSize) || (newSize <= minSize);
      setIsAtLimit(atLimit);
      
      // 只有在尺寸实际发生变化时才触发回调
      onResize(newSize);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setIsAtLimit(false);
      onResizeEnd?.();
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    const handleWindowBlur = () => {
      setIsDragging(false);
      setIsAtLimit(false);
      onResizeEnd?.();
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isDragging) {
      onResizeStart?.();
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      window.addEventListener('blur', handleWindowBlur);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('blur', handleWindowBlur);
    };
  }, [isDragging, onResize, onResizeStart, onResizeEnd, direction, minSize, maxSize, currentSize]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    startXRef.current = e.clientX;
    startSizeRef.current = currentSize;
    
    const container = e.currentTarget.closest('[data-resize-container]') as HTMLElement | null;
    containerWidthRef.current = Math.max(1, container?.offsetWidth || window.innerWidth);
  };

  return (
    <div
      className={`
        w-1 h-full bg-transparent hover:bg-blue-500 cursor-col-resize 
        flex-shrink-0 relative group transition-colors
        ${isDragging ? 'bg-blue-500' : ''}
        ${isAtLimit ? 'bg-red-500 hover:bg-red-500' : ''}
        ${className}
      `}
      onMouseDown={handleMouseDown}
    >
      {/* 拖拽手柄指示器 */}
      <div className={`
        absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
        w-0.5 h-8 transition-colors
        ${isAtLimit 
          ? 'bg-red-500' 
          : isDragging 
            ? 'bg-blue-500' 
            : 'group-hover:bg-blue-500'
        }
        ${!isDragging && !isAtLimit ? (isDark ? 'bg-gray-600' : 'bg-gray-300') : ''}
      `} />
    </div>
  );
}
