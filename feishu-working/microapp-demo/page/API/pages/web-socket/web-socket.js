import i18n from '../../../i18n/index'
const web_socket = i18n.web_socket
console.log('...',i18n)
var gTexts = [
  'line 1',
  'line 2',
  'line 3',
  'line 4',
  'line 5'
];
var gCounter = 0;


function showModal(title, content) {
  tt.showModal({
    title,
    content,
    showCancel: false
  })
}

function showSuccess(title) {
  tt.showToast({
    title,
    icon: 'success',
    duration: 1000
  })
}
function showMsg(title) {
  tt.showToast({
    title,
    icon: "none",
    duration: 1000
  })
}

Page({

  data: {
    socketStatus: 'closed',
    text: web_socket.tip,
    ...web_socket
  },

  onLoad() {
    const self = this
    self.setData({
      hasLogin: true
    })
  },

  onUnload() {
    this.closeSocket()
  },

  toggleSocket(e) {
    const turnedOn = e.detail.value

    if (turnedOn && this.data.socketStatus == 'closed') {
      this.openSocket()
    } else if (!turnedOn && this.data.socketStatus == 'connected') {
      const showSuccess = true
      this.closeSocket(showSuccess)
    }
  },

  openSocket() {

    var that = this;


    //open signal
    that.socket = tt.connectSocket({
      url: 'wss://frontier.snssdk.com/ws/v2?aid=1288&device_id=98543534&fpid=72&access_key=f075e82cde98601fc5d41302af325631',
      success() {
        console.log('Build WebSocketTask success');

      },
      fail(err) {
        console.error('Build WebSocketTask failed', err);
        showMsg('build WebSocketTask failed')
      }

    });

    that.socket.onOpen(() => {
      console.log('WebSocket connected')
      showSuccess('Socket connected')
      this.setData({
        socketStatus: 'connected',
        text: '',
        waitingResponse: false
      })
    })

    that.socket.onClose(() => {
      console.log('WebSocket disconnected')
      this.setData({ socketStatus: 'closed' })
      showMsg('WebSocket disconnected')
    })

    that.socket.onError(error => {
      showModal('WebSocket has some error', JSON.stringify(error))
      console.error('socket error:', error)
      this.setData({
        loading: false,
        socketStatus: 'errored'

      })
    })

    // event for push
    that.socket.onMessage(message => {
      showSuccess('receive message')
      console.log('socket message:', message)
      let data = message.data;

      this.setData({
        loading: false,
        text: that.data.text + '[receive] ' + data + '\n'

      })
    })

  },

  closeSocket() {
    if (this.data.socketStatus == 'connected') {
      this.socket.close({
        success: () => {
          showSuccess('Socket disconnected')
          this.setData({ socketStatus: 'closed' })
        }
      })
    }
  },

  sendMessage() {
    var that = this;

    if (this.data.socketStatus == 'connected') {
      this.socket.send({
        data: gTexts[gCounter],
        success() {
          console.log('send success');
          that.setData({
            text: that.data.text + '[send] ' + gTexts[gCounter] + '\n'
          });
          gCounter += 1;
          if (gCounter >= gTexts.length) {
            gCounter = 0;
          }
        },
        fail() {
          console.error('send failed');
        }

      })
    }
  },
})
