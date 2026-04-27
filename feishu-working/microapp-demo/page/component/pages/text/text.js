import i18n from '../../../i18n/index'
const iText = i18n.text

var texts = [
  'line 1',
  'line 2',
  'line 3',
  'line 4',
  'line 5'
];

Page({
  data: {
    text: '',
    canAdd: true,
    canRemove: false,
    ...iText
  },
  onShow(args) {
    console.log('page---onShow')
    console.log(args)
    console.log('-------------')
  },
  onLoad(args) {
    console.log('page---onLoad')
    console.log(args)
    console.log('-------------')
  },
  extraLine: [],
  add: function (e) {
    var that = this;
    this.extraLine.push(texts[this.extraLine.length % 12])
    this.setData({
      text: this.extraLine.join('\n'),
      canAdd: this.extraLine.length < 12,
      canRemove: this.extraLine.length > 0
    })
    setTimeout(function () {
      that.setData({
        scrollTop: 99999
      });
    }, 0)
  },
  remove: function (e) {
    var that = this;
    if (this.extraLine.length > 0) {
      this.extraLine.pop()
      this.setData({
        text: this.extraLine.join('\n'),
        canAdd: this.extraLine.length < 12,
        canRemove: this.extraLine.length > 0,
      })
    }
    setTimeout(function () {
      that.setData({
        scrollTop: 99999
      });
    }, 0)
  }
})
