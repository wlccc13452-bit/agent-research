import i18n from '../../../i18n/index'
const iLabel = i18n.label

Page({
  data: {
    checkboxItems: [
      {name: 'apple', value: 'apple'},
      {name: 'peal', value: 'peal', checked: 'true'}
    ],
    radioItems: [
      {name: 'apple', value: 'apple'},
      {name: 'peal', value: 'peal', checked: 'true'}
    ],
    hidden: false,
    ...iLabel
  },
  checkboxChange: function (e) {
    var checked = e.detail.value
    var changed = {}
    for (var i = 0; i < this.data.checkboxItems.length; i++) {
      if (checked.indexOf(this.data.checkboxItems[i].name) !== -1) {
        changed['checkboxItems[' + i + '].checked'] = true
      } else {
        changed['checkboxItems[' + i + '].checked'] = false
      }
    }
    this.setData(changed)
  },
  radioChange: function (e) {
    var checked = e.detail.value
    var changed = {}
    for (var i = 0; i < this.data.radioItems.length; i ++) {
      if (checked.indexOf(this.data.radioItems[i].name) !== -1) {
        changed['radioItems[' + i + '].checked'] = true
      } else {
        changed['radioItems[' + i + '].checked'] = false
      }
    }
    this.setData(changed)
  },
  tapEvent: function (e) {
    console.log('button clicked')
  }
})
