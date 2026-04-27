import i18n from '../../../i18n/index'
const input = i18n.input

Page({
  data: {
    focus: false,
    inputValue: '',
    ...input
  },
  bindKeyInput: function (e) {
    this.setData({
      inputValue: e.detail.value
    })
  },
  bindReplaceInput: function (e) {
    var value = e.detail.value
    var pos = e.detail.cursor
    var left
    if (pos !== -1) {
      // coordinate is here
      left = e.detail.value.slice(0, pos)
      // calculate the coordinate
      pos = left.replace(/11/g, '2').length
    }

    // return the object, you can filter the input data, and control the position.
    return {
      value: value.replace(/11/g, '2'),
      cursor: pos
    }

    // return the string, and the mouse is on the right
    // return value.replace(/11/g,'2'),
  },
  bindHideKeyboard: function (e) {
    if (e.detail.value === '123') {
      // hide the keyboard
      tt.hideKeyboard()
    }
  }
})
