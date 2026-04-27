import i18n from '../../../i18n/index'
const iGetSystemInfo = i18n.get_system_info

Page({
  data: {
    systemInfo: {},
    ...iGetSystemInfo
  },
  getSystemInfo: function () {
    var that = this
    tt.getSystemInfo({
      success: function (res) {
				console.log(res);

        that.setData({
          systemInfo: res
        })
      }
    })
  },
  clear () {
    this.setData({
      systemInfo: {}
    })
  },
  getSystemInfoSync() {
    try {
      var res = tt.getSystemInfoSync()
      console.log(res);

      this.setData({
        systemInfo: res
      });
    } catch (e) {
      console.error(e);
    }
  }
})
