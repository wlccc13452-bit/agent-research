import i18n from '../../../i18n/index'
const iRequest = i18n.request

const duration = 2000

Page({
  data: {
    ...iRequest
  },
  makeRequest: function() {
    var self = this

    self.setData({
      loading: true
    })

    tt.request({
      url: 'https://www.toutiao.com',
      data: {
        noncestr: Date.now()
      },
      success: function(result) {
        tt.showToast({
          title: 'request success',
          icon: 'success',
          mask: true,
          duration: duration
        })
        self.setData({
          loading: false
        })
        console.log('request success', result)
      },

      fail: function({errMsg}) {
        console.log('request fail', errMsg)
        self.setData({
          loading: false
        })
      }, complete (res) {
        console.log("complete:"+res)
      }
    })
  }
})
