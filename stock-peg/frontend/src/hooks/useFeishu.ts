import { useState, useEffect, useCallback } from 'react';

/**
 * 飞书 JSSDK Hook
 * 
 * 功能：
 * - 自动判断是否在飞书环境下运行
 * - 动态加载飞书 JSSDK
 * - 提供鉴权初始化方法
 * - 提供关闭窗口方法
 */
export function useFeishu() {
  const [isFeishuEnv, setIsFeishuEnv] = useState(false);
  const [isSDKReady, setIsSDKReady] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // 检测是否在飞书环境
  useEffect(() => {
    const checkFeishuEnv = () => {
      const ua = navigator.userAgent.toLowerCase();
      const isFeishu = ua.includes('lark') || ua.includes('feishu');
      setIsFeishuEnv(isFeishu);
      return isFeishu;
    };

    // 加载飞书 JSSDK
    const loadSDK = (): Promise<void> => {
      return new Promise((resolve, reject) => {
        // 如果已经加载过
        if (window.lark) {
          setIsSDKReady(true);
          resolve();
          return;
        }

        // 动态创建 script 标签
        const script = document.createElement('script');
        script.src = 'https://open.larksuite.com/open/apis/jssdk/lark/h5_sdk.js';
        script.async = true;
        
        script.onload = () => {
          // 等待 larkready 回调
          window.larkready = () => {
            setIsSDKReady(true);
            resolve();
          };
          
          // 如果 lark 对象已经存在，直接标记为就绪
          if (window.lark) {
            setIsSDKReady(true);
            resolve();
          }
        };

        script.onerror = () => {
          reject(new Error('Failed to load Feishu JSSDK'));
        };

        document.head.appendChild(script);
      });
    };

    const init = async () => {
      const isFeishu = checkFeishuEnv();
      
      if (isFeishu) {
        try {
          await loadSDK();
        } catch (error) {
          console.error('Failed to load Feishu JSSDK:', error);
        }
      }
      
      setIsLoading(false);
    };

    init();
  }, []);

  /**
   * 鉴权初始化
   * @param params 鉴权参数
   */
  const config = useCallback(async (params: {
    appId: string;
    timestamp: number;
    nonceStr: string;
    signature: string;
    jsApiList?: string[];
  }) => {
    if (!isFeishuEnv) {
      console.warn('Not in Feishu environment');
      return { success: false, errorMsg: 'Not in Feishu environment' };
    }

    if (!window.lark) {
      console.error('Feishu JSSDK not loaded');
      return { success: false, errorMsg: 'Feishu JSSDK not loaded' };
    }

    return new Promise<{ success: boolean; errorMsg?: string }>((resolve) => {
      window.lark!.config({
        ...params,
        onSuccess: (res: any) => {
          console.log('Feishu config success:', res);
          resolve({ success: true });
        },
        onFail: (res: any) => {
          console.error('Feishu config failed:', res);
          resolve({ success: false, errorMsg: res?.errorMsg || 'Config failed' });
        }
      });
    });
  }, [isFeishuEnv]);

  /**
   * 关闭当前网页窗口
   */
  const closeWindow = useCallback(() => {
    if (!isFeishuEnv) {
      console.warn('Not in Feishu environment');
      return;
    }

    if (!window.lark) {
      console.error('Feishu JSSDK not loaded');
      return;
    }

    window.lark.closeWindow({
      onSuccess: () => {
        console.log('Window closed successfully');
      },
      onFail: (error: any) => {
        console.error('Failed to close window:', error);
      }
    });
  }, [isFeishuEnv]);

  return {
    /** 是否在飞书环境下运行 */
    isFeishuEnv,
    /** SDK 是否加载完成 */
    isSDKReady,
    /** 是否正在加载 */
    isLoading,
    /** 鉴权初始化方法 */
    config,
    /** 关闭窗口方法 */
    closeWindow
  };
}
