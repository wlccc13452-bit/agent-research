Component({
  properties: {
    _key: Number,
    active: {
      type: Boolean,
      value: false,
    }
  },
  attached() {
    console.log('wsttest ', );
  },
  methods: {
    onClick(e) {
      this.triggerEvent('clickitem', {key: this.data._key});
    },
  }
})