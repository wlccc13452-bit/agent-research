import i18n from '../../../i18n/index'
const iGetUserInfo = i18n.get_user_info

var app = getApp()
Page({
	data: {
		hasUserInfo: false,
		withCredentials: false,
		userInfo: {},
		rawData: "",
		signature: "",
		encryptedData: "",
		iv: "",
		...iGetUserInfo
	},
	getUserInfo: function () {
		var that = this;
		console.log('getUserInfo start');
		tt.login({
			success: function (res) {
				tt.getUserInfo({
					withCredentials: that.data.withCredentials,
					success: function (res) {
						console.log('getUserInfo success')
						console.log(arguments);
						tt.showToast({
							title: 'success'
						});
						that.setData({
							hasUserInfo: true,
							userInfo: res.userInfo,
							rawData: res.rawData ? res.rawData : "",
							signature: res.signature ? res.signature : "",
							encryptedData: res.encryptedData ? res.encryptedData : "",
							iv: res.iv ? res.iv : ""
						});
						tt.showModal({
							title: 'get user info',
							content: JSON.stringify(res)
						});
					},
					fail() {
						console.log('getUserInfo fail')
					}
				});
			}, fail: function () {
				console.log(`login fail`);
			}
		});

		console.log('getUserInfo end')
	},
	clear: function () {
		this.setData({
			hasUserInfo: false,
			userInfo: {},
			rawData: "",
			signature: "",
			encryptedData: "",
			iv: ""
		})
	},
	changeCrendentials(e) {
		this.setData({
			withCredentials: e.detail.value
		});
	}
})
