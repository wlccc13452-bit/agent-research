import { useState, useRef, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';

interface HorizontalResizableDividerProps {
  onResize: (delta: number) => void;
  minHeight?: number;
  maxHeight?: number;
}

export default function HorizontalResizableDivider({ 
  onResize,
  minHeight = 50,
  maxHeight = 500
}: HorizontalResizableDividerProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  
  const [isDragging, setIsDragging] = useState(false);
  const startYRef = useRef(0);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      
      const deltaY = e.clientY - startYRef.current;
      onResize(deltaY);
      startYRef.current = e.clientY;
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, onResize, minHeight, maxHeight]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    startYRef.current = e.clientY;
  };

  return (
    <div
      className={`
        w-full h-1 bg-transparent hover:bg-blue-500 cursor-row-resize 
        flex-shrink-0 relative group transition-colors
        ${isDragging ? 'bg-blue-500' : ''}
      `}
      onMouseDown={handleMouseDown}
    >
      {/* 拖拽手柄指示器 */}
      <div className={`
        absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
        h-0.5 w-12
        group-hover:bg-blue-500 transition-colors
        ${isDragging ? 'bg-blue-500' : isDark ? 'bg-gray-600' : 'bg-gray-300'}
      `} />
    </div>
  );
}
