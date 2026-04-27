const contentBehavior = require('./content-behavior')

Component({
  properties: {
    currentKey: {
      type: String,
      observer: 'showPage'
    }
  },
  data: {
    loading: true
  },
  relations: {
    'contentBehavior': {
      type: 'child',
      target: contentBehavior
    }
  },
  options: {
    addGlobalClass: true,
  },
  // attached() {
  //   this.showPage(this.data.currentKey);
  // },
  methods: {
    _getAllLi: function (cb) {
      this.getRelationNodes('contentBehavior', (nodes) => {
        cb(nodes);
      })
    },

    showPage(key) {
      let isHide;
      const queue = [];

      const _changeLoading = () => {
        queue.every(e => !!e) && this.setData({loading: false})
      }
      this._getAllLi((nodes) => {
        nodes.map((node, idx) => {
          isHide = node.is === key ? false : true;
          node.setData({isHide}, () => { queue[idx] = true; _changeLoading() });
          queue.push(false)
        })
      })
    }
  }
})