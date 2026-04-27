Page({
  docsInput: function (e) {
    this.docsInputValue = e.detail.value
    this.setData({
      disabled: this.docsInputValue.length <= 0
    })
  },
  internalInput: function (e) {
    this.internalInputValue = e.detail.value
    this.setData({
      disabled: this.internalInputValue.length <= 0
    })
  },
  externalInput: function (e) {
    this.externalInputValue = e.detail.value
    this.setData({
      disabled: this.externalInputValue.length <= 0
    })
  },
  openDocs() {
    tt.openSchema({
      schema: this.docsInputValue,
      success: res => {
        console.log(JSON.stringify(res));
      },
      fail: res => {
        console.log(JSON.stringify(res));
      }
    })
  },
  openInternalURL() {
    tt.openSchema({
      schema: this.internalInputValue,
      external: false,
      success: res => {
        console.log(JSON.stringify(res));
      },
      fail: res => {
        console.log(JSON.stringify(res));
      }
    })
  },
  openExternalURL() {
    tt.openSchema({
      schema: this.externalInputValue,
      external: true,
      success: res => {
        console.log(JSON.stringify(res));
      },
      fail: res => {
        console.log(JSON.stringify(res));
      }
    })
  }
})