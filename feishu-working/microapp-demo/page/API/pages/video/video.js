import i18n from '../../../i18n/index'
const iVideo = i18n.video

var sourceType = [['camera'], ['album'], ['camera', 'album']]
//var camera = [['front'], ['back'], ['front', 'back']]
var duration = Array.apply(null, { length: 60 }).map(function (n, i) {
  return i + 1
})

Page({
  data: {
    sourceTypeIndex: 2,
    sourceType: [iVideo.camera, iVideo.album, iVideo.camera_or_album],
    cameraIndex: 2,
    durationIndex: 59,
    duration: duration.map(function (t) { return t + 'seconds' }),
    src: '',
    ...iVideo
  },
  sourceTypeChange: function (e) {
    this.setData({
      sourceTypeIndex: e.detail.value
    })
  },
  cameraChange: function (e) {
    this.setData({
      cameraIndex: e.detail.value
    })
  },
  durationChange: function (e) {
    this.setData({
      durationIndex: e.detail.value
    })
  },
  chooseVideo: function (e) {
    tt.chooseVideo({
      sourceType: sourceType[this.data.sourceTypeIndex],
      maxDuration: duration[this.data.durationIndex],
      compressed: true,
      success: res => {
        console.log(JSON.stringify(res))
        this.setData({
          src: res.tempFilePath
        })
      }, fail: res => {
        console.log(JSON.stringify(res))
      }, complete: res => {
        console.log(JSON.stringify(res))
      }
    })
  }
})
