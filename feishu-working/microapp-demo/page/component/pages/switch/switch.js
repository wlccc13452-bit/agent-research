import i18n from '../../../i18n/index'
const iSwitch = i18n.switch
console.log(i18n)

Page({
  data: {
    ...iSwitch
  },
  switch1Change: function (e){
    console.log('switch1 change ，data:', e.detail.value)
  },
  switch2Change: function (e){
    console.log('switch2 change ，data:', e.detail.value)
  }
})
