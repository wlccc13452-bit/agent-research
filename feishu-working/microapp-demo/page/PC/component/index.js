import i18n from '../../i18n/index.js'
const { component: iComponent, api: iAPI } = i18n

const COMP_MENU_DATA = [
  {
    key: 'content',
    title: iComponent.basic_content,
    active: true,
    list: [
      'icon',
      'text',
      // 'richtext',
      'progress'
    ]
  }, {
    key: 'view',
    title: iComponent.view_container,
    list: [
      'view',
      'scroll-view',
      // 'swiper'
    ]
  }, {
    key: 'form',
    title: iComponent.form,
    list: [
      'button',
      'checkbox',
      // 'form',
      'input',
      'label',
      'picker',
      // 'picker-view',
      'radio',
      'slider',
      'switch',
      'textarea'
    ]
  },
  // {
  //   key: 'nav',
  //   title: iComponent.navigation,
  //   list: ['navigator']
  // },
  {
    key: 'media',
    title: iComponent.media_component,
    list: [
      'image',
      'video'
    ]
  },
  {
    key: 'others',
    title: iComponent.other,
    list: [
      'canvas',
      'web-view'
    ]
  }
]

const API_MENU_DATA = [
  {
    key: 'mode',
    title: iAPI.mode,
    list: [
      'feed'
    ]
  }
]

const pwd = "/page/PC/component/pages/"

Page({
  data: {
    currentPage: pwd + 'icon',
    menuData: [COMP_MENU_DATA, API_MENU_DATA],
    activeItemIdx0: 0,
    activeItemIdx1: -1,
    component: iComponent.component,
    api: iAPI.api,
    hide_1: false,
    hide_2: false
  },
  toggleMenu1(e) {
    const hide_1 = this.data.hide_1;
    this.setData({
      hide_1: !hide_1
    })
  },
  toggleMenu2(e) {
    const hide_2 = this.data.hide_2;
    this.setData({
      hide_2: !hide_2
    })
  },
  onClick(e) {
    const { key } = e.detail;
    const { key: _key } = e.currentTarget.dataset;
    if (_key == 0) {
      this.setData({
        activeItemIdx1: -1
      })
    } else if (_key == 1) {
      this.setData({
        activeItemIdx0: -1
      })
    }
    this.showPage(key);
  },
  showPage(key) {
    const api_keys = ['feed'];
    if (api_keys.includes(key)) {
      this.setData({
        currentPage: "/page/PC/API/pages/" + key
      })
      return;
    }
    this.setData({
      currentPage: pwd + key
    })
  },
})