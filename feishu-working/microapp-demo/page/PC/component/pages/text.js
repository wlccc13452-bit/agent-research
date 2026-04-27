import i18n from '../../../i18n/index'
const iText = i18n.text

var texts = [
  'line 1',
  'line 2',
  'line 3',
  'line 4',
  'line 5'
];

const contentBehavior = require('../../common/component/Content/content-behavior')

const extraLine = [];

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
    text: '',
    canAdd: true,
    canRemove: false,
    ...iText
  },
  
  methods: {
    add: function (e) {
      var that = this;
      extraLine.push(texts[extraLine.length % 5])
      this.setData({
        text: extraLine.join('\n'),
        canAdd: extraLine.length < 5,
        canRemove: extraLine.length > 0
      })
      setTimeout(function () {
        that.setData({
          scrollTop: 99999
        });
      }, 0)
    },
    remove: function (e) {
      var that = this;
      if (extraLine.length > 0) {
        extraLine.pop()
        this.setData({
          text: extraLine.join('\n'),
          canAdd: extraLine.length < 5,
          canRemove: extraLine.length > 0,
        })
      }
      setTimeout(function () {
        that.setData({
          scrollTop: 99999
        });
      }, 0)
    }
  }
})