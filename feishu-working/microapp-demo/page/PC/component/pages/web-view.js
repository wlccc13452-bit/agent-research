import i18n from '../../../i18n/index'
const iWebview = i18n.webview

const contentBehavior = require('../../common/component/Content/content-behavior')

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
    ...iWebview
  },
  methods: {
    openWebview(e) {
      tt.navigateTo({
        url: '/page/PC/component/pages/web-view-page',
        complete(e) {
        }
      })
    }
  }
})