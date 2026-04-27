import { useState, useEffect, useCallback } from 'react';
import { configApi } from '../services/api';
import layoutConfigRaw from '../config/layout.json?raw';

export interface LayoutConfig {
  leftPanelWidth: number;
  rightPanelWidth: number;
  centerPanelMinWidth: number;
  headbarHeight: number;
  statusbarHeight: number;
}

const parsedDefaultConfig = (() => {
  try {
    return JSON.parse(layoutConfigRaw) as Partial<LayoutConfig>;
  } catch {
    return {};
  }
})();

export const DEFAULT_LAYOUT_CONFIG: LayoutConfig = {
  leftPanelWidth: parsedDefaultConfig.leftPanelWidth ?? 18,
  rightPanelWidth: parsedDefaultConfig.rightPanelWidth ?? 22,
  centerPanelMinWidth: parsedDefaultConfig.centerPanelMinWidth ?? 30,
  headbarHeight: parsedDefaultConfig.headbarHeight ?? 56,
  statusbarHeight: parsedDefaultConfig.statusbarHeight ?? 32
};

const isValidLayoutConfig = (config: Partial<LayoutConfig> | null | undefined): config is LayoutConfig => {
  if (!config) return false;
  const left = config.leftPanelWidth;
  const right = config.rightPanelWidth;
  const centerMin = config.centerPanelMinWidth;
  const headbar = config.headbarHeight;
  const statusbar = config.statusbarHeight;
  if (
    typeof left !== 'number' ||
    typeof right !== 'number' ||
    typeof centerMin !== 'number' ||
    typeof headbar !== 'number' ||
    typeof statusbar !== 'number'
  ) {
    return false;
  }
  const total = left + right;
  const centerWidth = 100 - total;
  return centerWidth >= centerMin && total <= 95;
};

const getLocalLayoutConfig = (): LayoutConfig | null => {
  const localConfig = localStorage.getItem('layoutConfig');
  if (!localConfig) return null;
  try {
    const parsed = JSON.parse(localConfig) as Partial<LayoutConfig>;
    return isValidLayoutConfig(parsed) ? parsed : null;
  } catch {
    return null;
  }
};

export function useLayoutConfig() {
  const [config, setConfig] = useState<LayoutConfig>(() => getLocalLayoutConfig() ?? DEFAULT_LAYOUT_CONFIG);
  const [isLoading, setIsLoading] = useState(true);

  // 加载配置
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setIsLoading(true);
      const localConfig = getLocalLayoutConfig();

      if (localConfig) {
        setConfig(localConfig);
      } else {
        setConfig(DEFAULT_LAYOUT_CONFIG);
        localStorage.setItem('layoutConfig', JSON.stringify(DEFAULT_LAYOUT_CONFIG));
      }
    } catch (error) {
      console.error('加载布局配置失败:', error);
      setConfig(DEFAULT_LAYOUT_CONFIG);
    } finally {
      setIsLoading(false);
    }
  };

  const saveConfig = useCallback(async (newConfig: Partial<LayoutConfig>, persist: boolean = true) => {
    // 检查是否有实际变化
    const isChanged = Object.entries(newConfig).some(([key, value]) => {
      return (config as any)[key] !== value;
    });

    if (!isChanged) {
      return true;
    }

    const updated = { ...config, ...newConfig };
    
    // 验证：确保中间面板有足够宽度
    const total = updated.leftPanelWidth + updated.rightPanelWidth;
    const centerWidth = 100 - total;
    
    if (centerWidth < updated.centerPanelMinWidth) {
      // 在非持久化模式下（拖拽中），如果超出限制，不更新状态
      if (!persist) return false;
      
      console.warn(`中间面板宽度不足: 当前${centerWidth.toFixed(1)}%, 最小要求${updated.centerPanelMinWidth}%`);
      return false;
    }
    
    // 确保总宽度不超过100%
    if (total > 95) {
      if (!persist) return false;
      console.warn('面板总宽度超过95%，请调整');
      return false;
    }
    
    // 立即更新本地状态以保证UI响应流畅
    setConfig(updated);
    
    // 如果不需要持久化到服务器（例如在拖拽中），到此为止
    if (!persist) {
      return true;
    }

    localStorage.setItem('layoutConfig', JSON.stringify(updated));
    
    try {
      await configApi.updateLayoutConfig({
        left_panel_width: Math.round(updated.leftPanelWidth),
        right_panel_width: Math.round(updated.rightPanelWidth),
        center_panel_min_width: Math.round(updated.centerPanelMinWidth),
        headbar_height: Math.round(updated.headbarHeight),
        statusbar_height: Math.round(updated.statusbarHeight)
      });
    } catch (error) {
      console.error('保存布局配置到服务器失败:', error);
    }
    
    return true;
  }, [config]);

  return {
    config,
    isLoading,
    saveConfig,
    reloadConfig: loadConfig
  };
}
