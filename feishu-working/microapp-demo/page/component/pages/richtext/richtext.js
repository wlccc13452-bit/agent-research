import i18n from "../../../i18n/index"
const richText = i18n.richtext

let params = {
  picture: [],
  at: [
    {
      id: '1234567890',
      name: 'abcabcba ab',
      offset: 1,
      length: 12,
    },
    {
      id: '0987654321',
      name: 'abcabcba ab',
      offset: 14,
      length: 11,
    }
  ],
  userModelSelect: {
    items: ['real name', 'anonymous'],
    data: 'real name'
  },
  placeholder: 'reply：',
  content: ' @abcabcba ab @abcabcba ab ',
  avatar: 'https://developer.apple.com/assets/elements/icons/xcode-12/xcode-12-256x256_2x.png',
  showEmoji: true,
  enablesReturnKey: true
}

Page({
  data: {
    ...richText
  },
  uploadPic: function (e) {
    let show = e.detail.value
    params.picture = show ? [] : null
  },
  showPickerView: function (e) {
    let show = e.detail.value
    params.userModelSelect = show ? {
      items: ['real name', 'anonymous'],
      data: 'real name'
    } : null
    params.avatar = show ? 'https://developer.apple.com/assets/elements/icons/xcode-12/xcode-12-256x256_2x.png' : null
  },
  atContact: function (e) {
    let show = e.detail.value
    params.at = show ? [] : null
  },
  inputEmoji: function (e) {
    let show = e.detail.value
    params.showEmoji = show
  }, enableReturnKey: function (e) {
    let show = e.detail.value
    params.enablesReturnKey = show
  },
  showRichText: function (e) {
    let richText = tt.getRichText();
    richText
      .onShow(function () {
        console.log('show rich text')
      })
      .onPicSelect(function (data) {
        tt.showToast({
          icon: 'none',
          title: JSON.stringify(data),
          duration: 3000
        })
      })
      .onModelSelect(function (data) {
        tt.showToast({
          icon: 'none',
          title: JSON.stringify(data),
          duration: 3000
        })
        if (data.userModelSelect == 'anonymous') {
          params.picture = null
          params.at = null
        } else {
          params.picture = []
          params.at = []
        }
        params.content = data.content
        params.userModelSelect.data = data.userModelSelect
        richText.update(params);
      })
      .onPublish(function (data) {
        console.log(data);
        tt.showToast({
          icon: 'none',
          title: JSON.stringify(data),
          duration: 3000
        })
      })
      .onHide(function (data) {
        console.log(data);
        tt.showToast({
          icon: 'none',
          title: JSON.stringify(data),
          duration: 3000
        })
      })
      .onError(function (err) {
        console.log(err);
        tt.showToast({
          icon: 'none',
          title: err,
          duration: 3000
        })
      });
    richText.show(params);
  }
})
