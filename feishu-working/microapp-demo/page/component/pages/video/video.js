import i18n from '../../../i18n/index';
const video = i18n.video_component;

Page({
  data: {
    ...video,
    seekPosition: 0,
    playSpeed: 1
  },
  onReady: function() {
    this.videoContext = tt.createVideoContext('myVideo')
    console.log(this.data.play);
  },

  play: function() {
    this.videoContext.play();
  },

  pause: function() {
    this.videoContext.pause();
  },

  stopVideo: function() {
    this.videoContext.stop();
  },

  enterFullScreen: function() {
    this.videoContext.requestFullScreen();
  },

  getSeekPosition: function(e) {
    const position = parseInt(e.detail.value ?? 0);
    this.setData({
      seekPosition: position
    });
  },

  seek: function() {
    this.videoContext.seek(this.data.seekPosition);
  },

  getPlaySpeed: function(e) {
    const speed = parseFloat(e.detail.value ?? 1);
    this.setData({
      playSpeed: speed
    });
  },

  setPlaySpeed: function() {
    this.videoContext.playbackRate(this.data.playSpeed);
  },

  bindPlay: function() {
    console.log('video play');
  },

  bindPause: function() {
    console.log('video pause');
  },

  bindTimeUpdate: function(e) {
    console.log(`video timeupdate currentTime: ${e.detail.currentTime}, duration: ${e.detail.duration}`);
  },

  bindLoadedMetaData: function(e) {
    console.log(`video loadedmetadata width: ${e.detail.width}, height: ${e.detail.height}, duration: ${e.detail.duration}`);
  },

  bindError: function(e) {
    console.log('video error message: ', e.detail);
  }
})