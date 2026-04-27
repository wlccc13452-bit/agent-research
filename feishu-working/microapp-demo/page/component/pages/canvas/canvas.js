import i18n from '../../../i18n/index'
const canvas = i18n.canvas

Page({
  data :{
    ...canvas
  },
  onShow: function (res) {
    this.position = {
      x: 150,
      y: 150,
      vx: 2,
      vy: 2
    }
    this.interval = setInterval(this.drawBall, 17)
  },
  drawBall: function () {
    var p = this.position
    p.x += p.vx
    p.y += p.vy
    if (p.x >= 300) {
      p.vx = -2
    }
    if (p.x <= 7) {
      p.vx = 2
    }
    if (p.y >= 300) {
      p.vy = -2
    }
    if (p.y <= 7) {
      p.vy = 2
    }

    var context = tt.createCanvasContext('canvas')

    function ball(x, y) {
      context.beginPath(0)
      context.arc(x, y, 5, 0, Math.PI * 2)
      context.setFillStyle('#1aad19')
      context.fill()
      context.stroke()
    }

    ball(p.x, 150)
    ball(150, p.y)
    ball(300 - p.x, 150)
    ball(150, 300 - p.y)
    ball(p.x, p.y)
    ball(300 - p.x, 300 - p.y)
    ball(p.x, 300 - p.y)
    ball(300 - p.x, p.y)

    //console.log('will call context.draw');
    context.draw();
  },
  onUnload: function () {
    clearInterval(this.interval)
  }, exportImage: function () {
    tt.canvasToTempFilePath({
      canvasId: 'canvas',
      fileType: "jpg",
      x: 100,
      y: 200,
      width: 100,
      height: 200,
      destWidth: 300,
      destHeight: 400,
      quality: 1,
      success: function (res) {
        console.log(" canvasToTempFilePath success")
        console.log(res.tempFilePath)
        tt.showToast({
          title: "success"
        })
      }, fail: function () {
        console.log(" canvasToTempFilePath fail")
      }

    })
  }
})

