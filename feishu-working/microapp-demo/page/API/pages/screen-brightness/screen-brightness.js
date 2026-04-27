import i18n from '../../../i18n/index'
const iScreenBrightness = i18n.screen_brightness

Page({
  data: {
     cl: false,
     screenBrightness: 0,
     ...iScreenBrightness
  },
  onLoad() {
    this.getScreenBrightness()
  },

  light () {
    var now = this.data.cl;
    tt.setKeepScreenOn({
      keepScreenOn: !now,
      success: () => {
        this.setData({
          cl: !now
        })
        tt.showToast({
          title: `${!now ? iScreenBrightness.constantly_bright : iScreenBrightness.light_out}`
        })
      }
    })

  },
  setScreenBrightness (e) {
    const brightnessValue = Number.parseFloat(
      e.detail.value.toFixed(1)
    )
    this.setData({
      screenBrightness: Number.parseFloat(
        e.detail.value.toFixed(1)
      )
    })
    tt.setScreenBrightness({
      value: brightnessValue,
      success: res => {
        tt.showToast({
          title: 'success ' + brightnessValue.toFixed(1)
        })
      },
      fail: error => {
        tt.showToast({
          title: 'fail'
        })
      }
    })
  },
  getScreenBrightness () {
    tt.getScreenBrightness({
      success: res => {
        this.setData({
          screenBrightness: Number.parseFloat(
            res.value.toFixed(1)
          )
        })
        tt.showToast({
          title: 'success ' + res.value.toFixed(1)
        })
      },
      fail: error => {
        tt.showToast({
          title: 'fail'
        })
      }
    })
  }
})