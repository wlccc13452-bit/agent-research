import i18n from '../../../i18n/index'
const iVideo = i18n.video

const contentBehavior = require('../../common/component/Content/content-behavior')

Component({
  data: {
    ...iVideo
  },
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  options: {
    addGlobalClass: true,
  },
  methods: {
    videoErrorCallback: function(e) {
      console.log('video error message:')
      console.log(e.detail.errMsg)
    }
  }
})