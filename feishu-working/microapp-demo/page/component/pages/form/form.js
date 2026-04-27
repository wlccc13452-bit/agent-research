import i18n from '../../../i18n/index'
const form = i18n.form

Page({
  data: {
    pickerHidden: true,
    chosen: '',
    ...form
  },
  pickerConfirm: function (e) {
    this.setData({
      pickerHidden: true
    })
    this.setData({
      chosen: e.detail.value
    })
  },
  pickerCancel: function (e) {
    this.setData({
      pickerHidden: true
    })
  },
  pickerShow: function (e) {
    this.setData({
      pickerHidden: false
    })
  },
  formSubmit: function (e) {
    console.log('form submit，data：', e.detail.value)
  },
  formReset: function (e) {
    console.log('form reset，data：', e.detail.value)
    this.setData({
      chosen: ''
    })
  }
})
