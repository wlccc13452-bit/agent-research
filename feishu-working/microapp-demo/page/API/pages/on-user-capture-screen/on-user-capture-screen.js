import i18n from '../../../i18n/index'
const iOnUseCaptureScreen = i18n.on_use_capture_screen

Page({
  data: {
    result: iOnUseCaptureScreen.no_triggered,
    ...iOnUseCaptureScreen
  },
  onLoad() {
    tt.onUserCaptureScreen(this.onUserCaptureScreenCallback);
  },
  offObserver() {
    tt.offUserCaptureScreen(this.onUserCaptureScreenCallback);
    this.setData({
      result: iOnUseCaptureScreen.has_cancel
    });
  },
  onUserCaptureScreenCallback: function(res) {
    this.setData({
      result: iOnUseCaptureScreen.has_triggered
    });
  }
});
