import i18n from '../../../i18n/index'
const iTextarea = i18n.textarea

const contentBehavior = require('../../common/component/Content/content-behavior')

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
    focus: false,
    ...iTextarea
  },
  methods: {
    bindTextAreaBlur: function(e) {
      console.log(e.detail.value)
    }
  }
})