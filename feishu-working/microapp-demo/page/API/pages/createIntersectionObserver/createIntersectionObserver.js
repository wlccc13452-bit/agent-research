import i18n from '../../../i18n/index'
const iCreateIntersectionObserver = i18n.create_intersection_observer

Page({
  data: {
    appear: false,
    ...iCreateIntersectionObserver
  },
  onReady() {
    this._observer = tt.createIntersectionObserver(this);
    this._observer
      .relativeTo('.scroll-view')
      .observe('.ball', (res) => {
        console.log("IntersectionObserver 对象: ", res);
        this.setData({
          appear: res.intersectionRatio > 0
        });
      })
  },
  onUnload() {
    if (this._observer) {
      this._observer.disconnect();
    }
  }
})
