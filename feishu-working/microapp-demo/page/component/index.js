import i18n from '../i18n/index.js'
import componentList from './component-list'
import { kindImage } from '../imageConfig';
const iComponent = i18n.component

const appInstance = getApp()
Page({
  data: {
    list: componentList,
    logoIcon: kindImage.LOGO,
    componentTip: iComponent.component_tip
  },
  onLaunch: function () {
    console.log('index Launch')
  },
  onLoad: function (params) {
    console.log('page/component/index onLoad')
    console.log(params)
    console.log('-------------')
  },
  onShow: function () {
    console.log('page/component/index onShow')
    console.log('-------------')

    if (!appInstance.globalData.hasLogin) {
      console.log('haslogin' + appInstance.globalData.hasLogin)
      tt.reLaunch({
        url: 'page/API/pages/chat/chat',
        success: (res) => {
          console.log('relaunch success----' + 'page/API/pages/chat/chat')
        }, fail: (res) => {
          console.log('relaunch fail----' + 'page/API/pages/chat/chat')
        }
      });
    }

  },
  onReady: function () {
    console.log('page/component/index onReady')
    console.log('-------------')
  },
  onHide: function () {
    console.log('page/component/index onHide')
    console.log('-------------')
  },
  onUnload: function () {
    console.log('page/component/index onUnload')
    console.log('-------------')
  },
  onTabItemTap: function (e) {
    tt.showToast({
      title: 'click',
      icon: 'none',
      image: '',
      duration: 1500,
      mask: false
    });
  },
  onTabbarDoubleTap: function (e) {
    tt.showToast({
      title: 'double click',
      icon: 'none',
      image: '',
      duration: 1500,
      mask: false
    });
  },
  kindToggle: function (e) {
    var id = e.currentTarget.id, list = this.data.list;
    for (var i = 0, len = list.length; i < len; ++i) {
      if (list[i].id == id) {
        list[i].open = !list[i].open
      } else {
        list[i].open = false
      }
    }
    this.setData({
      list: list
    });
  },
  gotoPage({ currentTarget: { dataset: { url } } }) {
    tt.navigateTo({
      url
    })
  }
})

