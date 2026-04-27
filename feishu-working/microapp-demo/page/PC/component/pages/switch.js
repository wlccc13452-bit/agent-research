import i18n from '../../../i18n/index'
const iSwitch = i18n.switch

const contentBehavior = require('../../common/component/Content/content-behavior')

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
    ...iSwitch
  },
  methods: {
    switch1Change: function (e){
      console.log('switch1 change ，data:', e.detail.value)
    },
    switch2Change: function (e){
      console.log('switch2 change ，data:', e.detail.value)
    }
  }
})