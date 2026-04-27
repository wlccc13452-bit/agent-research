import i18n from '../../../i18n/index'
const navigator = i18n.navigator

Page({
  data: {
    ...navigator
  },
  onLoad: function(options) {
    console.log(options)
    this.setData({
      title: options.title
    })
  }
})
