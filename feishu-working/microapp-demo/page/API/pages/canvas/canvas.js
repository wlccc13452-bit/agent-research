var example = require('./example.js')

Page({
  onLoad: function (e) {
    this.context = tt.createCanvasContext('ttcanvas');
    var methods = Object.keys(example)
    this.setData({
      methods: methods
    })
    methods.forEach((method) => {
      this[method] = function () {
        example[method](this.context)
        this.context.draw(); //绘图
      }
    })
  },
  toTempFilePath: function (e) {
    tt.canvasToTempFilePath({
      canvasId: 'ttcanvas',
      success: res => {
        console.log(JSON.stringify(res))
      },
      fail: res => {
        console.log(JSON.stringify(res))
      }
    })
  }
})
