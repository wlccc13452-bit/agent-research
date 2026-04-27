import i18n from '../../../i18n/index'
const iIcon = i18n.icon

const contentBehavior = require('../../common/component/Content/content-behavior')

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
    ...iIcon
  },
})