import { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import VolumeChart from './VolumeChart';
import MACDChart from './MACDChart';
import PMR5Chart from './PMR5Chart';
import PMRMultiChart from './PMRMultiChart';
import ForceIndexChart from './ForceIndexChart';

type IndicatorType = 'volume' | 'macd' | 'pmr5' | 'pmr-multi' | 'forceindex';

interface IndicatorContainerProps {
  // 成交量数据
  volumeData?: Array<{
    date: string;
    open: number;
    close: number;
    volume: number;
  }>;
  // MACD数据
  macdData?: {
    dif: number[];
    dea: number[];
    macdHist: number[];
  };
  dates?: string[];
  zoomRange?: {
    start: number;
    end: number;
  };
  // PMR数据
  pmrData?: {
    dates: string[];
    pmr5?: (number | null)[];
    pmr10?: (number | null)[];
    pmr20?: (number | null)[];
    pmr30?: (number | null)[];
    pmr60?: (number | null)[];
  };
  // Force Index数据
  forceIndexData?: {
    dates: string[];
    rawForceIndex: number[];
    fi2Ema: number[];
    fi13Ema: number[];
  };
  // 默认显示的指标
  defaultIndicator?: IndicatorType;
  // 指标变化回调
  onIndicatorChange?: (indicator: IndicatorType) => void;
  // 高度变化回调
  onHeightChange?: (height: number) => void;
  // 暴露chart实例
  chartRef?: React.RefObject<any>;
}

export default function IndicatorContainer({
  volumeData,
  macdData,
  dates,
  zoomRange,
  pmrData,
  forceIndexData,
  defaultIndicator = 'volume',
  onIndicatorChange,
  chartRef,
}: IndicatorContainerProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [selectedIndicator, setSelectedIndicator] = useState<IndicatorType>(defaultIndicator);

  const handleIndicatorChange = (indicator: IndicatorType) => {
    setSelectedIndicator(indicator);
    onIndicatorChange?.(indicator);
  };

  const getIndicatorName = (indicator: IndicatorType) => {
    switch (indicator) {
      case 'volume': return '成交量';
      case 'macd': return 'MACD';
      case 'pmr5': return 'PMR5';
      case 'pmr-multi': return 'PMR多周期';
      default: return indicator;
    }
  };

  return (
    <div className={`relative w-full h-full flex flex-col ${
      isDark ? 'bg-[#0a0a0a]' : 'bg-white'
    }`}>
      {/* 左上角选择器 */}
      <div className="absolute top-2 left-2 z-10">
        <select
          value={selectedIndicator}
          onChange={(e) => handleIndicatorChange(e.target.value as IndicatorType)}
          className={`px-2 py-1 text-xs font-medium rounded border transition-colors ${
            isDark 
              ? 'bg-[#1a1a1a] border-[#2a2a2a] text-gray-300 hover:border-blue-500' 
              : 'bg-white border-gray-300 text-gray-700 hover:border-blue-500'
          } focus:outline-none focus:ring-1 focus:ring-blue-500`}
        >
          <option value="volume">成交量</option>
          <option value="macd">MACD</option>
          <option value="pmr5">PMR5</option>
          <option value="pmr-multi">PMR多周期</option>
          <option value="forceindex">Force Index</option>
        </select>
      </div>

      {/* 图表内容 */}
      <div className="w-full h-full">
        {selectedIndicator === 'volume' && volumeData && volumeData.length > 0 && (
          <VolumeChart data={volumeData} zoomRange={zoomRange} ref={chartRef} />
        )}
        
        {selectedIndicator === 'macd' && macdData && dates && dates.length > 0 && (
          <MACDChart data={macdData} dates={dates} zoomRange={zoomRange} ref={chartRef} />
        )}
        
        {selectedIndicator === 'pmr5' && pmrData && pmrData.dates && pmrData.dates.length > 0 && pmrData.pmr5 && (
          <PMR5Chart data={{ dates: pmrData.dates, pmr5: pmrData.pmr5 }} zoomRange={zoomRange} ref={chartRef} />
        )}
        
        {selectedIndicator === 'pmr-multi' && pmrData && pmrData.dates && pmrData.dates.length > 0 && (
          <PMRMultiChart data={{
            dates: pmrData.dates,
            pmr10: pmrData.pmr10,
            pmr20: pmrData.pmr20,
            pmr30: pmrData.pmr30,
            pmr60: pmrData.pmr60
          }} zoomRange={zoomRange} ref={chartRef} />
        )}
        
        {selectedIndicator === 'forceindex' && forceIndexData && forceIndexData.dates && forceIndexData.dates.length > 0 && (
          <ForceIndexChart data={forceIndexData} zoomRange={zoomRange} ref={chartRef} />
        )}
        
        {/* 空状态 */}
        {((selectedIndicator === 'volume' && (!volumeData || volumeData.length === 0)) ||
          (selectedIndicator === 'macd' && (!macdData || !dates || dates.length === 0)) ||
          (selectedIndicator === 'pmr5' && (!pmrData || !pmrData.dates || pmrData.dates.length === 0 || !pmrData.pmr5)) ||
          (selectedIndicator === 'pmr-multi' && (!pmrData || !pmrData.dates || pmrData.dates.length === 0)) ||
          (selectedIndicator === 'forceindex' && (!forceIndexData || !forceIndexData.dates || forceIndexData.dates.length === 0))) && (
          <div className={`flex items-center justify-center h-full ${
            isDark ? 'text-gray-500' : 'text-gray-400'
          }`}>
            <p className="text-sm">暂无{getIndicatorName(selectedIndicator)}数据</p>
          </div>
        )}
      </div>
    </div>
  );
}


