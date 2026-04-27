import i18n from '../../../i18n/index'
const iOnNetworkStatusChange = i18n.on_network_status_change

Page({
  data: {
    isConnected: false,
    ...iOnNetworkStatusChange
  },
  onLoad() {
    const that = this
    tt.onNetworkStatusChange(function (res) {
      that.setData({
        isConnected: res.isConnected,
        networkType: res.networkType
      })
    })
  },
  onShow() {
    const that = this
    tt.getNetworkType({
      success(res) {
        that.setData({
          isConnected: res.networkType !== 'none',
          networkType: res.networkType
        })
      }
    })
  }
})