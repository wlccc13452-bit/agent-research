import i18n from '../i18n/index'
import { apiKindImage } from  '../imageConfig';
const iAPI = i18n.api

let apiList = [
  {
    id: 'openApi',
    icon: apiKindImage.OPEN_API,
    name: iAPI.open_ability,
    open: false,
    pages: [
      {
        zh: iAPI.login,
        url: 'login/login'
      },
      {
        zh: 'checkSession',
        url: 'check-session/check-session'
      },
      {
        zh: iAPI.get_user_info,
        url: 'get-user-info/get-user-info'
      }, {
        zh: iAPI.share,
        url: 'share/share'
      }, {
        zh: iAPI.contact,
        url: 'choose-contact/choose-contact'
      }, {
        zh: iAPI.biometric,
        url: 'device-authentication/device-authentication'
      }, {
        zh: iAPI.password_verify,
        url: 'password-verify/password-verify'
      }, {
        zh: iAPI.send_email,
        url: 'mailto/mailto'
      }, {
        zh: iAPI.check_watermark,
        url: 'watermark/watermark'
      }, {
        zh: iAPI.live_check,
        url: 'live-check/live-check'
      }, {
        zh: iAPI.choose_chat,
        url: 'choose-chat/choose-chat'
      }, {
        zh: iAPI.send_msg_card,
        url: 'send-msg-card/send-msg-card'
      },
      {
        zh: iAPI.authorized,
        url: 'authorized/authorized'
      },
       {
        zh: iAPI.launch_query,
        url: 'get-launch-query/get-launch-query'
      }
    ]
  },
  {
    id: 'network',
    icon: apiKindImage.NETWORK,
    name: iAPI.network,
    open: false,
    pages: [
      {
        zh: iAPI.send_a_request,
        url: 'request/request'
      }, {
        zh: iAPI.webSocket,
        url: 'web-socket/web-socket'
      }, {
        zh: iAPI.upload_file,
        url: 'upload-file/upload-file'
      }, {
        zh: iAPI.download_file,
        url: 'download-file/download-file'
      }
    ]
  }, {
    id: 'media',
    icon: apiKindImage.MEDIA,
    name: iAPI.media,
    open: false,
    pages: [
      {
        zh: iAPI.image,
        url: 'image/image'
      }, {
        zh: iAPI.recording,
        url: 'voice/voice'
      }, {
        zh: iAPI.file,
        url: 'file/file'
      }, {
        zh: iAPI.audio,
        url: 'inneraudio/inneraudio'
      },
      {
        zh: iAPI.video,
        url: 'video/video'
      },
      {
        zh: iAPI.choose_media,
        url: 'choose-media/choose-media'
      }
    ]
  }, {
    id: 'storage',
    icon: apiKindImage.STORAGE,
    name: iAPI.storage,
    url: 'storage/storage'
  }, {
    id: 'location',
    icon: apiKindImage.LOCATION,
    name: iAPI.location,
    open: false,
    pages: [
      {
        zh: iAPI.get_location,
        url: 'get-location/get-location'
      },
      
      {
        zh: iAPI.open_location,
        url: 'open-location/open-location'
      },
      {
        zh: iAPI.choose_location,
        url: 'choose-location/choose-location'
      }
    ]
  }, {
    id: 'device',
    icon: apiKindImage.DEVICE,
    name: iAPI.device,
    open: false,
    pages: [
      {
        zh: iAPI.canvas,
        url: 'canvas/canvas'
      },
      {
        zh: iAPI.get_system_info,
        url: 'get-system-info/get-system-info'
      },
      {
        zh: iAPI.get_network_type,
        url: 'get-network-type/get-network-type'
      }, {
        zh: iAPI.monitor_network_change,
        url: 'on-network-status-change/on-network-status-change'
      },
      {
        zh: 'Wi-Fi',
        url: 'get-connected-wifi/get-connected-wifi'
      },
      {
        zh: iAPI.monitor_gravity_sensing_data,
        url: 'on-accelerometer-change/on-accelerometer-change'
      },
      {
        zh: iAPI.monitor_compass_data,
        url: 'on-compass-change/on-compass-change'
      },
      {
        zh: iAPI.make_phone_call,
        url: 'make-phone-call/make-phone-call'
      },
      {
        zh: iAPI.scan_code,
        url: 'scan-code/scan-code'
      },
      {
        zh: iAPI.clipboard,
        url: 'get-clipboard-data/get-clipboard-data'
      },
      {
        zh: iAPI.screen_brightness,
        url: 'screen-brightness/screen-brightness'
      },
      {
        zh: iAPI.vibrate,
        url: 'vibrate/vibrate'
      }, {
        zh: iAPI.monitor_user_screen_capture,
        url: 'on-user-capture-screen/on-user-capture-screen'
      }, {
        zh: iAPI.bluetooth,
        url: 'bluetooth/bluetooth'
      },{
        zh: "wifiList",
        url: 'wifilist/wifilist'
      },{
        zh: iAPI.nfc,
        url: 'nfc/nfc'
      }
    ]
  }, {
    id: 'page',
    icon: apiKindImage.PAGE,
    name: iAPI.interface,
    open: false,
    pages: [
      {
        zh: iAPI.toast_tip,
        url: 'toast/toast'
      },
      {
        zh: iAPI.modal_tip,
        url: 'modal/modal'
      },
      {
        zh: iAPI.prompt_tip,
        url: 'prompt/prompt'
      },
      {
        zh: iAPI.actionsheet_tip,
        url: 'action-sheet/action-sheet'
      },
      {
        zh: iAPI.set_navigation_bar_title,
        url: 'set-navigation-bar-title/set-navigation-bar-title'
      }, {
        zh: iAPI.create_animation,
        url: 'animation/animation'
      },
      {
        zh: iAPI.page_position,
        url: 'page-scroll-to/page-scroll-to'
      },
      {
        zh: iAPI.pull_down_refresh,
        url: 'pull-down-refresh/pull-down-refresh'
      },
      {
        zh: 'Tab Bar',
        url: 'tabbar/tabbar'
      },
      {
        zh: iAPI.enter_level,
        url: 'enter-level-back/enter-level-back'
      }
    ]
  },
  {
    id: 'feedback',
    icon: apiKindImage.FEEDBACK,
    name: iAPI.navigation,
    url: 'navigator/navigator'
  },
  {
    id: 'api',
    icon: apiKindImage.API,
    name: 'API',
    open: false,
    pages: [
      {
        zh: 'native',
        url: 'chat/chat'
      },
      {
        zh: 'Open Schema',
        url: 'openschema/openschema'
      },
      
      {
        zh: 'Share Menu',
        url: 'share_menu/share_menu'
      }
    ]
  }, {
    id: 'ttml',
    name: 'TTML',
    open: false,
    pages: [
      {
        zh: 'createSelectorQuery',
        url: 'createSelectorQuery/createSelectorQuery'
      },
      {
        zh: 'createIntersectionObserver',
        url: 'createIntersectionObserver/createIntersectionObserver'
      },
    ]
  }
];

export default apiList;
