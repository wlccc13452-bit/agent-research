import i18n from '../../../i18n/index'
const iClipboard = i18n.get_clipboard_data

Page({
  data: {
    value: 'edit and copy me',
    pasted: '',
    ...iClipboard
  },

  valueChanged(e) {
    this.setData({
      value: e.detail.value
    })
  },

  copy() {
    tt.setClipboardData({
      data: this.data.value,
      success() {
        tt.showToast({
          title: 'Copy Success',
          icon: 'success',
          duration: 1000
        })
      }
    })
  },

  paste() {
    const self = this
    tt.getClipboardData({
      success(res) {
        self.setData({
          pasted: res.data
        })
        tt.showToast({
          title: 'Paste Success',
          icon: 'success',
          duration: 1000
        })
      }
    })
  }
})
