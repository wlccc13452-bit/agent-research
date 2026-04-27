import i18n from '../../../i18n/index'
const iActionSheet = i18n.action_sheet

Page({
  data: {
    ...iActionSheet
  },
  actionSheetTap: function () {
    tt.showActionSheet({
      itemList: ['item1', 'item2', 'item3', 'item4'],
      success: res => {
        console.log(JSON.stringify(res))
        tt.showToast({
          title: `You click ${res.tapIndex + 1} item`
        });
      },
      fail: res => {
        console.log(JSON.stringify(res))
      }
    });
  }
})
