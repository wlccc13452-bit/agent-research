import i18n from '../../../i18n/index'
const iToast = i18n.toast

Page({
	data: {
		...iToast
	},
  toast1Tap: function () {
    tt.showToast({
      title: "default toast"
    })
  },
  toast2Tap: function () {
    tt.showToast({
      title: "duration 3000",
      duration: 3000,
			icon: "success"
    });
  },
  toast3Tap: function () {
    tt.showToast({
      title: "loading",
      icon: "loading",
      duration: 3000
    })
  },
	toast4Tap: function () {
		tt.showToast({
			title: "duration 3000，toast when icon is none",
			icon: "none",
			duration: 3000
		})
	},
	toast5Tap: function () {
		tt.showToast({
			title: "Mask",
			mask: true
		})
	},
  hideToast: function () {
    tt.hideToast()
  },

	showLoadingTap () {
		tt.showLoading({
			title: 'can not disappear automatically',
			mask: false
		})
	},

	hideLoadingTap () {
		tt.hideLoading()
	}
})
