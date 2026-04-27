import i18n from '../../../i18n/index';
const camera = i18n.cameraComponent

Page({
  data: {
    ...camera,
    src: undefined,
    videoSrc: undefined,
    maxZoom: undefined,
    currentDevicePosition: undefined
  },

  onReady: function () {
    this.ctx = tt.createCameraContext('myCamera');
  },
  takePhoto: function () {
    this.ctx.takePhoto({
      success: res => {
        console.log('takePhoto success', res);
        this.setData({
          src: res.tempImagePath
        });
      },
      fail: res => {
        console.log('takePhoto fail', res);
      }
    });
  },

  startRecord: function () {
    this.ctx.startRecord({
      timeoutCallback: res => {
        console.log('startRecord timeout', res);
        this.setData({
          src: res.tempThumbPath,
          videoSrc: res.tempVideoPath
        });
      },
      success: res => {
        console.log('startRecord success', res);
      },
      fail: res => {
        console.log('startRecord fail', res);
      }
    });
  },

  stopRecord: function () {
    this.ctx.stopRecord({
      compressed: this.data.stopRecordCompressed,
      success: res => {
        console.log('stopRecord success', res);
        this.setData({
          src: res.tempThumbPath,
          videoSrc: res.tempVideoPath
        });
      },
      fail: res => {
        console.log('stopRecord fail', res);
      }
    });
  },

  binderror: function (e) {
    console.log('binderror', e);
  },

  bindstop: function (e) {
    console.log('bindstop', e);
  },

  bindinitdone: function (e) {
    console.log('bindinitdone', e.detail);
    this.setData({
      maxZoom: e.detail.maxZoom,
      currentDevicePosition: e.detail.devicePosition,
    })
  },

  previewImage: function () {
    let image = this.data.src;
    tt.previewImage({
      urls: [image]
    })
  },
})
