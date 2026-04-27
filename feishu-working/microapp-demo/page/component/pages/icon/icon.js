import i18n from '../../../i18n/index'
const iIcon = i18n.icon

Page({
  data :{
    icons: [
      ['success', 'success_no_circle'],
      ['info', 'warn'],
      ['waiting', 'clear'],
      ['cancel', 'download'],
      ['search']
    ],
    sizes: [66, 48, 36, 24],
    colors: ['#222222', '#CACACA', '', '#50ABF9'],
    i18nText: iIcon
  },
})
