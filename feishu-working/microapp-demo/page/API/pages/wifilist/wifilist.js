Page({
  data: {
    wifiStatus: "",
    listenWifiList: false,
    listenlabel: "开始监听",
    wifiList: []
  },

  onShow: function(){
    let that = this
    tt.getWifiStatus({
      success: res => {
        console.log("hahahahah", res)
         that.setData({
           wifiStatus: res.status
         })
      },
      fail: res => {
         that.setData({
           wifiStatus: res
         })
      }
    })
  },
  callback: function(res){
    console.log(res)
     this.setData({
       wifiList: res.wifiList
     })
  },
  
  listen: function() {
    var that = this
    if(this.data.listenWifiList){
      tt.offGetWifiList(that.callback)
      that.setData({
          listenWifiList: false,
          listenlabel: "开始监听"
      })
    }else{
      tt.onGetWifiList(that.callback)
      that.setData({
          listenWifiList: true,
          listenlabel: "取消监听"
      })
    }
  },

  getWifiList: function () {
    tt.getWifiList()
  },
})
