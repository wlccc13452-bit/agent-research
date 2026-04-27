import i18n from '../../../i18n/index'
const iImage = i18n.image

const contentBehavior = require('../../common/component/Content/content-behavior')

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
    ...iImage
  },
  methods: {

  }
})