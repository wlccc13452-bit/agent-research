Page({
  checkSession: function () {
    tt.checkSession({
      success: res => {
        console.log(JSON.stringify(res))
        tt.showModal({
          title: 'success',
        })
      },
      fail: res => {
        console.log(JSON.stringify(res))
        tt.showModal({
          title: 'fail',
        })
      }
    })
  }
})
