import i18n from '../i18n/index';
import apiList from './api-list';
import { apiKindImage } from '../imageConfig';
const iAPI = i18n.api

Page({
  data: {
    logoIcon: apiKindImage.LOGO,
    isSetTabBarPage: false,
    apiTip: iAPI.api_tip,
    list: apiList
  },
  onLoad: function(data) {
    if (data && data.showTabBarPage === 'true') {
      this.setData({ isSetTabBarPage: true });
    }
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
        if (list[i].url) {
          tt.navigateTo({
            url: 'pages/' + list[i].url
          })
          return
        }
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
    if (url === 'pages/tabbar/tabbar') {
      this.setData({
        isSetTabBarPage: true
      })
      return;
    }
    tt.navigateTo({
      url
    })
  },
  leaveSetTabBarPage() {
    this.setData({
      isSetTabBarPage: false
    });
  }
})
