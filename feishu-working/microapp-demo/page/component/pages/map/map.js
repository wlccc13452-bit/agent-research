import i18n from '../../../i18n/index';
import { commonImage } from '../../../imageConfig';
const map = i18n.map

Page({
  data: {
    ...map,
    latitude: 23.099994,
    longitude: 113.324520,
    scale:15,
    markers: [{
      id: 1,
      latitude: 23.099994,
      longitude: 113.324520,
      title: 'T.I.T 创意园',
      iconPath: '/image/location.png'
    },
    {
      latitude: 23.099994,
      longitude: 113.344520,
      title: '111111',
      iconPath: '/image/location.png'
    }, {
      latitude: 23.099994,
      longitude: 113.304520,
      title: '22222',
      iconPath: '/image/location.png'
    }],
    covers: [{
      latitude: 23.499994,
      longitude: 113.344520,
      iconPath: '/image/location.png'
    }, {
      latitude: 23.099994,
      longitude: 113.304520,
      iconPath: '/image/location.png'
    }],
    circles: [{
      latitude: 23.099994,
      longitude: 113.324520,
      radius: 500,
      color: "#313131",
      fillColor: "#121212",
      strokeWidth: 10
    }]
  },
  onReady: function (e) {
    this.mapCtx = tt.createMapContext('myMap',this)
   
  },
  getCenterLocation: function () {
    this.mapCtx.getCenterLocation({
      success: function(res){
        console.log(res.longitude)
        console.log(res.latitude)
      }
    })
  },
  moveToLocation: function () {
      console.log("moveToLocation")
    this.mapCtx.moveToLocation()
  },
  translateMarker: function() {
    this.mapCtx.translateMarker({
      markerId: 1,
      autoRotate: true,
      duration: 1000,
      destination: {
        latitude:23.10229,
        longitude:113.3345211,
      },
      animationEnd() {
        console.log('animation end')
      }
    })
  },
  move: function(){
    console.log("move")
    this.setData({
        latitude:this.data.latitude+1
    })
},
  addZoom: function(){
      console.log("addzoom")
      this.setData({
          scale:this.data.scale+1
      })
      console.log("addzoom")
  },
  includePoints: function() {
    this.mapCtx.includePoints({
      padding: [10],
      points: [{
        latitude:23.10229,
        longitude:113.3345211,
      }, {
        latitude:23.00229,
        longitude:113.3345211,
      }]
    })
  }
})
