import i18n from '../../../i18n/index'
const iPrompt = i18n.prompt

Page({
	data: {
		...iPrompt
		},
  promptTap: function(e) {
    tt.showPrompt({
	  title: iPrompt.prompt_title,
      maxLength: 40,
	  confirmText: iPrompt.confirm,
	  cancelText: iPrompt.cancel,
	  success (res) {
		  if (res.confirm) {
			  tt.showToast({
				  title: res.inputValue
				})
		  }
		  if (res.cancel) {
			  tt.showToast({
				  title: iPrompt.cancel,
				  icon: "none"
				})
			}
	  },
	  fail (res) {
		  console.log(res);
	  }
	})
  },
  noTitlePromptTap: function(e) {
    tt.showPrompt({
      maxLength: -1,
	  confirmText: iPrompt.confirm,
	  cancelText: iPrompt.cancel,
	  success (res) {
		  if (res.confirm) {
			  tt.showToast({
				  title: res.inputValue
				})
		  }
		  if (res.cancel) {
			  tt.showToast({
				  title: iPrompt.cancel,
				  icon: "none"
				})
			}
	  },
	  fail (res) {
		console.log(res);
	}
	})
  },
})
