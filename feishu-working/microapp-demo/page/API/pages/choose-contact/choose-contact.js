import i18n from '../../../i18n/index'
const iChooseContact = i18n.choose_contact

function getChoosenIds(contacts) {
    var arr = [];
    contacts.forEach(element => {
        arr.push(element.openId)
    });
    return arr;
}

Page({
    data: {
        isMulti: true,
        isIgnore: false,
        isDisplayBack: false,
        externalContact: true,
        contacts: [],
        ...iChooseContact
    },
    switchMulti: function(e) {
        this.setData({
            isMulti: e.detail.value
        });
    },
    switchIgnore: function(e) {
        this.setData({
            isIgnore: e.detail.value
        });
    },
    switchDisplayBack: function(e) {
        this.setData({
            isDisplayBack: e.detail.value
        });
    },
    switchExternalContact: function(e){
        this.setData({
            externalContact: e.detail.value
        });
    },
    chooseContact: function(e) {
        tt.login({
            success: res => {
                console.log(JSON.stringify(res))
                if (res.code) {
                    var choosenIds = null;
                    if (this.data.isDisplayBack) {
                        choosenIds = getChoosenIds(this.data.contacts);
                    }
                    console.log('choosen ids:' + choosenIds)
                    tt.chooseContact({
                        multi: this.data.isMulti,
                        ignore: this.data.isIgnore,
                        choosenIds: choosenIds,
                        externalContact: this.data.externalContact,
                        success: res => {
                            console.log(JSON.stringify(res))
                            this.setData({
                                contacts: res.data
                            });
                        },
                        fail(res) {
                            console.log(JSON.stringify(res))
                        }
                    });
                } else {
                    tt.showModal({
                        title: 'local api call success, but login failed'
                    });
                }
            },
            fail: res => {
                console.log(JSON.stringify(res))
                tt.showModal({
                    title: 'login failed'
                });
            }
        });
    }
})