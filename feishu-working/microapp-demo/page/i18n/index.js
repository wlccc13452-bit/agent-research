// const zh = require("./zh")
import zh from './zh'
import en from './en'
import rw from './rw'

let i18n = en
try {
    var res = tt.getSystemInfoSync();
    if (res.language) {
        if (res.language.indexOf('zh') != -1) {
            i18n = zh;
        } else if (res.language.indexOf('rw') != -1) {
            i18n = rw;
        }
    }
    console.log(res)
} catch (error) {
    console.log(error);
}

export default i18n;
