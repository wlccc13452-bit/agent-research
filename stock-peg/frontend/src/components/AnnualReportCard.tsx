/**
 * 年报/季报卡片组件
 * 显示最新年报或季报的财务摘要
 */
import { FileText } from 'lucide-react';
import CollapsibleCard from './CollapsibleCard';
import { useTheme } from '../contexts/ThemeContext';

interface AnnualReportCardProps {
  annualReport: any;
  stockCode: string | null;
}

export default function AnnualReportCard({ annualReport, stockCode }: AnnualReportCardProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <CollapsibleCard 
      title="最新年报或季报" 
      icon={<FileText size={16} style={{ color: 'var(--warning-color)' }} />}
      defaultOpen={false}
      className="flex-shrink-0"
    >
      <div className="p-2 space-y-2">
        {annualReport && (annualReport.report_date || annualReport.revenue || annualReport.net_profit || annualReport.basic_eps) ? (
          <>
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2" style={{ backgroundColor: 'var(--bg-dark)' }}>
                <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>报告类型</div>
                <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                  {annualReport.report_type || '年报'}
                </div>
              </div>
              <div className="p-2" style={{ backgroundColor: 'var(--bg-dark)' }}>
                <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>报告期</div>
                <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{annualReport.report_date || annualReport.end_date || '--'}</div>
              </div>
              <div className="p-2" style={{ backgroundColor: 'var(--bg-dark)' }}>
                <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>营业收入</div>
                <div className="text-sm font-bold font-mono" style={{ color: 'var(--text-primary)' }}>
                  {annualReport.revenue 
                    ? `${(annualReport.revenue / 100000000).toFixed(2)}亿` 
                    : '--'}
                </div>
              </div>
              <div className="p-2" style={{ backgroundColor: 'var(--bg-dark)' }}>
                <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>净利润</div>
                <div className="text-sm font-bold font-mono" style={{
                  color: annualReport.net_profit > 0 ? 'var(--success-color)' : 'var(--danger-color)'
                }}>
                  {annualReport.net_profit 
                    ? `${(annualReport.net_profit / 100000000).toFixed(2)}亿` 
                    : '--'}
                </div>
              </div>
              <div className="p-2" style={{ backgroundColor: 'var(--bg-dark)' }}>
                <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>毛利</div>
                <div className="text-sm font-bold font-mono" style={{ color: 'var(--text-primary)' }}>
                  {annualReport.gross_profit 
                    ? `${(annualReport.gross_profit / 100000000).toFixed(2)}亿` 
                    : '--'}
                </div>
              </div>
              <div className="p-2" style={{ backgroundColor: 'var(--bg-dark)' }}>
                <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>毛利率</div>
                <div className="text-sm font-bold font-mono" style={{ color: 'var(--text-primary)' }}>
                  {annualReport.revenue && annualReport.gross_profit
                    ? `${(annualReport.gross_profit / annualReport.revenue * 100).toFixed(2)}%`
                    : '--'}
                </div>
              </div>
              <div className="p-2" style={{ backgroundColor: 'var(--bg-dark)' }}>
                <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>每股收益</div>
                <div className="text-sm font-bold font-mono" style={{ color: 'var(--text-primary)' }}>
                  {annualReport.eps?.toFixed(2) || annualReport.basic_eps?.toFixed(2) || '--'}
                </div>
              </div>
              <div className="p-2" style={{ backgroundColor: 'var(--bg-dark)' }}>
                <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>数据来源</div>
                <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                  {annualReport.data_source === 'markdown' ? '本地资料' : '实时数据'}
                </div>
              </div>
            </div>
            
            {annualReport.summary && (
              <div className="p-2 text-xs leading-relaxed" style={{ 
                backgroundColor: isDark ? 'rgba(59, 130, 246, 0.1)' : '#eff6ff',
                color: isDark ? '#93c5fd' : '#1e40af'
              }}>
                {annualReport.summary}
              </div>
            )}
          </>
        ) : (
          <div className="space-y-2">
            <div className="text-center py-3 text-xs" style={{ color: 'var(--text-secondary)' }}>
              <div className="mb-2">暂无年报或季报数据</div>
            </div>
            <div className="p-2 text-xs leading-relaxed" style={{ 
              backgroundColor: isDark ? 'rgba(251, 191, 36, 0.1)' : '#fffbeb',
              color: isDark ? '#fbbf24' : '#92400e',
              borderLeft: '3px solid var(--warning-color)'
            }}>
              <div className="font-medium mb-1">💡 提示</div>
              <ul className="space-y-1 ml-3">
                <li>• 可能原因：新上市股票暂无财务数据</li>
                <li>• 建议：查看公司公告或定期报告</li>
                <li>• 可手动创建资料文件：backend/data/stock_profiles/{stockCode}.md</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </CollapsibleCard>
  );
}
