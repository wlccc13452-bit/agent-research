import i18n from '../../../i18n/index'
const checkbox = i18n.checkbox

Page({
  data: {
    items: [
      {value: 'watermelon', name: 'watermelon'},
      {value: 'apple', name: 'apple', checked: 'true'},
      {value: 'pear', name: 'pear'},
      {value: 'banana', name: 'banana'},
      {value: 'orange', name: 'orange'},
      {value: 'grape', name: 'grape'},
    ],
    ...checkbox
  },
  checkboxChange: function(e) {
    console.log('Checkbox change，value：', e.detail.value)

    var items = this.data.items, values = e.detail.value;
    for (var i = 0, lenI = items.length; i < lenI; ++i) {
      items[i].checked = false;

      for (var j = 0, lenJ = values.length; j < lenJ; ++j) {
        if(items[i].value == values[j]){
          items[i].checked = true;
          break
        }
      }
    }

    this.setData({
      items: items
    })
  }
})
