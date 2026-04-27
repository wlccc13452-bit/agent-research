import i18n from '../../../i18n/index'
const iScanCode = i18n.scan_code

var scanType = [['barCode'], ['qrCode'], ['barCode', 'qrCode', 'datamatrix','pdf417']]
Page({
  data: {
    result: '',
    ...iScanCode
  },
  scanCode: function () {
    
    var that = this
    tt.scanCode({
      scanType:scanType[2],
      barCodeInput: true,
      success: function (res) {
        console.log(JSON.stringify(res));
        that.setData({
          result: res.result
        })
      },
      fail: function (res) {
        console.log(JSON.stringify(res));
      }
    })
  }
})
