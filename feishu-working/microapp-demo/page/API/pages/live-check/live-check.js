import i18n from '../../../i18n/index'
const iLiveCheck = i18n.live_check

Page({
  data: {
    uid: 'ou_87ef315c7591034c8f9447f96bfd89ff'
  },
  uidInput: function(e) {
    this.setData({
        uid: e.detail.value
    })
  },
  startFaceVerify: function () {
    let that = this;
    tt.startFaceVerify({
      userId: that.data.uid,
      success: (res) => {
        console.log(res)
          tt.showModal({
          title: 'startFaceVerify',
          content: JSON.stringify(res),
          showCancel: true,
          cancelText: 'Cancel',
          cancelColor: '#000000',
          confirmText: 'Confirm',
          confirmColor: '#3CC51F'
        });
      },
      fail: (res) => {
        console.log(res)
          tt.showModal({ 
          title: 'startFaceVerify',
          content: JSON.stringify(res),
          showCancel: true,
          cancelText: 'Cancel',
          cancelColor: '#000000',
          confirmText: 'Confirm',
          confirmColor: '#3CC51F'
        });
      }
    })
  }
})
