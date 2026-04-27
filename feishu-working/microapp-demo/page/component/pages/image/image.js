import i18n from '../../../i18n/index';
import { componentDataUrl } from '../../../imageConfig';
console.log('qmj-hhh', componentDataUrl.IMAGE_NET_IMAGE);

const iImage = i18n.image

Page({
    data :{
        ...iImage,
        netImageUrl: componentDataUrl.IMAGE_NET_IMAGE
    }
})
