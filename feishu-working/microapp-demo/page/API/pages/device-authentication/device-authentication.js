import i18n from "../../../i18n/index";
const iDeviceAuth = i18n.device_authentication;

Page({
  data: {
    ...iDeviceAuth,
  },
  startDeviceCredential: function () {
    tt.startDeviceCredential({
      authContent: iDeviceAuth.unlock_interface,
      success: (res) => {
        console.log(JSON.stringify(res));
        tt.showToast({
          title: iDeviceAuth.unlock_success,
          icon: "none",
          duration: 1500,
        });
      },
      fail: function (e) {
        tt.showModal({
          title: iDeviceAuth.unlock_fail,
          content: JSON.stringify(e),
          showCancel: true,
          cancelText: iDeviceAuth.cancel,
          cancelColor: "#000000",
          confirmText: iDeviceAuth.confirm,
          confirmColor: "#3CC51F",
        });
      },
    });
  },
  acquireFaceImage() {
    tt.acquireFaceImage({
      cameraDevice: "front",
      success(res) {
        tt.showModal({
          title: 'acquireFaceImage success',
          content: JSON.stringify(res)
        })
      },
      fail(res) {
        tt.showModal({
          title: 'acquireFaceImage error',
          content: JSON.stringify(res)
        })
      },
    });
  },
});
