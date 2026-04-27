import i18n from '../../../i18n/index'
const feed = i18n.feed

const contentBehavior = require('../../common/component/Content/content-behavior')

const globalData = getApp().globalData
const { appId, feed: {pathMap: {mobile: mobilePath, pc: pcPath}, notify_content } } = globalData

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
    notify_content,
    items: [
      { value: 'default', name: 'Default page', checked: true },
      { value: 'image', name: 'Image page'},
      { value: 'feed', name: 'Feed page' },
      { value: 'video', name: 'Video page' },
    ],
    pcPath: pcPath.default,
    mobilePath: mobilePath.default,
    ...feed
  },
  methods: {
    bindKeyInput(e) {
      this.setData({
        notify_content: e.detail.value
      })
    },
    radioChange: function (e) {
      const value = e.detail.value;
      var items = this.data.items;
      for (var i = 0, len = items.length; i < len; ++i) {
        items[i].checked = items[i].value == value
      }

      this.setData({
        items: items,
        mobilePath: mobilePath[value],
        pcPath: pcPath[value]
      });
    },
    onClick(e) {
      const that = this;
      tt.login({
        complete(e) {
        },
        success(res) {
          const code = res.code;
          tt.request({
            url: 'https://cloudapi.bytedance.net/faas/services/ttrmjbc27jpg1hs7mt/invoke/appnotify',
            data: {
              app_id: appId,
              code,
              method: 'POST',
              notify_content: that.data.notify_content,
              "pc_schema": {
                "path": that.data.pcPath,
                "query": "dst=pc"
              },
              "ios_schema": {
                "path": that.data.mobilePath,
                "query": "dst=mobile"
              },
              "android_schema": {
                "path": that.data.mobilePath,
                "query": "dst=mobile"
              }
            },
            header: {
              'content-type': 'application/json'
            },
            success(res) {
              if (res.data.code != 0) {
                tt.showToast({
                  title: 'send app notify fail',
                  icon: 'error'
                })
                console.log(`appnotify: request error `, res.data.msg);
                return;
              }
              tt.showToast({
                title: 'send app notify success',
                icon: 'success'
              })
            },
            fail(res) {
              console.log(`appnotify: request error`);
            }
          })
        }
      })
    }
  }
})