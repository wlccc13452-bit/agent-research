Component({
  properties: {
    data: {
      type: Array,
    },
    activeSubMenuIndex: {
      type: Number,
      value: 0
    },
    activeItemIdx: {
      type: Number,
      value: 0
    },
    hide: {
      type: Boolean,
      value: false
    }
  },
  methods: {
    onClicksubmenu(e) {
    },
    onClickitem(e) {
      const activeItemIdx = e.detail.key;
      this.setData({
        activeItemIdx
      });
      const key = this.data.data[Math.floor(activeItemIdx/10)].list[Math.floor(activeItemIdx % 10)];
      this.triggerEvent('click', {key});
    }
  }
})