import i18n from '../../../i18n/index'
const iEnterWindow = i18n.api

Page({
    data: {
        effect: ['close']
    },
    onLoad: function () {
        this.enableLeaveConfirm()
    },
    back(e) {
        const value = e.detail.value
        const { effect } = this.data
        if (value) {
            effect.push('back');
        } else {
            const index = effect.findIndex(item => item === 'back');
            effect.splice(index, 1)
        }
        this.setData({
            effect
        })
        this.enableLeaveConfirm()
    },
    close(e) {
        const value = e.detail.value
        const { effect } = this.data
        if (value) {
            effect.push('close');
        } else {
            const index = effect.findIndex(item => item === 'close');
            effect.splice(index, 1)
        }
        this.setData({
            effect
        })
        this.enableLeaveConfirm()
    },
    enableLeaveConfirm() {
        this.disableLeaveConfirm()
        const { effect } = this.data
        if (typeof tt.enableLeaveConfirm != 'function') {
            tt.showModal({
                title: 'enableLeaveConfirm not a function'
            })
            return
        }
        tt.enableLeaveConfirm({
            effect: effect,
            title: iEnterWindow.enter,
            content: iEnterWindow.enter_content,
            success(res) {
                console.log(res)
            },
            fail(err) {
                console.log(err)
            }
        })
    },
    disableLeaveConfirm() {
        if (typeof tt.disableLeaveConfirm != 'function') {
            tt.showModal({
                title: 'disableLeaveConfirm not a function'
            })
            return
        }
        tt.disableLeaveConfirm()
    },

})