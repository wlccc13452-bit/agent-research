Page({
  chatAndProfileInput: function (e) {
    this.inputValue = e.detail.value
    this.setData({
      disabled: this.inputValue.length <= 0
    })
  },
  openChatIdInput: function (e) {
    this.openChatIdInputValue = e.detail.value
    this.setData({
      disabled: this.openChatIdInputValue.length <= 0
    })
  },
  chatTypeInput: function (e) {
    this.chatTypeInputValue = e.detail.value
    this.setData({
      disabled: this.chatTypeInputValue.length <= 0
    })
  },
  chatFeishu: function (e) {
    tt.login({
      success: res => {
        console.log(JSON.stringify(res));
        tt.enterChat({
          openid: this.inputValue,
          openChatId: this.openChatIdInputValue,
          success: res => {
            console.log(JSON.stringify(res));
          },
          fail: res => {
            console.log(JSON.stringify(res));
          }
        });
      },
      fail: res => {
        console.log(JSON.stringify(res));
      }
    })
  },
  profileFeishu: function (e) {
    tt.login({
      success: res => {
        console.log(JSON.stringify(res))
        tt.enterProfile({ openid: this.inputValue })
      },
      fail: res => {
        console.log(JSON.stringify(res))
      }
    })
  },
  botFeishu: function (e) {
    tt.login({
      success(res) {
        console.log(JSON.stringify(res))
        tt.enterBot({
          success: res => {
            console.log(JSON.stringify(res));
          },
          fail: res => {
            console.log(JSON.stringify(res));
          }
        })
      },
      fail: res => {
        console.log(JSON.stringify(res));
      }
    })
  },
  getChatInfo: function (e) {
    tt.getChatInfo(
      {
        openChatId: this.openChatIdInputValue,
        chatType: this.chatTypeInputValue,
        success: res => {
          console.log(JSON.stringify(res))
        },
        fail: res => {
          console.log(JSON.stringify(res));
        }
      }
    )
  },
  onChatBadgeChange: function (e) {
    tt.onChatBadgeChange(
      {
        openChatId: this.openChatIdInputValue,
        onChange: (res) => {
          console.log(JSON.stringify(res))
        }
      }
    )
  },
  offChatBadgeChange: function (e) {
    tt.offChatBadgeChange(
      {
        openChatId: this.openChatIdInputValue,
      }
    )
  },
})
