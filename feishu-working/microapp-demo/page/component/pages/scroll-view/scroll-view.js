import i18n from '../../../i18n/index'
const iScrollView = i18n.scroll_view

var order = ['demo1', 'demo2', 'demo3']
Page({
  data: {
    toView: 'demo1',
    scrollTop: 0,
    ...iScrollView
  },
  upper: function(e) {
    console.log(e)
  },
  lower: function(e) {
    console.log(e)
  },
  scroll: function(e) {
    console.log(e)
  },
  tap: function(e) {
    for (var i = 0; i < order.length; ++i) {
      if (order[i] === this.data.toView) {
        this.setData({
          toView: order[i < order.length - 1 ? i + 1 : 0],
        })
        break
      }
    }
  },
  tapMove: function(e) {
    this.setData({
      scrollTop: this.data.scrollTop + 20
    })
  }
})