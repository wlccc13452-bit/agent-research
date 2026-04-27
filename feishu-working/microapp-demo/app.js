App({
  onLaunch: function (args) {
    console.log('App Launch')
    console.log(args.query)
  },
  onShow: function (args) {
    console.log('App Show');
    console.log(args);
    // check the update of mini program
    let updateManager = tt.getUpdateManager();
    updateManager.onCheckForUpdate((result) => {
      console.log('is there any update?：' + result.hasUpdate);
    });
    updateManager.onUpdateReady((result) => {
      tt.showModal({
        title: 'Update infomation',
        content: 'new version is ready, do you want to restart app?',
        success: res => {
          console.log(JSON.stringify(res))
          if (res.confirm) {
            updateManager.applyUpdate();
          }
        }
      })
    });
    updateManager.onUpdateFailed((result) => {
      console.log('mini program update failed');
    });
  },
  onHide: function () {
    console.log('App Hide')
  },
  globalData: {
    hasLogin: false,
    openid: null,
    appId: 'cli_9dff7f6ae02ad104',
    feed: {
      notify_content: 'notice that your app wanna show ',
      pathMap: {
        mobile: {
          "default": "page/component/index",
          "image": "page/component/pages/image/image",
          "feed": "page/API/pages/feed/feed",
          'video': "page/component/pages/video/video"
        },
        pc: {
          "default": "page/PC/component/index",
          "image": "page/PC/component/pages/image",
          "feed": "page/PC/API/pages/feed",
          'video': "page/PC/component/pages/video"
        }
      }
    }
  }
})
