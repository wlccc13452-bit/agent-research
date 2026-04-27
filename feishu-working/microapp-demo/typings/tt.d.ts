interface IAnimation {
  /**
   * opacity, value range 0~1
   */
  opacity(value: number): IAnimation;
  /**
   * background color
   */
  backgroundColor(color: string): IAnimation;
  /**
   * default px, and it can input another unit.
   */
  width(length: number): IAnimation;
  /**
   * default px, and it can input another unit.
   */
  height(length: number): IAnimation;
  /**
   * default px, and it can input another unit.
   */
  top(length: number): IAnimation;
  /**
   * default px, and it can input another unit.
   */
  left(length: number): IAnimation;
  /**
   * default px, and it can input another unit.
   */
  bottom(length: number): IAnimation;
  /**
   * default px, and it can input another unit.
   */
  right(length: number): IAnimation;
  /**
   * deg range -180~180
   */
  rotate(deg: number): IAnimation;

  rotateX(deg: number): IAnimation;

  rotateY(deg: number): IAnimation;

  rotateZ(deg: number): IAnimation;

  rotate3d(x: number, y: number, z: number, deg: number): IAnimation;

  scale(sx: number, sy?: number): IAnimation;

  scaleX(sx: number): IAnimation;

  scaleY(sy: number): IAnimation;

  scaleZ(sz: number): IAnimation;

  scale3d(sx: number, sy: number, sz: number): IAnimation;

  translate(tx: number, ty?: number): IAnimation;

  translateX(tx: number): IAnimation;

  translateY(tx: number): IAnimation;

  translateZ(tx: number): IAnimation;

  translate3d(tx: number, ty: number, tz: number): IAnimation;

  skew(ax: number, ay?: number): IAnimation;

  skewX(ax: number): IAnimation;

  skewY(ay: number): IAnimation;

  matrix(a, b, c, d, tx, ty): IAnimation;

  matrix3d(): IAnimation;
}

interface ICanvasContext {
  setFillStyle(color: string): void;

  setStrokeStyle(color: string): void;

  setShadow(offsetX: number, offsetY: number, blur: number, color: string): void;

  addColorStop(stop: number, color: string): void;

  setLineCap(lineCap: 'butt' | 'round' | 'square'): void;

  setLineJoin(lineJoin: 'bevel' | 'round' | 'miter'): void;

  setLineWidth(lineWidth: number): void;

  setMiterLimit(miterLimit: number): void;

  rect(x: number, y: number, width: number, height: number): void;

  fillRect(x: number, y: number, width: number, height: number): void;

  strokeRect(x: number, y: number, width: number, height: number): void;

  clearRect(x: number, y: number, width: number, height: number): void;

  fill(): void;

  stroke(): void;

  beginPath(): void;

  closePath(): void;

  moveTo(x: number, y: number): void;

  lineTo(x: number, y: number): void;

  arc(x: number, y: number, radius: number, startAngle: number, sweepAngle: number): void;

  quadraticCurveTo(cpx: number, cpy: number, x: number, y: number): void;

  bezierCurveTo(cpx1: number, cpy1: number, cpx2: number, cpy2: number, x: number, y: number): void;

  scale(scaleWidth: number, scaleHeight: number): void;

  rotate(deg: number): void;

  translate(x: number, y: number): void;

  fillText(text: string, x: number, y: number): void;

  setFontSize(fontSize: number): void;

  drawImage(imageResource: string, x: number, y: number, width: number, height: number): void;

  setGlobalAlpha(alpha: number): void;

  save(): void;

  restore(): void;

  draw(): void;
}

class IAudioContext {
  play: () => void;

  pause: () => void;

  stop: () => void;

  seek: (position: number) => void;

  autoplay: boolean;

  src: string;

  onPlay: () => void;
}

interface Application {
  setData: (obj: any) => void;
}

interface AppConstructor {
  new (): Application;
  (opts: {
    /**
     * Lifecycle function – listener applet initialization
     * OnLaunch (trigger only once) is triggered when the applet initialization is complete.
     */
    onLaunch?: () => void;
    /**
     * Life cycle function - monitor applet display
     */
    onShow?: () => void;
    /**
     * Lifecycle function--listening applet hiding
     */
    onHide?: () => void;

    /**
     * When a minor program has a script error, or the API call fails, onError is raised with an error message.
     */
    onError?: () => void;

    /**
     * When the applet appears to open the page does not exist, it will bring the page information callback function
     */
    onPageNotFound?: () => void;

    [key: string]: any;
  }): Application;
}

declare var App: AppConstructor;
declare function getApp(): Application;

declare function getCurrentPages(): Page[];

interface Page {
  setData: (obj: any) => void;
}

interface PageConstructor {
  new (): Page;
  (opts: {
    data?: any;
    /**
     * Initial data of the page
     */
    onLoad?: () => void;
    /**
     * Lifecycle function - the first time the listener page is rendered
     */
    onReady?: () => void;
    /**
     * Lifecycle function - monitor page display
     */
    onShow?: () => void;
    /**
     * Lifecycle function--listening page hiding
     */
    onHide?: () => void;
    /**
     * Lifecycle function--listening page unloading
     */
    onUnload?: () => void;
    /**
     * Page related event handler - listener user pulldown
     */
    onPullDownRefreash?: () => void;
    /**
     * The handler for pulling the bottom event on the page
     */
    onReachBottom?: () => void;
    /**
     * User clicks on the top right corner to share
     */
    onShareAppMessage?: () => {
      title: string;
      imageUrl: string;
      path: string;
    };

    /**
     * The processing function of the page scrolling trigger event
     */
    onPageScroll?: () => void;

    /**
     * When the tab page is currently tabped, it is triggered when the tab is clicked
     */
    onTabItemTap?: (item: { index: number; pagePath: string; text: string }) => void;

    /**
     * When the tab page is currently tabped, it is triggered when you double-click the tab
     */
    onTabbarDoubleTap?: (item: { index: number; pagePath: string; text: string }) => void;

    viewTap?: () => void;

    [key: string]: any;
  }): Page;
}

declare var Page: PageConstructor;

interface IRequest {
  abort?: () => void;
}

interface IWebSocket {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: () => void;
  onMessage?: () => void;
}

interface IProgressTask {
  onProgressUpdate?: (callback: Function) => void;
}

class IStorageInfo {
  keys: number[];

  currentSize: number;

  limitSize: number;
}

interface IRecorderManager {
  start?: (option: {
    duration: number;
    sampleRate: number;
    numberOfChannels: number;
    encodeBitRate: number;
    format: string;
    frameSize: number;
  }) => void;
  pause?: () => void;
  resume?: () => void;
  stop?: () => void;
  onStart?: (callback: Function) => void;
  onPause?: (callback: Function) => void;
  onStop?: (callback: Function) => void;
  onFrameRecorded?: (callback: Function) => void;
  onError?: (callback: Function) => void;
}

class ISystemInfo {
  system: string;

  platform: string;

  brand: string;

  model: string;

  version: string;

  SDKVersion: string;

  screenWidth: number;

  screenHeight: number;

  windowWidth: number;

  windowHeight: number;

  pixelRatio: number;

  statusBarHeight: number;

  language: string;

  fontSizeSetting: number;

  appName: string;
}

class UserInfo {
  nickName: string;

  avatarUrl: string;

  gender: number;

  country: string;

  province: string;

  city: string;

  language: string;
}

class AuthSetting {}

class ContactInfo {
  openId: string;

  name: string;
}

class ChatInfo {
  id: string;

  chatType: string;
}

interface UpdateManager {
  applyUpdate?: () => void;
  onCheckForUpdate?: (callback: (res: { hasUpdate: boolean }) => void) => void;
  onUpdateFailed?: Function;
  onUpdateReady?: Function;
}

class BoundingClientRect {
  id: string;

  dataset: any;

  left: number;

  right: number;

  top: number;

  bottom: number;

  width: number;

  height: number;
}

class ScrollOffset {
  id: string;

  dataset: any;

  scrollLeft: number;

  scrollTop: number;
}

interface NodesRef {
  boundingClientRect: (callback: (res: BoundingClientRect) => void) => void;
  scrollOffset: (callback: (res: ScrollOffset) => void) => void;
}

class SelectorQuery {
  in: SelectorQuery;

  select: NodesRef;

  selectAll: NodesRef;

  selectViewport: () => NodesRef;

  exec: () => void;
}

interface TTIntersectionObserver {
  relativeTo: () => void;
  relativeToViewport: () => void;
  observe: () => void;
  disconnect: () => void;
}

declare var tt: {
  getUpdateManager(): UpdateManager;

  createSelectorQuery(): SelectorQuery;

  createIntersectionObserver(): TTIntersectionObserver;

  request(obj: {
    /**
     * developer server address
     */
    url: string;
    /**
     * request data
     */
    data?: any | string;
    /**
     * request header, but not contain referer
     */
    header?: any;
    /**
     * Default GET，Such as：OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, CONNECT
     */
    method?: string;
    /**
     * Default json
     */
    dataType?: string;
    /**
     * success callback
     */
    success?: Function;
    /**
     * fail callback
     */
    fail?: Function;
  }): IRequest;

  uploadFile(obj: {
    url: string;
    /**
     * file path which should upload
     */
    filePath: string;

    name: string;

    header?: any;

    formData?: any;

    success?: Function;

    fail?: Function;
  }): IProgressTask;

  downloadFile(obj: {
    url: string;

    header?: any;

    success?: Function;

    fail?: Function;

    complete?: Function;
  }): IProgressTask;

  connectSocket(obj: {
    url: string;
    /**
     * HTTP Header
     */
    header?: any;

    protocols?: string[];
  }): IWebSocket;

  chooseImage(obj: {
    count?: number;

    cameraDevice?: string;

    sourceType?: string[];

    success: Function;

    fail?: Function;
  }): void;

  previewImage(obj: { urls: string[]; current?: string; header?: any }): void;

  getImageInfo(obj: {
    src: string;

    success?: Function;

    fail?: Function;
  }): void;

  saveImageToPhotosAlbum(obj: {
    filePath: string;

    success?: Function;

    fail?: Function;
  }): void;

  compressImage(obj: { src?: string; quality?: number }): void;

  startRecord(obj: {
    success?: Function;

    fail?: Function;
  }): void;

  createInnerAudioContext(audioId: string): IAudioContext;

  chooseVideo(obj: {
    sourceType?: string[];

    maxDuration?: number;

    success?: Function;

    fail?: Function;
  }): void;

  saveVideoToPhotosAlbum(obj: {
    filePath: string;

    success?: Function;

    fail?: Function;
  }): void;

  getRecorderManager(): IRecorderManager;

  saveFile(obj: {
    tempFilePath: string;

    success?: Function;

    fail?: Function;
  }): void;

  openDocument(obj: {
    filePath: string;

    fileType?: string;

    success?: Function;

    fail?: Function;
  }): void;

  setStorage(obj: {
    key: string;

    data: any;

    success?: Function;

    fail?: Function;
  }): void;

  setStorageSync(key: string, data: any): void;

  getStorage(obj: {
    key: string;

    success: Function;

    fail?: Function;
  }): void;

  getStorageSync(key: string): void;

  getStorageInfo(obj: {
    success: Function;

    fail?: Function;
  }): void;

  getStorageInfoSync(): IStorageInfo;

  removeStorage(obj: {
    key: string;

    fail?: Function;
  }): void;

  removeStorageSync(key: string): void;

  clearStorage(): void;

  clearStorageSync(): void;

  getLocation(obj: {
    type?: string;

    success: Function;

    fail?: Function;
  }): void;

  chooseLocation(obj: {
    success: Function;

    cancel?: Function;

    fail?: Function;
  }): void;

  openLocation(obj: {
    latitude: number;

    longitude: number;

    scale?: number;

    name?: string;

    address?: string;

    success?: Function;

    fail?: Function;
  }): void;

  getSystemInfo(obj: { success: Function; fail?: Function }): void;

  getSystemInfoSync(): ISystemInfo;

  getNetworkType(obj: {
    success: Function;

    fail?: Function;

    complete?: Function;
  }): void;

  onNetworkStatusChange(callback: Function): void;

  vibrateLong(obj: {
    success?: Function;

    fail?: Function;
  }): void;

  vibrateShort(obj: {
    success?: Function;

    fail?: Function;
  }): void;

  onAccelerometerChange(callback: Function): void;

  startAccelerometer(obj: {
    success?: Function;

    fail?: Function;
  }): void;

  stopAccelerometer(obj: {
    success?: Function;

    fail?: Function;
  }): void;

  onCompassChange(callback: Function): void;

  startCompass(obj: {
    success?: Function;

    fail?: Function;
  }): void;

  stopCompass(obj: {
    success?: Function;

    fail?: Function;
  }): void;

  makePhoneCall(obj: {
    phoneNumber: string;

    success?: Function;

    fail?: Function;
  }): void;

  scanCode(obj: {
    onlyFromCamera?: boolean;

    success?: Function;

    fail?: Function;
  }): void;

  setClipboardData(obj: {
    data: string;

    success?: Function;

    fail?: Function;
  }): void;

  getClipboardData(obj: {
    success?: Function;

    fail?: Function;
  }): void;

  onUserCaptureScreen(callback: Function): void;

  showToast(obj: {
    title: string;

    icon?: string;

    image?: string;

    duration?: number;

    mask?: boolean;

    success?: Function;

    fail?: Function;
  }): void;

  showLoading(obj: {
    title: string;

    mask?: boolean;

    success?: Function;

    fail?: Function;

    complete?: Function;
  }): void;

  hideToast(): void;

  hideLoading(): void;

  showModal(obj: {
    title: string;

    content: string;

    showCancel?: boolean;

    cancelText?: string;

    cancelColor?: undefined;

    confirmText?: string;

    confirmColor?: undefined;

    success?: Function;

    fail?: Function;
  }): void;

  showActionSheet(obj: {
    itemList: undefined;

    itemColor?: undefined;

    success?: Function;

    fail?: Function;
  }): void;

  setNavigationBarTitle(obj: {
    title: string;

    success?: Function;

    fail?: Function;
  }): void;

  navigateTo(obj: {
    url: string;

    success?: Function;

    fail?: Function;
  }): void;

  redirectTo(obj: {
    url: string;

    success?: Function;

    fail?: Function;
  }): void;

  reLaunch(obj: {
    url: string;

    success?: Function;

    fail?: Function;
  }): void;

  /**
   *
   * Jump to the tabBar page and close all other non-tabBar pages
   */
  switchTab(obj: {
    /**
     * The path to the tabBar page that needs to be jumped (the page defined in the tabBar field of app.json ), with no arguments after the path.
     */
    url: string;

    success?: Function;

    fail?: Function;
  }): void;

  /**
   *
   * Close the current page and return to the previous or multi-level page. The current page stack can be obtained via getCurrentPages()), which determines how many layers need to be returned.
   */
  navigateBack(obj: {
    /**
     * The number of pages returned, if delta is greater than the number of existing pages, return to the first page.
     */
    delta?: number;
  }): void;

  createAnimation(obj: {
    /**
     * 400
     */
    duration?: number;
    /**
     * "linear"
     */
    timingFunction?: string;
    /**
     * 0
     */
    delay?: number;
    /**
     * "50% 50% 0"
     */
    transformOrigin?: string;
  }): IAnimation;

  pageScrollTo(obj: { scrollTop: number }): void;

  createCanvasContext(canvasId: string): ICanvasContext;

  canvasToTempFilePath(canvasId: string): void;

  startPullDownRefresh(obj: {
    success?: Function;

    fail?: Function;
  }): void;

  stopPullDownRefresh(): void;

  login(obj: {
    success?: Function;

    fail?: Function;
  }): void;

  checkSession(obj: {
    success?: Function;

    fail?: Function;
  }): void;

  authorize(obj: {
    scope: string;

    success?: Function;

    fail?: Function;
  }): void;

  getUserInfo(obj: {
    withCredentials?: boolean;

    lang?: string;

    success: (res: { userInfo: UserInfo; rawData: string }) => void;

    fail?: Function;
  }): void;

  openSetting(obj: {
    success: (authSetting: AuthSetting) => void;

    fail?: Function;
  }): void;

  getSetting(obj: {
    success: (authSetting: AuthSetting) => void;

    fail?: Function;
  }): void;

  chooseContact(obj: {
    multi?: boolean;
    ignore?: boolean;
    choosenIds?: string[];
    success: (res: { data: ContactInfo[] }) => void;
    fail?: () => void;
  }): void;

  chooseChat(obj: {
    allowCreateGroup?: boolean;
    multiSelect?: boolean;
    ignoreSelf?: boolean;
    selectType?: number;
    confirmTitle?: string;
    confirmDesc?: string;
    success: (res: { data: ChatInfo[] }) => void;
    fail?: () => void;
  }): void;

  checkWatermark(obj: { success: (res: { hasWatermark: boolean }) => void; fail?: () => void }): void;

  startPasswordVerify(obj: { success: (res: { errCode: int; token: string }) => void; fail?: () => void }): void;

  startFaceVerify(obj: { success: (res: { errCode: int; reqNo: string }) => void; fail?: () => void }): void;
};
