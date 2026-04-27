import i18n from '../../../i18n/index'
const radio = i18n.radio

const contentBehavior = require('../../common/component/Content/content-behavior')

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
    items: [
      {value: 'watermelon', name: 'watermelon'},
      {value: 'apple', name: 'apple', checked: 'true'},
      {value: 'pear', name: 'pear'},
      {value: 'banana', name: 'banana'},
      {value: 'orange', name: 'orange'},
      {value: 'grape', name: 'grape'},
    ],
    ...radio
  },
  methods: {
    radioChange: function(e) {
      console.log('Radio emmit change event，value ：', e.detail.value)
  
      var items = this.data.items;
      for (var i = 0, len = items.length; i < len; ++i) {
        items[i].checked = items[i].value == e.detail.value
      }
  
      this.setData({
        items: items
      });
    }
  }
})