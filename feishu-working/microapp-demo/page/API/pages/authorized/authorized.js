Page({
  authorize: function() {
    tt.authorize({
      scope: 'scope.userInfo',
      success () {
        console.log('grand permission')
        tt.showToast({
         title: 'grand permission scope.userInfo',
         icon: 'none',
         duration: 1500
        });
      },
      fail () {
        console.log('grand deny')
        tt.showToast({
         title: 'grand deny scope.userInfo',
         icon: 'none',
         duration: 1500
        });
      }
    })
  },
  openSetting: () => {
    tt.openSetting({
      success (res) {
        console.log(res.authSetting)
      }
    })
  },
  getSetting: () => {
    tt.getSetting({
      success (res) {
        tt.showModal({
          title: 'getSetting',
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