import i18n from "../../../i18n/index";
const iShare = i18n.share;

Page({
  data: {
    shareData: {
      desc: iShare.custom_share_describe,
    },
    ...iShare,
  },
  onLoad(query) {
    console.log("onLoad", query);
  },
  onShareAppMessage: function (opt) {
    console.log(opt);
    this.setData({
      from: opt.from,
    });
    return Object.assign({}, this.data.shareData, {
      title: opt.from === "button" ? iShare.button_share : iShare.menu_share,
      path: "/page/API/pages/share/share?a=b&from=" + opt.from,
      success(res) {
        console.log("success", res.data);
        setTimeout(function () {
          tt.showModal({
            title: "share success",
            content: JSON.stringify(res.data),
          });
        }, 1000);
      },
      fail(errr) {
        console.error(errr);
      },
    });
  },
  shareWebContent: function () {
    tt.shareWebContent({
      title: "我是分享标题",
      url: "https://www.feishu.cn/",
      success(res) {
        console.log(JSON.stringify(res));
      },
      fail(res) {
        tt.showToast({
          title: "share error",
          icon: "error",
          duration: 1500,
        });
      },
    });
  },
  /*,
  open () {
    tt.showShareMenu({
      success () {
        console.log('show succes');
      },
      fail () {
        console.error('show fail');
      }
    })
  },
  hide() {
    tt.hideShareMenu({
      success() {
        console.log('hide succes');
      },
      fail() {
        console.error('hide fail');
      }
    })
  }*/
});
