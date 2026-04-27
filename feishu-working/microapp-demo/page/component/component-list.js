import i18n from '../i18n/index.js';
import { kindImage as imagePath} from '../imageConfig';
const iComponent = i18n.component

const componentList = [
  {
    id: 'content',
    icon: imagePath.CONTENT,
    name: iComponent.basic_content,
    open: false,
    pages: [
      'icon',
      'text',
      'richtext',
      'progress'
    ]
  }, {
    id: 'view',
    icon: imagePath.VIEW,
    name: iComponent.view_container,
    open: false,
    pages: [
      'view',
      'scroll-view',
      'swiper'
    ]
  }, {
    id: 'form',
    icon: imagePath.FORM,
    name: iComponent.form,
    open: false,
    pages: [
      'button',
      'checkbox',
      'form',
      'input',
      'label',
      'picker',
      'picker-view',
      'radio',
      'slider',
      'switch',
      'textarea',
      'editor'
    ]
  },
  {
    id: 'map',
    icon: imagePath.MAP,
    name: iComponent.map,
    open: false,
    pages: [
      'map'
    ]
  },
  {
    id: 'nav',
    icon: imagePath.NAV,
    name: iComponent.navigation,
    open: false,
    pages: ['navigator']
  },
  {
    id: 'media',
    icon: imagePath.MEDIA,
    name: iComponent.media_component,
    open: false,
    pages: [
      'image',
      'video',
      'camera'
    ]
  },
  {
    id: 'others',
    icon: imagePath.OTHERS,
    name: iComponent.other,
    open: false,
    pages: [
      'canvas',
      'web-view'
    ]
  }
];

export default componentList;