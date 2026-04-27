import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { reportApi } from '../services/api';
import { FileText, Download } from 'lucide-react';
import PMRDataTable from '../components/PMRDataTable';

export default function Reports() {
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );

  // 获取报告列表
  const { data: reportsData, isLoading } = useQuery({
    queryKey: ['reports', selectedDate],
    queryFn: () =>
      reportApi.getList({
        start_date: selectedDate,
        end_date: selectedDate,
      }),
  });

  // 获取报告详情
  const [selectedReport, setSelectedReport] = useState<any>(null);

  const { data: reportDetail } = useQuery({
    queryKey: ['report-detail', selectedReport],
    queryFn: () =>
      reportApi.getDetail(
        selectedReport.stock_code,
        selectedReport.report_date
      ),
    enabled: !!selectedReport,
  });

  if (isLoading) {
    return <div className="loading">加载中...</div>;
  }

  const reports = reportsData?.reports || [];

  return (
    <div className="reports-page">
      <div className="page-header">
        <h2>分析报告</h2>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="date-picker"
        />
      </div>

      <div className="reports-container">
        {/* 报告列表 */}
        <div className="reports-list">
          <h3>报告列表 ({reports.length})</h3>
          {reports.map((report: any) => (
            <div
              key={report.id}
              className={`report-item ${
                selectedReport?.id === report.id ? 'active' : ''
              }`}
              onClick={() => setSelectedReport(report)}
            >
              <FileText className="report-icon" />
              <div className="report-info">
                <h4>{report.stock_name}</h4>
                <p>
                  {report.report_date} | 评分: {report.overall_score?.toFixed(1) || 'N/A'}
                </p>
              </div>
              <div className="report-prediction">
                <span className={`direction ${report.predict_direction}`}>
                  {report.predict_direction}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* 报告详情 */}
        <div className="report-detail">
          {reportDetail ? (
            <>
              <div className="detail-header">
                <h3>
                  {reportDetail.stock_name} ({reportDetail.stock_code})
                </h3>
                <p>{reportDetail.report_date}</p>
                <button className="btn-icon" title="导出报告">
                  <Download className="icon" />
                </button>
              </div>

              {/* 行情回顾 */}
              <div className="detail-section">
                <h4>行情回顾</h4>
                <div className="market-grid">
                  <div className="market-item">
                    <span>开盘</span>
                    <span>{reportDetail.market?.open?.toFixed(2)}</span>
                  </div>
                  <div className="market-item">
                    <span>收盘</span>
                    <span>{reportDetail.market?.close?.toFixed(2)}</span>
                  </div>
                  <div className="market-item">
                    <span>最高</span>
                    <span>{reportDetail.market?.high?.toFixed(2)}</span>
                  </div>
                  <div className="market-item">
                    <span>最低</span>
                    <span>{reportDetail.market?.low?.toFixed(2)}</span>
                  </div>
                  <div className="market-item">
                    <span>涨跌幅</span>
                    <span className={reportDetail.market?.change_pct > 0 ? 'up' : 'down'}>
                      {reportDetail.market?.change_pct?.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* 预测结果 */}
              <div className="detail-section">
                <h4>明日预测</h4>
                <div className="prediction-box">
                  <div className="prediction-main">
                    <span className="direction-label">预测方向</span>
                    <span className={`direction-value ${reportDetail.prediction?.direction}`}>
                      {reportDetail.prediction?.direction}
                    </span>
                  </div>
                  <div className="prediction-info">
                    <span>概率: {(reportDetail.prediction?.probability * 100).toFixed(1)}%</span>
                    <span>置信度: {reportDetail.prediction?.confidence}</span>
                    <span>风险: {reportDetail.prediction?.risk_level}</span>
                  </div>
                </div>
              </div>

              {/* 操作建议 */}
              <div className="detail-section">
                <h4>操作建议</h4>
                <div className="action-box">
                  <div className="action-main">
                    <span className="action-label">建议</span>
                    <span className="action-value">{reportDetail.action?.action}</span>
                  </div>
                  <div className="action-info">
                    <span>仓位: {reportDetail.action?.position}%</span>
                    {reportDetail.action?.stop_loss && (
                      <span>止损: {reportDetail.action.stop_loss.toFixed(2)}</span>
                    )}
                    {reportDetail.action?.take_profit && (
                      <span>止盈: {reportDetail.action.take_profit.toFixed(2)}</span>
                    )}
                  </div>
                </div>
              </div>

              {/* 综合评分 */}
              <div className="detail-section">
                <h4>综合评分</h4>
                <div className="scores-grid">
                  <div className="score-item">
                    <span>技术面</span>
                    <span className="score">{reportDetail.technical?.score?.toFixed(1)}</span>
                  </div>
                  <div className="score-item">
                    <span>基本面</span>
                    <span className="score">{reportDetail.fundamental?.score?.toFixed(1)}</span>
                  </div>
                  <div className="score-item">
                    <span>资金面</span>
                    <span className="score">{reportDetail.money?.score?.toFixed(1)}</span>
                  </div>
                  <div className="score-item">
                    <span>消息面</span>
                    <span className="score">{reportDetail.news?.score?.toFixed(1)}</span>
                  </div>
                  <div className="score-item highlight">
                    <span>综合</span>
                    <span className="score">{reportDetail.summary?.overall_score?.toFixed(1)}</span>
                  </div>
                </div>
              </div>

              {/* 报告总结 */}
              {reportDetail.summary?.summary && (
                <div className="detail-section">
                  <h4>报告总结</h4>
                  <div className="summary-text">{reportDetail.summary.summary}</div>
                </div>
              )}

              {/* 智能分析（新增） */}
              {reportDetail.smart_analysis && (
                <div className="detail-section">
                  <h4>
                    🤖 智能分析
                    {reportDetail.smart_analysis.llm_model && (
                      <span className="text-sm font-normal text-gray-500 ml-2">
                        (由 {reportDetail.smart_analysis.llm_model} 生成)
                      </span>
                    )}
                  </h4>

                  {/* PMR 数据表格 */}
                  {reportDetail.smart_analysis.raw?.pmr_summary && (
                    <div className="mb-4">
                      <h5 className="text-md font-semibold text-gray-700 mb-2">PMR 数据分析</h5>
                      <PMRDataTable data={reportDetail.smart_analysis.raw.pmr_summary} />
                    </div>
                  )}

                  {/* 格式化后的分析内容 */}
                  {reportDetail.smart_analysis.formatted && (
                    <div className="smart-analysis-content">
                      <div
                        className="prose prose-sm max-w-none"
                        dangerouslySetInnerHTML={{
                          __html: formatMarkdown(reportDetail.smart_analysis.formatted),
                        }}
                      />
                    </div>
                  )}

                  {/* LLM 原始数据（可折叠） */}
                  {reportDetail.smart_analysis.raw && (
                    <details className="mt-4">
                      <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                        查看原始 JSON 数据
                      </summary>
                      <pre className="mt-2 p-4 bg-gray-50 rounded-lg overflow-x-auto text-xs">
                        {JSON.stringify(reportDetail.smart_analysis.raw, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="no-report">
              <FileText className="no-report-icon" />
              <p>选择一份报告查看详情</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// 简单的 Markdown 格式化函数
function formatMarkdown(markdown: string): string {
  if (!markdown) return '';

  return (
    markdown
      // 标题
      .replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold text-gray-800 mt-4 mb-2">$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold text-gray-900 mt-6 mb-3">$1</h2>')
      .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold text-gray-900 mt-8 mb-4">$1</h1>')
      // 粗体
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
      // 列表项
      .replace(/^- (.*$)/gim, '<li class="ml-4">$1</li>')
      // 换行
      .replace(/\n/g, '<br>')
      // 分割线
      .replace(/---/g, '<hr class="my-4 border-gray-200">')
  );
}
