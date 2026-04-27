import i18n from '../../../i18n/index'

Page({
    showShareMenu: function() {
        tt.showShareMenu({
            success (res) {
                console.log(`res`);
                tt.showToast({
                    title: `success`,
                    icon: ''
                });
            },
            fail (res) {
                console.log(`showShareMenu failure`);
                tt.showToast({
                    title: `failure`,
                    icon: ''
                });
            }
        });

    },
    hideShareMenu: function() {
        tt.hideShareMenu({
            success (res) {
                console.log(`res`);
                tt.showToast({
                    title: `success`,
                    icon: ''
                });
            },
            fail (res) {
                console.log(`hideShareMenu failure`);
                tt.showToast({
                    title: `failure`,
                    icon: ''
                });
            }
        });
    }
})