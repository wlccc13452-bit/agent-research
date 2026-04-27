Page({
    data: {
        shouldChooseChat: true,
        withAdditionalMessage: true,
        chats: [],
        allowCreateGroup: false,
        multiSelect: false,
        ignoreSelf: false,
        externalChat: true,
        selectType: "0",
        cardContent: {
            "card": {
                "card_link": {
                    "android_url": "https://applink.feishu.cn/client/mini_program/open?appId=cli_9cf4d4ab0a7a9103&mode=appCenter&path=pages%2Farticle-detail%2Fmobile%2Findex%3FarticleId%3D6911614172958605316%26lang%3D%26tenateShareToken%3DmH-NWpguoMqONXyFl03T5-XOCr1agL9JSARx8Uevgtg%26from%3Dshare",
                    "ios_url":"https://applink.feishu.cn/client/mini_program/open?appId=cli_9cf4d4ab0a7a9103&mode=appCenter&path=pages%2Farticle-detail%2Fmobile%2Findex%3FarticleId%3D6911614172958605316%26lang%3D%26tenateShareToken%3DmH-NWpguoMqONXyFl03T5-XOCr1agL9JSARx8Uevgtg%26from%3Dshare",
                    "pc_url":"https://applink.feishu.cn/client/mini_program/open?appId=cli_9cf4d4ab0a7a9103&mode=appCenter&path=pages%2Farticle-detail%2Fpc%2Findex%3FarticleId%3D6911614172958605316%26lang%3D%26tenateShareToken%3DmH-NWpguoMqONXyFl03T5-XOCr1agL9JSARx8Uevgtg%26from%3Dshare",
                    "url":"https://applink.feishu.cn/client/mini_program/open?appId=cli_9cf4d4ab0a7a9103&mode=appCenter"
                },
                "config": {
                    "enable_forward": true,
                    "wide_screen_mode": false
                },
                "elements":[{
                    "extra": {
                        "alt": {
                            "tag":"plain_text","content":"飞书"
                        },
                        "img_key": "img_9aeef9d4-80a5-487c-a961-b53091e161bg",
                        "tag":"img"
                    },
                    "tag": "div",
                    "text": {
                        "tag": "plain_text",
                        "content":"2020年2月24日，字节跳动旗下办公套件飞书宣布，向全国所有企业和组织免费开放，不限规模，不限使用时长，所有用户均可使用飞书全部套件功能。2020年11月18日，飞书在北京举办“2020飞书未来无限大会”。会上，飞书推出全新版本“π”，发布独立App“飞书文档”，并在视频会议、即时沟通等功能上宣布了重大更新。",
                        "lines":3
                    }
                }],
                "header": {
                    "title": {
                        "tag":"plain_text",
                        "content":"飞书是字节跳动旗下办公平台，整合即时沟通、日历、音视频会议、云文档、云盘、工作台等功能于一体，成就组织和个人，更高效、更愉悦",
                        "lines":2
                    }
                }
            },
            "msg_type":"interactive"
        },
        // cardContent: {
        //     msg_type: "interactive",
        //     update_multi: false,
        //     card: {
        //         "elements": [{
        //           "tag": "div",
        //           "text": {
        //             "tag": "plain_text",
        //             "content": "Content module"
        //           }
        //         }]
        //     } 
        // }
    },

    chooseChat: function (e) {
        let that = this;
        tt.login({
            success: res => {
                console.log(JSON.stringify(res))
                if (res.code) {
                    tt.chooseChat({
                        allowCreateGroup: that.data.allowCreateGroup,
                        multiSelect: that.data.multiSelect,
                        ignoreSelf: that.data.ignoreSelf,
                        selectType: that.data.selectType,
                        confirmTitle: that.data.confirmTitle,
                        confirmDesc: that.data.confirmDesc,
                        externalChat: that.data.externalChat,
                        success: res => {
                            console.log(JSON.stringify(res))
                            that.setData({
                                chats: res.data
                            });
                        },
                        fail(res) {
                            console.log(JSON.stringify(res))
                        }
                    })
                } else {
                    tt.showModal({
                        title: 'local api call success, but login failed'
                    });
                }
            },
            fail: function () {
                console.log(JSON.stringify(res))
                tt.showModal({
                    title: 'login  failed'
                });
            }
        })
    },

    selectModeChange: function (e) {
        this.setData({
            multiSelect: e.detail.value === "true"
        })
    },
    shouldChooseChat: function (e) {
        this.setData({
            shouldChooseChat: e.detail.value === "true"
        })
    },
    withAdditionalMessage: function (e) {
        this.setData({
            withAdditionalMessage: e.detail.value === "true"
        })
    },
    selectTypeChange: function (e) {
        this.setData({
            selectType: e.detail.value
        })
    },
    otherValueChange: function (e) {
        this.setData({
            ignoreSelf: e.detail.value.includes("0"),
            allowCreateGroup: e.detail.value.includes("1")
        })
    },
    selectExternalChat: function (e) {
        this.setData({
            externalChat: e.detail.value === "true"
        })
    },

    titleInput: function (e) {
        this.setData({
            confirmTitle: e.detail.value
        })
    },

    descInput: function (e) {
        this.setData({
            confirmDesc: e.detail.value
        })
    },

    sendMessageCard: function (e) {
        let that = this;
        var openChatIds =[];
        console.log(this.data.chats);
        this.data.chats.forEach(function(item){
            openChatIds.push(item.id);
            console.log(item.id);
        });
        tt.login({
            success: res => {
                console.log("login success res=", res);
                console.log('qmj-withAdditionalMessage', this.data.withAdditionalMessage);
                if (res.code) {
                    tt.sendMessageCard({
                        openChatIDs: openChatIds,
                        withAdditionalMessage: this.data.withAdditionalMessage,
                        shouldChooseChat: this.data.shouldChooseChat,
                        cardContent: this.data.cardContent,
                        chooseChatParams: {
                            allowCreateGroup: that.data.allowCreateGroup,
                            multiSelect: that.data.multiSelect,
                            ignoreSelf: that.data.ignoreSelf,
                            selectType: that.data.selectType,
                            confirmTitle: that.data.confirmTitle,
                            confirmDesc: that.data.confirmDesc,
                            externalChat: that.data.externalChat,
                        },
                        success: res => {
                            tt.showModal({
                                title: JSON.stringify(res)
                            });
                        },
                        fail(res) {
                            tt.showModal({
                                title: JSON.stringify(res)
                            });
                        }
                    })
                } else {
                    tt.showModal({
                        title: 'local api call success, but login failed'
                    });
                }
            },
            fail: function () {
                console.log(JSON.stringify(res))
                tt.showModal({
                    title: 'login  failed'
                });
            }
        })
    }
});
