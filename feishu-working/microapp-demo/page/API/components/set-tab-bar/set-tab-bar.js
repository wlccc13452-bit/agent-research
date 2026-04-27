import i18n from '../../../i18n/index'
const iTabBar = i18n.set_tab_bar

const defaultTabBarStyle = {
  borderStyle: 'black',
  color: '#7A7E83',
  selectedColor: '#3cc51f',
  backgroundColor: '#ffffff',
}

const defaultItemName = 'API'

Component({
  data: {
    animation: true,
    tabIndex: 0,
    tabTitle: 'Default Title',
    badgeText: '99',
    ...iTabBar
  },

  attached() {
    tt.pageScrollTo({
      scrollTop: 0,
      duration: 0
    })
  },

  detached() {
    this.showTabBar()
  },

  methods: {

    switchAnimation: function(e) {
      this.setData({
        animation: e.detail.value
      });
    },

    tabIndexChange(e) {
      this.data.tabIndex = e.detail.value
    },

    tabTitleChange(e) {
      this.data.tabTitle = e.detail.value
    },

    badgeTextChange(e) {
      this.data.badgeText = e.detail.value
    },

    navigateBack() {
      this.triggerEvent('unmount')
    },

    hideTabBar() {
      tt.hideTabBar({
        animation: this.data.animation,
        complete (res) {
            console.log(`hideTabBar complete`, res);
        }
        })
    },

    showTabBar() {
      tt.showTabBar({
        animation: this.data.animation,
        complete (res) {
            console.log(`showTabBar complete`, res);
        }
        })
    },

    setTabBarItem1() {
      tt.setTabBarItem({
        index: parseInt(this.data.tabIndex),
        text: this.data.tabTitle,
        iconPath: 'image/cuvette.png',
        selectedIconPath: 'image/cuvette_HL.png',
        complete (res) {
            console.log(`setTabBarItem complete`, res);
        }
        })
    },

    setTabBarItem2() {
      tt.setTabBarItem({
        index: parseInt(this.data.tabIndex),
        text: this.data.tabTitle,
        iconPath: 'image/experiment.png',
        selectedIconPath: 'image/experiment_HL.png',
        complete (res) {
            console.log(`setTabBarItem complete`, res);
        }
        })
    },

    setTabBarStyle1() {
      tt.setTabBarStyle({
        color: '#FFFFFF',
        selectedColor: '#FFFF00',
        backgroundColor: '#000000',
        borderStyle: 'white',
        complete (res) {
            console.log(`setTabBarStyle complete`, res);
        }
      })
    },

    setTabBarStyle2() {
      tt.setTabBarStyle({
        color: '#000000',
        selectedColor: '#0000FF',
        backgroundColor: '#FFFFFF',
        borderStyle: 'black',
        complete (res) {
            console.log(`setTabBarStyle complete`, res);
        }
      })
    },

    showTabBarRedDot() {
      tt.showTabBarRedDot({
        index: parseInt(this.data.tabIndex),
        complete (res) {
            console.log(`showTabBarRedDot complete`, res);
        }
        })
    },

    hideTabBarRedDot() {
      tt.hideTabBarRedDot({
        index: parseInt(this.data.tabIndex),
        complete (res) {
            console.log(`hideTabBarRedDot complete`, res);
        }
        })
    },

    setTabBarBadge() {
      tt.setTabBarBadge({
        index: parseInt(this.data.tabIndex),
        text: this.data.badgeText,
        complete (res) {
            console.log(`setTabBarBadge complete`, res);
        },
      })
    },

    removeTabBarBadge() {
      tt.removeTabBarBadge({
        index: parseInt(this.data.tabIndex),
        complete (res) {
            console.log(`removeTabBarBadge complete`, res);
        }
        })
    },

    removeTabBarItem() {
      tt.removeTabBarItem({
        tag: 'page/component/index',
        complete (res) {
            console.log(`removeTabBarItem complete`, res);
        }
      })
    },
  }
})
