import i18n from '../../../i18n/index'
const form = i18n.form

const contentBehavior = require('../../common/component/Content/content-behavior')

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
    pickerHidden: true,
    chosen: '',
    ...form
  },
  methods: {
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
  }
})