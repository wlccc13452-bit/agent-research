import i18n from '../../../i18n/index'
const iLogin = i18n.login

var app = getApp()
Page({
  onLoad: function () {
		var that = this;
		tt.checkSession({
			success: function () {
				console.log('session not expired.');
				that.setData({
					hasLogin: true
				});
			},
			fail: function () {
				console.log('session expired');
				that.setData({
					hasLogin: false
				});
  		}
		})
  },
  data: {
		hasLogin: false,
		code: tt.getStorageSync('login.code'),
		...iLogin
	},
  login: function () {
    var that = this
    tt.login({
      success: function (res) {
				if (res.code) {
					that.setData({
						hasLogin: true,
						code: res.code
					});
					
					try{
	          tt.setStorageSync('login.code', res.code);
					}catch(error){
            console.log(`setStorageSync failed`);
					}
				
				} else {
					tt.showModal({
						title: 'function call success, but login failed.'
					});
				}
      },
			fail: function (){
				tt.showModal({
					title: 'login failed.'
				});
			}
    })
  }
})
