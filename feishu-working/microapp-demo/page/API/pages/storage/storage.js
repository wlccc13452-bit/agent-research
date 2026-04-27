import i18n from '../../../i18n/index'
const iStorage = i18n.storage

function showModal(title, content) {
  tt.showModal({
    title,
    content,
    showCancel: false
  })
}
Page({

  data: {
    key: '',
    data: '',
    keysStr: 'keys list:\n',
    ...iStorage
  },

  keyChange(e) {
    this.data.key = e.detail.value
  },

  dataChange(e) {
    this.data.data = e.detail.value
  },

  getStorage() {
    const { key, data } = this.data
    //let storageData

    if (key.length === 0) {

      showModal('load data failed', 'key must not null')
    } else {
      var k = key
      tt.getStorage({
        key: k,
        success(res) {
          showModal('load data success', "data: " + res.data)
          if (!res.data) {
            // request ad data
          }
        },
        fail(res) {
          console.log(`getStorage failed`);
        }
      });
    }
  },

  setStorage() {
    const { key, data } = this.data
    if (key.length === 0) {
      showModal('save data failed', 'key must not null')
    } else {

      try {

        tt.setStorageSync(key, data)

        //no need to call setdata key data
        showModal('save data success', '')
      } catch (error) {
        console.log(`setStorageSync failed`);
      }

    }
  },
  removeStorage() {

    const { key, data } = this.data
    if (key.length === 0) {
      showModal('clear data failed', 'key must not null')
    } else {

      try {
        tt.removeStorageSync(key);
        this.setData({
          key: null,
          data: null
        })
        this.setData({
          key: '',
          data: ''
        })
        showModal('clear data success.', '')

      } catch (error) {
        console.log(`removeStorageSync failed`);
      }

    }

  },
  clearStorage() {

    try {
      tt.clearStorageSync();
      this.setData({
        key: null,
        data: null,
        keysStr: 'keys list:\n'
      })
      this.setData({
        key: '',
        data: '',
        keysStr: 'keys list:\n'
      })
      showModal('clear all data success', '')
    } catch (error) {
      showModal('clearStorageSync failed', '')
      console.log(`clearStorageSync failed:` + error);
    }

  },
  getStorageInfo() {
    this.setData({
      keysStr: 'keys list:\n'
    })
    var that = this
    var strKeys = []
    tt.getStorageInfo({
      success(res) {
        console.log(`getStorageInfo success`);
        strKeys = res.keys
        for (var key of strKeys) { 

          that.setData({
            keysStr: that.data.keysStr + key + '\n'
          })
        }
console.log("s");
        //  console.log(res.keys);
        console.log(res);
       
        console.log("cur:"+res.currentSize);
        console.log("lim:"+res.limitSize);
         console.log("k:"+that.data.keysStr);

      },
      fail(res) {
        console.log(`getStorageInfo failed`);
      }
    });
  },
  getStorageInfoSync() {
    this.setData({
      keysStr: 'keys list:\n'
    })
    var that = this
    var strKeys = []

    try {
      console.log(`getStorageInfoSync success`);
      var res = tt.getStorageInfoSync();
      strKeys = res.keys

      for (var key of strKeys) { 

        that.setData({
          keysStr: that.data.keysStr + key + '\n'
        })
      }
      console.log(res);
      
        console.log("cur:"+res.currentSize);
        console.log("lim:"+res.limitSize);
          console.log("k:"+that.data.keysStr);

    } catch (error) {
      console.log(`getStorageInfoSync failed`);
    }
  }
})