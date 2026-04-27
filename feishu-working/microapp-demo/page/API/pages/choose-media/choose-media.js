import i18n from '../../../i18n/index'
const iImageApi = i18n.image_api
const iVideo = i18n.video

var sourceTypes = [
    ['camera'],
    ['album'],
    ['camera', 'album']
]
var duration = Array.apply(null, { length: 60 }).map(function(n, i) {
    return i + 1
})

var mediaTypes = [
    ['image'],
    ['video'],
    ['image', 'video']
]

var sizeTypes = [
    ['original'],
    ['compressed'],
    ['original', 'compressed']
]
var cameraDevices = ['back', 'front']

Page({
    data: {
        dataArray: [],
        sourceTypeIndex: 2,
        sourceType: [iImageApi.camera, iImageApi.album, iImageApi.album_or_camera],
        qualityTypeIndex: 0,
        qualityType: [iImageApi.origin, iImageApi.compression],
        countIndex: 8,
        count: [1, 2, 3, 4, 5, 6, 7, 8, 9],
        duration: duration.map(function(t) { return t + 'seconds' }),
        mediaTypes: [
            'image',
            'video',
            'image and video'
        ],
        mediaTypeIndex: 2,
        durationIndex: 59,
        sizeTypes: [
            'original',
            'compressed',
            'original and compressed'
        ],
        sizeTypeIndex: 2,
        cameraDevices: ['back', 'front'],
        cameraDeviceIndex: 0,
        ...iImageApi,
        ...iVideo

    },
    sizeTypeChange: function(e) {
        this.setData({
            sizeTypeIndex: e.detail.value
        })
    },
    cameraDeviceChange: function(e) {
        this.setData({
            cameraDeviceIndex: e.detail.value
        })
    },
    sourceTypeChange: function(e) {
        this.setData({
            sourceTypeIndex: e.detail.value
        })
    },
    mediaTypeChange: function(e) {
        this.setData({
            mediaTypeIndex: e.detail.value
        })
    },
    countChange: function(e) {
        this.setData({
            countIndex: e.detail.value
        })
    },
    durationChange: function(e) {
        this.setData({
            durationIndex: e.detail.value
        })
    },
    chooseMedia: function() {
        let mediaType = mediaTypes[this.data.mediaTypeIndex]
        let sourceType = sourceTypes[this.data.sourceTypeIndex]
        let count = this.data.count[this.data.countIndex]
        let maxDuration = duration[this.data.durationIndex]
        let sizeType = sizeTypes[this.data.sizeTypeIndex]
        let cameraDevice = cameraDevices[this.data.cameraDeviceIndex]
        console.log("chooseMedia入参")
        console.log(mediaType);
        console.log(sourceType)
        console.log(count)
        console.log(maxDuration)
        console.log(sizeType)
        console.log(cameraDevice);
        const that = this
        tt.chooseMedia({
            mediaType: mediaType,
            sourceType: sourceType,
            count: count,
            maxDuration: maxDuration,
            sizeType: sizeType,
            cameraDevice: cameraDevice,
            success: res => {
                console.log("选择图片/视频回调成功")
                console.log(JSON.stringify(res))
                console.log("res.tempFiles:");
                let dataArray = res.tempFiles
                console.log(dataArray);
                that.setData({ dataArray })
            },
            fail(res) {
                console.log("选择图片/视频回调失败")
                console.log(JSON.stringify(res))
            }
        })
    },
    previewImage: function(e) {
        var current = e.target.dataset.src
        const { dataArray } = this.data
        let urls = dataArray.map((item, index, array) => {
            if (item.type == 'image') {
                return item.tempFilePath
            }
        })
        console.log(urls);
        tt.previewImage({
            current: current,
            urls: urls,
            success: res => {
                console.log(JSON.stringify(res))
            },
            fail: res => {
                console.log(JSON.stringify(res))
            }
        })
    },
})