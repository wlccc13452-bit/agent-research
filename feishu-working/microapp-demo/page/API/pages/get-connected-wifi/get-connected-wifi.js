import i18n from '../../../i18n/index'
const iGetConnectedWifi = i18n.get_connected_wifi

Page({
	data: {
		hasGetWifi: false,
		wifiStr: {
			SSID: '',
			BSSID: '',
			secure: '',
			signalStrength: ''
		},
		...iGetConnectedWifi
	},
	getConnectedWifi: function () {
		var that = this

		tt.getConnectedWifi({
			success(res) {
				console.log(res)
				that.setData({
					hasGetWifi: true,
					'wifiStr.SSID': "Wi-Fi SSID:" + res.SSID,
					'wifiStr.BSSID': "Wi-Fi BSSID:" + res.BSSID,
					'wifiStr.secure': "Wi-Fi is Secure:" + res.secure,
					'wifiStr.signalStrength': "Wi-Fi signal strength :" + res.signalStrength,
				})
			},
			fail(res) {
				console.log(`getConnectedWifi invoke fail`);
			}
		});
	}

})