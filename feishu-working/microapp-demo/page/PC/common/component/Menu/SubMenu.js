Component({
  properties: {
    _key: Number,
    title: String,
    items: Array,
    active: {
      type: Boolean,
      value: true,
    },
    currentActive: {
      type: String,
      value: ''
    },
  },
  methods: {
    onClick(e) {
      this.setData({
        active: !this.data.active
      })
      this.triggerEvent('clicksubmenu', {key: this.data._key});
    },
  }
})