import i18n from '../../../i18n/index';
import { commonImage } from '../../../imageConfig';
const iInneraudio = i18n.inneraudio;

var app = getApp();
var util = require('../../../../util/util.js');
var dataUrl = 'https://sf1-ttcdn-tos.pstatp.com/obj/developer/sdk/0000-0002.mp3';
function log() {
	console.log.apply(log, arguments);
}

const defaultFormatedTime = '00:00:00';

Page({
	data: {
		formatedCurrentTime: defaultFormatedTime,
		formatedDuration: defaultFormatedTime,
		duration: 0,
		currentTime: 0,
		playing: false,
		paused: false,
		buffered: 0,
		pauseIcon: commonImage.PAUSE,
		stopIcon: commonImage.STOP,
		playIcon: commonImage.PLAY,
		...iInneraudio
	},
	onLoad: function () {
		this.canUpdateUI = true;
		var iac = this.innerAudioContext = tt.createInnerAudioContext();

		iac.src = dataUrl;
		iac.startTime = 0;
		iac.autoplay = true;
		iac.loop = false;
		iac.obeyMuteSwitch = false;

		iac.onCanplay(() => {
			log('onCanplay', 'audio is ready to play.');
			this.updateUI();
		});

		iac.onPlay(() => {
			log('onPlay', 'audio is playing.');
			this.updateUI();
		});

		iac.onPause(() => {
			log('onPause', 'audio play paused.');
			this.updateUI();
		});

		iac.onStop(() => {
			log('onStop', 'audio play stoped.');
			this.updateUI();
		});

		iac.onEnded(() => {
			log('onEnded', 'audio play ended.');
			this.updateUI();
		});

		iac.onTimeUpdate(() => {
			log('onTimeUpdate', 'audio play progress updated.');
			this.updateUI();
		});

		iac.onError(() => {
			log('onError', 'audio play error.');
			this.updateUI();
		});

		iac.onWaiting(() => {
			log('onWaiting', 'waiting for audio loading.');
			this.updateUI();
		});

		iac.onSeeking(() => {
			log('onSeeking', 'audio is seeking.');
			this.updateUI();
		});

		iac.onSeeked(() => {
			log('onSeeked', 'audio has finish seek.');
			this.updateUI();
		});
	},
	updateUI() {
		var iac = this.innerAudioContext;
		log(this.data);
		if (this.canUpdateUI) {
			this.setData({
				formatedCurrentTime: util.formatTime(parseInt(iac.currentTime) || 0) || defaultFormatedTime,
				formatedDuration: util.formatTime(parseInt(iac.duration) || 0) || defaultFormatedTime,
				duration: parseInt(iac.duration) || 0,
				currentTime: iac.currentTime || 0,
				playing: !iac.paused,
				buffered: parseInt(iac.buffered) || 0
			});

		}
	},
	onUnload() {
		if (this.innerAudioContext) {
			this.innerAudioContext.destroy();
		}
	},
	pause() {
		this.innerAudioContext.pause();
		this.updateUI();
	},
	play() {
		this.innerAudioContext.play();
		this.updateUI();
	},
	stop() {
		this.innerAudioContext.stop();
		this.updateUI();
	},
	seeking(e) {
		log('scrolling, can not update UI', e.detail.value);
		this.canUpdateUI = false;
	},
	seek(e) {
		log('finish scrolling, seek setup.', e.detail.value);
		this.canUpdateUI = true;
		try {
			this.innerAudioContext.seek(e.detail.value);
		} catch (ex) {
			log(ex);
		}
	},
	setloop(e) {
		this.innerAudioContext.loop = e.detail.value;
	},
	setmute(e) {
		this.innerAudioContext.obeyMuteSwitch = e.detail.value;
	}
})
