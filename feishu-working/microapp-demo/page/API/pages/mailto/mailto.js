import i18n from '../../../i18n/index'
const iMailto = i18n.mailto

Page({
  data: {
    ...iMailto
  },
  mailto: function() {
    tt.mailto({
      to: ["test@bytedance.com"],
      cc: ["test.cc@bytedance.com", "test.cc2@bytedance.com"],
      bcc: ["test.bcc@bytedance.com"],
      subject: 'test',
      body: 'text',
      success (res) {
        console.log('open system mail box success.');
      },
      fail (res) {
        console.log('send email failed.');
      }
    });
  }
})
