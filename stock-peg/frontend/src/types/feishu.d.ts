/**
 * 飞书 JSSDK 类型定义
 * 文档：https://open.larksuite.com/document/client-docs/h5/h5-overview
 */

interface LarkConfigParams {
  /** 应用 ID */
  appId: string;
  /** 时间戳 */
  timestamp: number;
  /** 随机字符串 */
  nonceStr: string;
  /** 签名 */
  signature: string;
  /** 需要使用的 JSAPI 列表 */
  jsApiList?: string[];
  /** 成功回调 */
  onSuccess?: (res: any) => void;
  /** 失败回调 */
  onFail?: (res: any) => void;
}

interface LarkConfigResponse {
  /** 是否成功 */
  success: boolean;
  /** 错误信息 */
  errorMsg?: string;
}

interface LarkCloseWindowParams {
  /** 成功回调 */
  onSuccess?: () => void;
  /** 失败回调 */
  onFail?: (error: any) => void;
}

interface LarkSDK {
  /**
   * 鉴权初始化
   * @param params 鉴权参数
   */
  config(params: LarkConfigParams): Promise<LarkConfigResponse>;
  
  /**
   * 关闭当前网页窗口
   * @param params 关闭参数
   */
  closeWindow(params?: LarkCloseWindowParams): void;
  
  /**
   * 其他 JSAPI 方法
   */
  [key: string]: any;
}

declare global {
  interface Window {
    /** 飞书 JSSDK 实例 */
    lark?: LarkSDK;
    /** 飞书 JSSDK 初始化回调 */
    larkready?: () => void;
  }
}

export {};
