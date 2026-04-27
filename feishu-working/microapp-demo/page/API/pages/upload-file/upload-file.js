import i18n from '../../../i18n/index'
const iUploadFile = i18n.upload_file
const uploadFileUrl = 'https://14592619.qcloud.la/upload'

Page({
  data: {
    someReason: false,
    ...iUploadFile
  },
  chooseImage: function (e) {
    tt.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album'],
      success: res => {
        console.log(JSON.stringify('chooseImage success', res))
        var localImagePath = res.tempFilePaths[0]
        let task = tt.uploadFile({
          url: uploadFileUrl,
          filePath: localImagePath,
          name: 'data',
          header: {
            a: 'b'
          },
          formData: {
            c: 'd'
          },
          success: res => {
            console.log('uploadFile success', JSON.stringify(res));
            tt.showToast({
              title: 'success',
              icon: 'success',
              duration: 3000
            })
            this.setData({
              imageSrc: localImagePath
            })
          },
          fail: res => {
            console.log('uploadFile fail', JSON.stringify(res))
            tt.showModal({
              title: 'uploadFile fail',
              content: JSON.stringify(res)
            });
          }
        });
        task.onProgressUpdate((res) => {
          console.log(JSON.stringify('onProgressUpdate', res))
          if (res.progress === 50 || res.progress === 51 || res.progress === 52) {
            this.setData({
              someReason: true
            })
            task.abort()
          }
        });
      },
      fail: res => {
        console.log(JSON.stringify(res))
      }
    })
  },
  someR: function (e) {
    var nowS = !this.data.someReason
    this.setData({
      someReason: nowS
    })
    console.log("someReason:" + this.data.someReason)
  },
})
