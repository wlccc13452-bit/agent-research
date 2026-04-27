import i18n from '../../../i18n/index'
const igetLocation = i18n.get_location

var util = require('../../../../util/util.js')
var formatLocation = util.formatLocation

Page({
  data: {
    hasLocation: false,
    ...igetLocation
  },
  getLocation: function () {
    var that = this
    tt.getLocation({
      type: 'gcj02',
      timeout: 3,
      cacheTimeout: 60,
      success: function (res) {
        console.log(res)
        that.setData({
          hasLocation: true,
          location: formatLocation(res.longitude, res.latitude)
        })
      },
      fail: res => {
        console.log(JSON.stringify(res))
      }
    })
  },
  clear: function () {
    this.setData({
      hasLocation: false
    })
  }
  
})
