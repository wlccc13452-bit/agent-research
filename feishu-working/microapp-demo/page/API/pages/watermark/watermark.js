import i18n from '../../../i18n/index'
const iWatermark = i18n.watermark

Page({
  data: {
    ...iWatermark
  },
  checkWatermark: function () {
    tt.checkWatermark({
      success: (res) => {
        console.log(res)
        const title = 'did app show watemark?：' + ((res.hasWatermark == true) ? '是' : '否')
        console.log(title)
        tt.showToast({
          title: title,
          icon: 'none'
        })
      },
      fail: (res) => {
        console.log(res)
      }
    })
  }
})