import i18n from '../../../i18n/index'
const iSetNavigationBarTitle = i18n.set_navigation_bar_title

Page({
  data: {
    ...iSetNavigationBarTitle
  },
  exec() {
    const query = tt.createSelectorQuery()
    query.select('#the-id').boundingClientRect()
    query.selectViewport().scrollOffset()
    query.exec(function(res){
      tt.showModal({
        title: 'exec',
        content: `res[0].top(#the-id 节点的上边界坐标): ${res[0].top}\nres[1].scrollTop(显示区域的竖直滚动位置): ${res[1].scrollTop}`
      });
    })
  },
  getRect () {
    tt.createSelectorQuery().select('#the-id1').boundingClientRect(function(rect){
      tt.showModal({
        title: 'getRect',
        content: `rect.id(节点的id): ${rect.id}\nrect.dataset(节点的dataset): ${JSON.stringify(rect.dataset)}\nrect.left(节点的左边界坐标): ${rect.left}\nrect.right(节点的右边界坐标): ${rect.right}\nrect.top(节点的上边界坐标): ${rect.top}\nrect.bottom(节点的下边界坐标): ${rect.bottom}\nrect.width(节点的宽度): ${rect.width}\nrect.height(节点的高度): ${rect.height}`
      });
    }).exec()
  },
  getAllRects () {
    tt.createSelectorQuery().selectAll('.class-name').boundingClientRect(function(rects){
      let content = "";
      rects.forEach(function(rect, index) {
        content += `rects[${index}].id(节点的id): ${rect.id}\n`;
      });
      
      tt.showModal({
        title: 'getAllRects',
        content
      });
    }).exec()
  },
  getScrollOffset: function(){
    tt.createSelectorQuery().selectViewport().scrollOffset(function(res){
      tt.showModal({
        title: 'getScrollOffset',
        content: `res.id(节点的id): ${res.id}\nres.dataset(节点的dataset): ${JSON.stringify(res.dataset)}\nres.scrollLeft(节点的水平滚动位置): ${res.scrollLeft}\nres.scrollTop(节点的竖直滚动位置): ${res.scrollTop}`
      });
    }).exec()
  },
  getFields: function(){
    tt.createSelectorQuery().select('#the-id3').fields({
      id: true,
      dataset: true,
      size: true,
      rect: true,
    }, function(res){
      tt.showModal({
        title: 'getFields',
        content: `res.id(节点的id): ${res.id}\nres.dataset(节点的dataset): ${JSON.stringify(res.dataset)}\nres.width(节点的宽度): ${res.width}\nres.height(节点的高度): ${res.height}`
      });
    }).exec()
  }
})
