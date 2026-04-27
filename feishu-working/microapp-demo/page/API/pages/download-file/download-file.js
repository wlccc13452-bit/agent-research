import i18n from '../../../i18n/index'
const iDownloadFile = i18n.download_file

const imageURL = 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Sunset_2007-1.jpg/800px-Sunset_2007-1.jpg'
const videoURL = 'http://sf1-ttcdn-tos.pstatp.com/obj/ttfe/tma/test.mp4'

var downloadImageTask;
var downloadVideoTask;
Page({
  data: {
    ...iDownloadFile,
    rgUrls:[
      "http://tosv.byted.org/obj/larkdeveloper/open_doc.doc",
      "http://tosv.byted.org/obj/larkdeveloper/open_docx.docx",
      "http://tosv.byted.org/obj/larkdeveloper/open_xls.xls",
      "http://tosv.byted.org/obj/larkdeveloper/open_xlsx.xlsx",
      "http://tosv.byted.org/obj/larkdeveloper/open_ppt.ppt",
      "http://tosv.byted.org/obj/larkdeveloper/open_ppt.ppt",
      "http://tosv.byted.org/obj/larkdeveloper/open_pptx.pptx",
      "http://tosv.byted.org/obj/larkdeveloper/open_pdf.pdf",
      "https://ttn3pg.apps.bytedance.net/download.doc",
      "https://ttn3pg.apps.bytedance.net/download.xls",
      "https://ttn3pg.apps.bytedance.net/download.xlsx",
      "https://ttn3pg.apps.bytedance.net/download.docx",
      "https://ttn3pg.apps.bytedance.net/download.ppt",
      "https://ttn3pg.apps.bytedance.net/download.pptx",
      "https://ttn3pg.apps.bytedance.net/download.pdf",
    ],
    idxUrl: 0,
    sdUrl:"http://tosv.byted.org/obj/larkdeveloper/open_doc.doc",
    rgMethods:[
      'GET',
      'POST'
    ],
    idxMethod:0,
    sdMethod:'GET',
    rgHeaders:[
      "{\"content-type\":\"text/plain\"}",
      "{\"s-crc-app-id\":\"10012\",\"Content-Type\":\"application/json\","
      +"\"s-crc-token\":\"0ed1fe39709f4c9f9e7fe8071fb8f4f1\",\"s-crc-tpl-code\":\"EMAP_FILE_DOWN\","
      +"\"s-crc-ds-codes\":\"hack2020Download\"}"
    ],
    idxHeader:0,
    sdHeader: "{\"content-type\":\"text/plain\"}",
  },
  downloadImage: function () {
    var self = this

    downloadImageTask = tt.downloadFile({
      url: imageURL,
      success: function (res) {
        console.log(JSON.stringify(res))
        tt.showToast({
          title: 'downloadFile success',
          icon: 'none'
        });
        self.setData({
          imageSrc: res.tempFilePath
        })
      },
      fail: function (res) {
        console.log(JSON.stringify(res))
        tt.showToast({
          title: 'downloadFile Fail',
          icon: 'none'
        });
      }
    });
    downloadImageTask.onProgressUpdate((res) => {
      console.log(JSON.stringify(res))
      self.setData({
        imageProgress: res.progress
      });
    });

  },
  downloadVideo: function () {
    var self = this
    downloadVideoTask = tt.downloadFile({
      url: videoURL,
      success: function (res) {
        console.log(JSON.stringify(res))
        tt.showToast({
          title: 'downloadFile success',
          icon: 'none'
        });
        self.setData({
          videoSrc: res.tempFilePath
        })
      },
      fail: function (res) {
        console.log(JSON.stringify(res))
        tt.showToast({
          title: 'downloadFile Fail',
          icon: 'none'
        });
      }
    });

    downloadVideoTask.onProgressUpdate((res) => {

      console.log("process:" + res.progress);
      console.log("totalBytesWritten:" + res.totalBytesWritten);
      console.log("totalBytesExpectedToWrite:" + res.totalBytesExpectedToWrite);
      self.setData({
        videoProgress: res.progress
      });

      if (res.progress == 50 || res.progress == 51 || res.progress == 52) {

        console.log("----task.abort--------start")
        task.abort()
        console.log("----task.abort--------end")
      }
    });

  },
  saveImageToPhotosAlbum() {
    tt.saveImageToPhotosAlbum({
      filePath: this.data.imageSrc,
      success: res => {
        console.log(JSON.stringify(res))
        tt.showToast({
          title: 'save success',
          icon: 'none',
          success: res => {
            console.log(JSON.stringify(res))
          },
          fail: res => {
            console.log(JSON.stringify(res))
          }
        })
      },
      fail: res => {
        console.log(JSON.stringify(res))
        tt.showToast({
          title: 'save fail',
          icon: 'none',
          success: res => {
            console.log(JSON.stringify(res))
          },
          fail: res => {
            console.log(JSON.stringify(res))
          }
        })
      }
    })
  },
  saveVideoToPhotosAlbum() {
    tt.saveVideoToPhotosAlbum({
      filePath: this.data.videoSrc,
      success(res) {
        tt.showToast({
          title: 'save success',
          icon: 'none'
        });
        console.log(res);
      },
      fail(res) {
        tt.showToast({
          title: 'save fail',
          icon: 'none'
        });
        console.error(res);
      }
    })
  },
  pickUrl:function(e) {
    let sdUrl = this.data.rgUrls[e.detail.value];
    this.setData({
      idxUrl: e.detail.value,
      sdUrl
    })
  },
  inputUrl: function(e) {
    console.log("url=" + e.detail.value);
    this.setData({
      sdUrl: e.detail.value
    })
  },
  pickMethod:function(e) {
    let sdMethod = this.data.rgMethods[e.detail.value];
    this.setData({
      idxMethod: e.detail.value,
      sdMethod
    })
  },
  inputMethod: function(e){
    console.log("method="+ e.detail.value);
    this.setData({
      sdMethod: e.detail.value
    })
  },
  pickHeader:function(e) {
    let sdHeader = this.data.rgHeaders[e.detail.value];
    this.setData({
      idxHeader: e.detail.value,
      sdHeader
    })
  },
  inputHeader: function(e){
    console.log("header="+e.detail.value);
    this.setData({
      sdHeader: e.detail.value
    })
  },
  inputData: function(e){
    console.log("data="+e.detail.value);
    this.setData({
      sdData: e.detail.value
    })
  },
  startDownload: function(e){
    console.log(`开始下载 url=${this.data.sdUrl} method=${this.data.sdMethod} header=${this.data.sdHeader} data=${this.data.sdData}`);
    
    const that = this;
    tt.downloadFile({
      url: this.data.sdUrl,
      method: this.data.sdMethod,
      header: this.data.sdHeader?JSON.parse(this.data.sdHeader):this.data.sdHeader,
      data: this.data.sdData,
      success (res) {
        console.log('downloadFile 调用成功 res=', res);
        if (res.statusCode === 200) {
          that.setData({
            downloadedPath: res.tempFilePath
          });
        }
      },
      fail (res) {
        console.log(`downloadFile 调用失败 res=`, res);
      }
    })
  }
})
