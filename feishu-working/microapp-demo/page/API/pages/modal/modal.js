import i18n from '../../../i18n/index'
const iModal = i18n.modal

Page({
  data: {
    modalHidden: true,
		modalHidden2: true,
		...iModal
  },
  modalTap: function(e) {
    tt.showModal({
      title: iModal.modal_title,
      content: iModal.modal_content,
      showCancel: false,
      confirmText: iModal.confirm,
			success ({ confirm, cancel }) {
				if (confirm) {
					tt.showToast({
						title: iModal.confirm
					})
				}
				if (cancel) {
					tt.showToast({
						title: iModal.cancel,
						icon: "none"
					})
				}
			}
    })
  },
  noTitlemodalTap: function(e) {
    tt.showModal({
      content: iModal.modal_content,
      confirmText: iModal.confirm,
			confirmColor: "#102099",
			cancelText: iModal.cancel,
			cancelColor: "#efefef",
			success({ confirm, cancel }) {
				if (confirm) {
					tt.showToast({
						title: iModal.confirm
					})
				}
				if (cancel) {
					tt.showToast({
						title: iModal.cancel,
						icon: "none"
					})
				}
			}
    })
  }
})
