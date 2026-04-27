import { commonImage } from '../../../imageConfig';
import i18n from '../../../i18n/index';
const iText = i18n.editor;

Page({
    data: {
        placeholder: 'Hello editor!',
        readOnly: false,
        contents: {
            html: `<div id="magicdomid-1_19" class="ace-line align-center heading-h1  locate lineguid-B2nSe8" dir="auto"><span class=" ">${iText.title}</span></div><div id="magicdomid-1_26" class="ace-line blockquote blockquote  locate lineguid-17mqsc" dir="auto"><span class=" ">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${iText.first_paragraph}</span></div><div id="magicdomid-1_27" class="ace-line locate lineguid-6UxLlZ" dir="auto"><span class=" ">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${iText.second_paragraph}</span></div><div id="magicdomid-1_37" class="ace-line locate lineguid-AWIi9E" dir="auto"><span class=" ">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span><span class=" backgroundcolor " style="background-color: #FFF362; ">${iText.last_paragraph}</span></div><div id="magicdomid-1_38" class="ace-line" dir="auto"><br></div><div id="magicdomid-1_34" class="ace-line" dir="auto"><br></div><div id="magicdomid-1_35" class="ace-line image-upload single-line" dir="auto"><span><div contenteditable="false" class="image-container single-elem-cls"><span class="image-wrapper"><span class="point tl n-icon-dragable"></span><span class="point tr n-icon-dragable"></span><span class="point br n-icon-dragable"></span><span class="point bl n-icon-dragable"></span><img src="${commonImage.LARK_LOGO}" data-faketext=" " data-uuid="LxW0dlVX" class="editor_image" style="width: 88px;height: 88px"></span></div></span></div><div id="magicdomid-1_36" class="ace-line" dir="auto"><br></div>`
        },
        plugins: ['indentRight','indentLeft', 'mention', 'undo', 'redo', 'attribution'],
        placeholderStyle: {
            color: '#FFFD00',
            fontSize:"25px"
        }
    },
    onLoad: function () {

    },
    onShow: function () {

    },
    onHide: function () {
    },

    onEditorReady: function (res) {
        console.log('onEditorReady '  + JSON.stringify(res))
    },
    onEditorInputValueChange: function(res) {
        console.log('onEditorInputValueChange '  + JSON.stringify(res))
    },

    onMentionSelect: function(res) {
        console.log('onMentionSelect ' + JSON.stringify(res))
    },

    onMentionClick: function(res) {
        console.log('onMentionClick ' + JSON.stringify(res))
    },

    onInsertImages: function (res) {
        console.log('onInsertImages '  + JSON.stringify(res));
        const images = res.detail.images.map(item => ({
            ...item,
            src: item.filePath,
        }))
        res.insertImagesCallback({ images });
    }
})
