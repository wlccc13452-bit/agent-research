import i18n from '../../../i18n/index'
const iVibrate = i18n.vibrate

Page({
  data: {
    ...iVibrate
  },
  short() {
    tt.vibrateShort({
      success(res) {
        console.log(`${res}`);
      },
      fail(res) {
        console.log(`vibrateShort failed`);
      }
    })
  },
  long() {
    tt.vibrateLong({
      success(res) {
        console.log(`${res}`);
      },
      fail(res) {
        console.log(`vibrateLong failed`);
      }
    })
  }
})
