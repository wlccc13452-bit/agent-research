import i18n from '../../../i18n/index'
const iNavigatorApi = i18n.navigator_api

Page({
  data: {
    now: Date.now(),
    ...iNavigatorApi
  },
  onShow () {
    this.setData({
      now: Date.now()
    })
  },
  onLoad (par) {
    console.log('par', par)
  },
  navigateTo: function () {
    tt.navigateTo({ url: './navigator' })
  },
  navigateBack: function () {
    tt.navigateBack()
  },
  redirectTo: function () {
    tt.redirectTo({ url: './navigator' })
  },
  reLaunch () {
    tt.reLaunch({
      url: './navigator',
      success: function(res) {},
      fail: function(res) {},
      complete: function(res) {},
    })
  },
  switchTab() {
    tt.switchTab({
      url: '/page/API/index',
      success: function(res) {},
      fail: function(res) {},
      complete: function(res) {},
    })
  },
  exitMiniProgram() {
    tt.exitMiniProgram()
  }
})
