import i18n from '../../../i18n/index'
const iTextarea = i18n.textarea

Page({
  data: {
    focus: false,
    ...iTextarea
  },
  bindTextAreaBlur: function(e) {
    console.log(e.detail.value)
  }
})
