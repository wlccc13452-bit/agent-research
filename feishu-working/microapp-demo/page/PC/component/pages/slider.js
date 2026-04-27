import i18n from '../../../i18n/index'
const iSlider = i18n.slider

const contentBehavior = require('../../common/component/Content/content-behavior')

const methods = {
  data: {
    ...iSlider
  }
}
for (var i = 1; i < 5; ++i) {
  (function (index) {
    methods['slider' + index + 'change'] = function(e) {
      console.log('slider' + index + 'change event，value : ', e.detail.value)
    }
  })(i)
}

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
    ...iSlider
  },
  methods: {
    ...methods
  }
})