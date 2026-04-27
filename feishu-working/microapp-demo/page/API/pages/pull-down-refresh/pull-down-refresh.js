import i18n from '../../../i18n/index'
const iPullDownRefresh = i18n.pull_down_refresh

Page({
  data: {
    ...iPullDownRefresh
  },
  onPullDownRefresh: function () {
    tt.showToast({
      title: 'loading...',
      icon: 'loading'
    })
    console.log('onPullDownRefresh', new Date())
  },

  startPullDownRefresh: function () {
    tt.startPullDownRefresh({
      success(res) {
        tt.showToast({
          title: 'loading...',
          icon: 'loading'
        })
        console.log(`startPullDownRefresh调用成功`);
      },
      fail(res) {
        console.log(`startPullDownRefresh调用失败`);
      }
    });
  },

  stopPullDownRefresh: function () {
    tt.stopPullDownRefresh({
      complete: function (res) {
        tt.hideToast()
        console.log(res, new Date())
      }
    })
  },

  disablePullDownRefresh: function () {
    tt.disablePullDownRefresh();
    tt.showToast({
      title: 'disable pull',
    })
  },

  enablePullDownRefresh: function () {
    tt.enablePullDownRefresh();
    tt.showToast({
      title: 'enable pull',
    })
  }
  
})
