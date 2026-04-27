let isOverSea = false;
try {
  var res = tt.getSystemInfoSync();
  if (res.host === 'lark') {
    isOverSea = true;
  }
    console.log(res)
} catch (error) {
    console.log(error);
}

function getImageDomain() {
  if (isOverSea) {
    return 'https://sf16-muse-va.ibytedtos.com';
  }
  return 'https://sf3-cn.feishucdn.com';
}

const kindImage = {
  get CONTENT() {
    return `${getImageDomain()}/obj/open-platform-opendoc/615612b9b0a182c35edbd42cb79ff0fe_iKJUp5dGSF.png`;
  },
  get FORM() {
    return `${getImageDomain()}/obj/open-platform-opendoc/1d8d4bd417f27bef2587b69ae2ea8a2c_CrDg7PqveP.png`;
  },
  get LOGO() { 
    return `${getImageDomain()}/obj/open-platform-opendoc/d6e75ef3ca2bbe83d363a1de6b6d5eee_RzxWQb8Y0h.png`;
  },
  get MAP() {
    return `${getImageDomain()}/obj/open-platform-opendoc/41504ecbb0c688631308c29f9b8ff154_AvTd3u20Rb.png`;
  },
  get MEDIA() {
    return `${getImageDomain()}/obj/open-platform-opendoc/1c79816483fce3f65a39f288dc0dd4d8_agitc8co2N.png`;
  },
  get NAV() {
    return `${getImageDomain()}/obj/open-platform-opendoc/29b98f6e40e695cd192a6caa3874be1e_c07PZBxxIc.png`;
  },
  get OTHERS() {
    return `${getImageDomain()}/obj/open-platform-opendoc/05ae3530895d3d83728736980a0392bc_BZSUTWl9c0.png`;
  },
  get VIEW() {
    return `${getImageDomain()}/obj/open-platform-opendoc/b6fa8358d950874b977bfa5b432c8ad6_NwTNQ379Y6.png`;
  }
};

const picImage = {
  get LOGO() {
    return `${getImageDomain()}/obj/open-platform-opendoc/201f80d530c7e4df0ca2c7d8d35ab9dc_OdxAFJ8ksy.png`;
  }
}

const apiKindImage = {
  get API() {
    return `${getImageDomain()}/obj/open-platform-opendoc/39de5770d28e0a02647b3654f0ceb1f5_iKlYw7As8K.png`;
  },
  get DEVICE() {
    return `${getImageDomain()}/obj/open-platform-opendoc/804d59ac7993fb73414f28f1c1d9928f_TlL30Y9XdO.png`;
  },
  get FEEDBACK() {
    return `${getImageDomain()}/obj/open-platform-opendoc/495a0495bdd8e3948e506954ef805660_4fF5vjtq8p.png`;
  },
  get LARK_API() {
    return `${getImageDomain()}/obj/open-platform-opendoc/39de5770d28e0a02647b3654f0ceb1f5_q7xcZPiLV0.png`;
  },
  get LOCATION() {
    return `${getImageDomain()}/obj/open-platform-opendoc/41504ecbb0c688631308c29f9b8ff154_gL7SytDzXs.png`;
  },
  get LOGO() {
    return `${getImageDomain()}/obj/open-platform-opendoc/0d40a730b9cf38f01c1f8bb35b4b7870_4p4E305bQW.png`;
  },
  get MEDIA() {
    return `${getImageDomain()}/obj/open-platform-opendoc/1c79816483fce3f65a39f288dc0dd4d8_uSPjua5oAh.png`;
  },
  get NETWORK() {
    return `${getImageDomain()}/obj/open-platform-opendoc/c9413b17774a2ab8b7dc8d2a6fcc90a4_l5v9pYTzW8.png`;
  },
  get OPEN_API() {
    return `${getImageDomain()}/obj/open-platform-opendoc/110a38ab219b88e37260b8410fb37cfc_0EuOZXIgaB.png`;
  },
  get PAGE() {
    return `${getImageDomain()}/obj/open-platform-opendoc/7e6c522adab8716c034de5fc97e24f24_9EyzHDr4v3.png`;
  },
  get PERFORMANCE() {
    return `${getImageDomain()}/obj/open-platform-opendoc/c45d61a17cccc7a98c5926bd27dfca73_Wfil6IiCRt.png`;
  },
  get STORAGE() {
    return `${getImageDomain()}/obj/open-platform-opendoc/c45d61a17cccc7a98c5926bd27dfca73_fRNCWosj9v.png`;
  }
}

const commonImage = {
  get CUVETTE_H() {
    return `${getImageDomain()}/obj/open-platform-opendoc/1b3c26bced22291aacaf5e19435d0bec_iMKasJYhOm.png`;
  },
  get CUVETTE() {
    return `${getImageDomain()}/obj/open-platform-opendoc/598efe0ec46826c9765fd1ebb286a52f_2s2QurYQUJ.png`;
  },
  get EXPERIMENT_HL() {
    return `${getImageDomain()}/obj/open-platform-opendoc/6d7c50048514429ca3db970e55f86258_KqcLndo70B.png`;
  },
  get EXPERIMENT() { 
    return `${getImageDomain()}/obj/open-platform-opendoc/7965f8e3ac1f68a49d99b1ec27d424a5_1wBRyvOa9u.png`;
  },
  get ICON_API_HL() {
    return `${getImageDomain()}/obj/open-platform-opendoc/b450dc3567164257c40ea2e53d2daa20_2ovMTrEYJs.png`;
  },
  get ICON_API() {
    return `${getImageDomain()}/obj/open-platform-opendoc/145b82b8ad1b96ec9935ef71dd82fa28_MpothLAtSt.png`;
  },
  get ICON_COMPONENT_HL() {
    return `${getImageDomain()}/obj/open-platform-opendoc/f953c9fcd985fe30c99d79163ae4e9c3_GfyzoFQV6l.png`;
  },
  get ICON_COMPONENT() {
    return `${getImageDomain()}/obj/open-platform-opendoc/90086e8f8fbd30adf8e5ff4f7ee293c0_WVyWw9fSR5.png`;
  },
  get ICON_FOOT() {
    return `${getImageDomain()}/obj/open-platform-opendoc/352be4df0bb43e9d7f4489a8790c9efc_BxFuTMfLT2.png`;
  },
  get LOCATION() {
    return `${getImageDomain()}/obj/open-platform-opendoc/95e079b6e8cd790e6f559426b9cf0dbc_WzQ8XJvAHU.png`;
  },
  get PAUSE() { 
    return `${getImageDomain()}/obj/open-platform-opendoc/7b8f7727aa30e7e1f3826b3dd018f8c3_mDOoaHyohB.png`;
  },
  get PLAY() {
    return  `${getImageDomain()}/obj/open-platform-opendoc/177e06e804eb031e01716b817ff49abe_KXfCB3B7QK.png`;
  },
  get PLUS() {
    return `${getImageDomain()}/obj/open-platform-opendoc/007ed547dad67325f681ac9678419e1b_ikOLvX84Ec.png`;
  },
  get RECORD() {
    return `${getImageDomain()}/obj/open-platform-opendoc/9903c32104af1dc577f36add57350644_po4m1sfPPN.png`;
  },
  get STOP() {
    return `${getImageDomain()}/obj/open-platform-opendoc/a82c4cb08f06a913102eed0edb7f5e44_SKf4dbojiJ.png`;
  },
  get TRASH() {
    return `${getImageDomain()}/obj/open-platform-opendoc/551f98cbd298388adf2f294a72dc9539_agH6dWKcMb.png`;
  },
  get LARK_LOGO() {
    return `${getImageDomain()}/obj/open-platform-opendoc/d58b49ffb88e731d89e7bd2a082796eb_dZJtyWZ1ma.svg`;
  }
}

// 组件中依赖的静态资源
const componentDataUrl = {
  get IMAGE_NET_IMAGE() {
    return `${getImageDomain()}/obj/open-platform-opendoc/ff499877393061cde0c1ac6228c316b6_YiG0ROizez.jpeg`;
  }
}

export { kindImage, picImage, apiKindImage, commonImage, componentDataUrl };
