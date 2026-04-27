import i18n from '../../../i18n/index'
const iSetNavigationBarTitle = i18n.set_navigation_bar_title

Page({
  data: {
    ...iSetNavigationBarTitle
  },
  setNaivgationBarTitle: function (e) {
    var title = e.detail.value.title
    console.log(title)
    tt.setNavigationBarTitle({
      title: title,
      success: function() {
        console.log('setNavigationBarTitle success')
      },
      fail: function(err) {
        console.log('setNavigationBarTitle fail, err is', err)
      }
    })
  }
})
