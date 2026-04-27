const contentBehavior = require('../../common/component/Content/content-behavior')

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  methods: {

  }
})