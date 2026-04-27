import { X, Download, Copy, Check } from 'lucide-react';
import { useMemo, useState, type ReactNode } from 'react';
import { useTheme } from '../contexts/ThemeContext';

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  content: string;
  stockCode?: string;
  stockName?: string;
  reportDate?: string;
}

const formatInline = (text: string) => {
  const segments = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);
  return segments.map((segment, index) => {
    if (segment.startsWith('`') && segment.endsWith('`')) {
      return (
        <code
          key={index}
          className="px-1 py-0.5 rounded text-[11px] bg-gray-100 text-gray-700 dark:bg-[#2a2a2a] dark:text-gray-300"
        >
          {segment.slice(1, -1)}
        </code>
      );
    }
    if (segment.startsWith('**') && segment.endsWith('**')) {
      return <strong key={index} className="font-semibold">{segment.slice(2, -2)}</strong>;
    }
    return segment;
  });
};

const parseTableCells = (line: string) => {
  const raw = line.trim().replace(/^\|/, '').replace(/\|$/, '');
  return raw.split('|').map(cell => cell.trim());
};

const renderMarkdown = (markdown: string): ReactNode[] => {
  const lines = markdown.split('\n');
  const blocks: ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      i += 1;
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const title = headingMatch[2];
      const headingClass = level === 1
        ? 'text-xl font-bold mt-2 mb-3'
        : level === 2
          ? 'text-lg font-bold mt-4 mb-2'
          : 'text-base font-semibold mt-3 mb-1.5';
      blocks.push(
        <div key={`h-${i}`} className={headingClass}>
          {formatInline(title)}
        </div>
      );
      i += 1;
      continue;
    }

    if (/^---+$/.test(trimmed)) {
      blocks.push(<div key={`hr-${i}`} className="border-t border-gray-200 dark:border-[#2a2a2a] my-3" />);
      i += 1;
      continue;
    }

    const next = lines[i + 1]?.trim() || '';
    const isTableHeader = trimmed.includes('|') && /^[:|\-\s]+$/.test(next);
    if (isTableHeader) {
      const header = parseTableCells(trimmed);
      const rows: string[][] = [];
      i += 2;
      while (i < lines.length && lines[i].trim().includes('|')) {
        rows.push(parseTableCells(lines[i]));
        i += 1;
      }
      blocks.push(
        <div key={`table-${i}`} className="overflow-x-auto my-2">
          <table className="min-w-full text-xs border border-gray-200 dark:border-[#2a2a2a]">
            <thead className="bg-gray-100 dark:bg-[#141414]">
              <tr>
                {header.map((cell, idx) => (
                  <th key={idx} className="px-2 py-1.5 text-left border-b border-gray-200 dark:border-[#2a2a2a]">
                    {formatInline(cell)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIdx) => (
                <tr key={rowIdx} className="border-b border-gray-100 dark:border-[#222]">
                  {row.map((cell, cellIdx) => (
                    <td key={cellIdx} className="px-2 py-1.5 align-top">
                      {formatInline(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*]\s+/, ''));
        i += 1;
      }
      blocks.push(
        <ul key={`ul-${i}`} className="list-disc pl-5 my-1.5 space-y-1 text-sm">
          {items.map((item, idx) => <li key={idx}>{formatInline(item)}</li>)}
        </ul>
      );
      continue;
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s+/, ''));
        i += 1;
      }
      blocks.push(
        <ol key={`ol-${i}`} className="list-decimal pl-5 my-1.5 space-y-1 text-sm">
          {items.map((item, idx) => <li key={idx}>{formatInline(item)}</li>)}
        </ol>
      );
      continue;
    }

    const paragraph: string[] = [trimmed];
    i += 1;
    while (i < lines.length) {
      const cursor = lines[i].trim();
      if (!cursor || /^(#{1,6})\s+/.test(cursor) || /^---+$/.test(cursor) || /^[-*]\s+/.test(cursor) || /^\d+\.\s+/.test(cursor) || (cursor.includes('|') && /^[:|\-\s]+$/.test(lines[i + 1]?.trim() || ''))) {
        break;
      }
      paragraph.push(cursor);
      i += 1;
    }
    blocks.push(
      <p key={`p-${i}`} className="my-1.5 text-sm leading-6">
        {formatInline(paragraph.join(' '))}
      </p>
    );
  }

  return blocks;
};

export default function ReportModal({
  isOpen,
  onClose,
  title,
  content,
  stockCode,
  stockName,
  reportDate
}: ReportModalProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [copied, setCopied] = useState(false);
  const formattedContent = useMemo(() => renderMarkdown(content || ''), [content]);

  if (!isOpen) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDownload = () => {
    const element = document.createElement('a');
    const file = new Blob([content], { type: 'text/markdown' });
    element.href = URL.createObjectURL(file);
    element.download = `${stockName || '股票'}_${reportDate || '报告'}.md`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div 
          className={`relative w-full max-w-4xl transform overflow-hidden rounded-lg shadow-2xl transition-all ${
            isDark 
              ? 'bg-[#1a1a1a] border border-[#2a2a2a]' 
              : 'bg-white border border-gray-200'
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className={`flex items-center justify-between px-6 py-4 border-b ${
            isDark ? 'border-[#2a2a2a] bg-[#0f0f0f]' : 'border-gray-200 bg-gray-50'
          }`}>
            <div className="flex-1">
              <h2 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {title}
              </h2>
              <div className={`flex items-center gap-3 mt-1 text-xs ${
                isDark ? 'text-gray-400' : 'text-gray-600'
              }`}>
                {stockName && <span>{stockName}</span>}
                {stockCode && <span className="font-mono">({stockCode})</span>}
                {reportDate && <span>· {reportDate}</span>}
              </div>
            </div>
            
            {/* Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className={`p-2 rounded transition-colors ${
                  isDark 
                    ? 'hover:bg-[#2a2a2a] text-gray-400 hover:text-white' 
                    : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
                }`}
                title="复制内容"
              >
                {copied ? <Check size={18} className="text-green-500" /> : <Copy size={18} />}
              </button>
              <button
                onClick={handleDownload}
                className={`p-2 rounded transition-colors ${
                  isDark 
                    ? 'hover:bg-[#2a2a2a] text-gray-400 hover:text-white' 
                    : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
                }`}
                title="下载报告"
              >
                <Download size={18} />
              </button>
              <button
                onClick={onClose}
                className={`p-2 rounded transition-colors ${
                  isDark 
                    ? 'hover:bg-[#2a2a2a] text-gray-400 hover:text-white' 
                    : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
                }`}
                title="关闭"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-6 max-h-[70vh] overflow-y-auto">
            <div className={`${isDark ? 'text-gray-300' : 'text-gray-800'}`}>
              {formattedContent}
            </div>
          </div>

          {/* Footer */}
          <div className={`px-6 py-4 border-t flex items-center justify-between ${
            isDark ? 'border-[#2a2a2a] bg-[#0f0f0f]' : 'border-gray-200 bg-gray-50'
          }`}>
            <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-600'}`}>
              智能分析报告由 AI 生成，仅供参考
            </div>
            <button
              onClick={onClose}
              className={`px-4 py-2 rounded font-medium text-sm transition-colors ${
                isDark 
                  ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
              }`}
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
