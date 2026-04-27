import i18n from '../../../i18n/index'
const iMakePhoneCall = i18n.make_phone_call

Page({
  data: {
    disabled: true,
    ...iMakePhoneCall
  },
  bindInput: function (e) {
    this.inputValue = e.detail.value
    this.setData({
      disabled: this.inputValue.length <= 0
    })
  },
  makePhoneCall: function (e) {
    tt.makePhoneCall({
      phoneNumber: this.inputValue,
      success: res => {
        console.log(JSON.stringify(res))
      },
      fail: res => {
        onsole.log(JSON.stringify(res))
      }
    })
  }
})