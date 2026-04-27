import i18n from '../../../i18n/index'
const iOpenLocation = i18n.open_location

Page({
  data: {
    ...iOpenLocation
  },
  openLocation: function(e) {
    const value = e.detail.value
    tt.openLocation({
      longitude: Number(value.longitude),
      latitude: Number(value.latitude),
      name: value.name,
      address: value.address,
      success: function (res) {
        console.log(JSON.stringify(res))
      },
      fail: res => {
        console.log(JSON.stringify(res))
      }
    })
  }
})
