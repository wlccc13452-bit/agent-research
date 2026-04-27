import i18n from '../../../i18n/index'
const igetNetworkType = i18n.get_network_type

Page({
  data: {
    hasNetworkType: false,
    ...igetNetworkType
  },
  getNetworkType: function () {
    tt.getNetworkType({
      success: res => {
        console.log(JSON.stringify(res))
        this.setData({
          hasNetworkType: true,
          networkType: res.subtype || res.networkType
        })
        tt.showToast({
          title: `${res.networkType}`,
          success: res => {
            console.log(JSON.stringify(res));
          },
          fail: res => {
            console.log(JSON.stringify(res));
          }
        });
      },
      fail: res => {
        console.log(JSON.stringify(res))
      }
    })
  },
  clear: function () {
    this.setData({
      hasNetworkType: false,
      networkType: ''
    })
  },
  onShow() {
    tt.onNetworkStatusChange(({ isConnected, networkType }) => {
      if (isConnected) {
        tt.hideLoading();
        tt.showToast({
          title: `${networkType}`,
          success: res => {
            console.log(JSON.stringify(res));
          },
          fail: res => {
            console.log(JSON.stringify(res));
          }
        })
      } else {
        tt.showLoading({
          title: 'please connect network.',
          success: res => {
            console.log(JSON.stringify(res));
          },
          fail: res => {
            console.log(JSON.stringify(res));
          }
        });
      }
    });
  }
})
