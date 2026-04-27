import i18n from '../../../i18n/index'
const iChooseLocation = i18n.choose_location

const util = require('../../../../util/util.js')

const formatLocation = util.formatLocation

Page({
  data: {
    hasLocation: false,
    ...iChooseLocation
  },
  chooseLocation() {
    const that = this
    tt.chooseLocation({
      success: res => {
        console.log(JSON.stringify(res))
        that.setData({
          hasLocation: true,
          location: formatLocation(res.longitude, res.latitude),
          locationAddress: res.address
        })
      },
      fail: res => {
        console.log(JSON.stringify(res))
      }
    })
  },
  clear() {
    this.setData({
      hasLocation: false
    })
  }
})
