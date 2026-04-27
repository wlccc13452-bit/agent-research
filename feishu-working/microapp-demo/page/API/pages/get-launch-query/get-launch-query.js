Page({
  data: {
    launchQuery: '',
  },
  getHostLaunchQuery: function () {
    var that = this
    console.log("start getHostLaunchQuery")
    tt.getHostLaunchQuery({
      success: res => {
        console.log("getHostLaunchQuery success")
        that.setData({
          launchQuery: res.launchQuery 
        })
      },
      fail: res => {
        console.log("getHostLaunchQuery fail")
        that.setData({
          deviceId: JSON.stringify(res)
        })
      }
    })
  },
  getHostLaunchQuerySync: function () {
    console.log("start getHostLaunchQuerySync")
    var that = this
    try {
      var res = tt.getHostLaunchQuerySync();
      that.setData({
        launchQuery: res.launchQuery 
      })
    } catch (error) {
      console.log("getHostLaunchQuerySync fail")
    }
  }
})