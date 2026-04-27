import i18n from '../../../i18n/index'
const button = i18n.button

const contentBehavior = require('../../common/component/Content/content-behavior')

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
    ...button
  },
  methods: {

  }
})