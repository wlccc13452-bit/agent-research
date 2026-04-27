import i18n from '../../../i18n/index'
const iImageApi = i18n.image_api

var sourceType = [['camera'], ['album'], ['camera', 'album']]

Page({
  data: {
    imageList: [],
    sourceTypeIndex: 2,
    sourceType: [iImageApi.camera, iImageApi.album, iImageApi.album_or_camera],
    qualityTypeIndex: 0,
    qualityType: [iImageApi.origin, iImageApi.compression],
    countIndex: 8,
    count: [1, 2, 3, 4, 5, 6, 7, 8, 9],
    compressImageSrc: '',
    compressedImageSrc: '',
    imageWidth: "",
    imageHeight: "",
    imagePath: "",
    ...iImageApi

  },
  qualityChange: function (e) {
    this.setData({
      qualityTypeIndex: e.detail.value
    })
  },
  sourceTypeChange: function (e) {
    this.setData({
      sourceTypeIndex: e.detail.value
    })
  },
  countChange: function (e) {
    this.setData({
      countIndex: e.detail.value
    })
  },
  chooseImage: function () {
    tt.chooseImage({
      sourceType: sourceType[this.data.sourceTypeIndex],
      count: this.data.count[this.data.countIndex],
      cameraDevice: "front",
      success: res => {
        console.log(JSON.stringify(res))
        this.setData({
          imageList: res.tempFilePaths
        })
      },
      fail(res) {
        console.log(JSON.stringify(res))
      }
    })
  },
  chooseCompressImage: function () {
    tt.chooseImage({
      count: 1,
      sourceType: ['album', 'camera'],
      success: res => {
        console.log(JSON.stringify(res))
        this.setData({
          compressImageSrc: res.tempFilePaths[0]
        })
      },
      fail(res) {
        console.log(JSON.stringify(res))
      }
    });
  },
  previewImage: function (e) {
    var current = e.target.dataset.src

    tt.previewImage({
      current: current,
      urls: this.data.imageList,
      success: res => {
        console.log(JSON.stringify(res))
      },
      fail: res => {
        console.log(JSON.stringify(res))
      }
    })
  },
  previewImage2: function (e) {
    tt.previewImage({
      urls: [e.target.dataset.src],
      success: res => {
        console.log(JSON.stringify(res))
      },
      fail: res => {
        console.log(JSON.stringify(res))
      }
    })
  },
  compressImage: function (e) {
    tt.compressImage({
      src: this.data.compressImageSrc,
      quality: 50,
      success: res => {
        console.log(JSON.stringify(res))
        this.setData({
          compressedImageSrc: res.tempFilePath
        })
      },
      fail: res => {
        console.log(JSON.stringify(res))
        tt.showToast({
          title: JSON.stringify(res),
          duration: 1500,
          mask: false,
          uccess: res => {
            console.log(JSON.stringify(res))
          },
          fail: res => {
            console.log(JSON.stringify(res))
          }
        });
      }
    })
  },
  getimageinfo: function () {
    tt.getImageInfo({
      src: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Sunset_2007-1.jpg/800px-Sunset_2007-1.jpg",
      success: res => {
        console.log(JSON.stringify(res))
        this.setData({
          imageWidth: res.width,
          imageHeight: res.height,
          imagePath: res.path
        })
      },
      fail: res => {
        console.log(JSON.stringify(res))
      }
    })
  }
})
