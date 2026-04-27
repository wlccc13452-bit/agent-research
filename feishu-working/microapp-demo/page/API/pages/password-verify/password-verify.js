import i18n from '../../../i18n/index'
const iPasswordVerify = i18n.password_verify

Page({
  data: {
    ...iPasswordVerify
  },
  startPasswordVerify: function () {
    tt.startPasswordVerify({
      success: function (e) {
       tt.showToast({
         title: 'Verify Success',
         icon: 'none',
         duration: 1500
       });
      },
      fail: function(e) {
        tt.showModal({
          title: 'Verify Fail',
          content: JSON.stringify(e),
          showCancel: true,
          cancelText: 'Cancel',
          cancelColor: '#000000',
          confirmText: 'Confirm',
          confirmColor: '#3CC51F'
        });
      }
    });
  }
})
