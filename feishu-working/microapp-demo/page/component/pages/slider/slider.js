import i18n from '../../../i18n/index'
const iSlider = i18n.slider

var pageData = {
  data: {
    ...iSlider
  }
}
for (var i = 1; i < 5; ++i) {
  (function (index) {
    pageData['slider' + index + 'change'] = function(e) {
      console.log('slider' + index + 'change event，value : ', e.detail.value)
    }
  })(i)
}
Page(pageData)
