Page({
        data: {
            commonInfo: [],
            operationContainerHeight: 0,
            // nfcaBlock: 5,
            // nfcaKey: "d3f7d3f7d3f7"
        },
        onLoad: function () {
            let that = this
            this.listenerList = []
            this.uid = ""
            this.count = 0
            this.nfcUid = undefined
            tt.getSystemInfo({
                success(res) {
                    let height = (res.windowHeight - res.statusBarHeight) * (750 / res.windowWidth) - 460
                    if (that.data.operationContainerHeight === 0) {
                        that.setData({operationContainerHeight: height})
                    }
                },
                fail(res) {
                    that.updateCommonInfo(`设置页面样式错误: ${JSON.stringify(res)}`);
                }
            });
        },
        onClearText(e) {
            tt.vibrateShort({})
            this.setData({commonInfo: []})
        },
        onCopyLog() {
            tt.vibrateShort({})
            let text = ""
            for (let i in this.data.commonInfo) {
                text += this.data.commonInfo[i] + "\n"
            }
            tt.setClipboardData({
                data: text
            });
        },
        updateCommonInfo(text) {
            let list = [text]
            this.setData({commonInfo: list.concat(this.data.commonInfo)})
        },
        addListener(listener) {
            let that = this
            this.checkAdapter()
            this.adapter.onDiscovered(listener);
            this.listenerList.push(listener)
        },
        checkAdapter() {
            if (this.adapter === undefined) {
                this.adapter = tt.getNFCAdapter()
            }
        },
        /**
         * NFCAdapter
         */
        handleGetNFCAdapter() {
            let that = this
            this.adapter = tt.getNFCAdapter()
        },
        handleOnDiscovered() {
            let that = this
            this.checkAdapter()
            this.addListener(this.nfcDiscovered)
        },
        handleStartDiscovery() {
            let that = this
            this.checkAdapter()
            this.adapter.startDiscovery({
                success(res) {
                    that.updateCommonInfo("开始扫描贴卡 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo("开始扫描贴卡失败 " + JSON.stringify(res))
                }
            })
        },
        handleOffDiscovered() {
            let that = this
            this.checkAdapter()
            for (let i in this.listenerList) {
                this.adapter.offDiscovered(this.listenerList[i])
            }
        },
        handleStopDiscovery() {
            let that = this
            this.checkAdapter()
            this.adapter.stopDiscovery({
                success(res) {
                    that.updateCommonInfo("停止扫描贴卡")
                },
                fail(res) {
                    that.updateCommonInfo(`❌停止扫描贴卡失败: ${JSON.stringify(res)}`)
                }
            });
        },
        nfcDiscovered(res) {
            let uid = this.nfcUid = new Uint8Array(res.uid)
            let _res = res
            _res.uid = this.bytesToHex(uid)
            this.updateCommonInfo("扫描到贴卡 " + JSON.stringify(_res))
            this.techs = res.techs
            this.uid = uid
        },
        hexToBytes(hex) {
            return new Uint8Array(hex.match(/[\da-f]{2}/gi).map(function (h) {
                return parseInt(h, 16)
            }));
        },
        bytesToHex(bytes) {
            let hex = [], i = 0
            for (; i < bytes.length; i++) {
                hex.push((bytes[i] >>> 4).toString(16));
                hex.push((bytes[i] & 0xF).toString(16));
            }
            return hex.join("");
        },
        /**
         * NFC-A
         */
        handleGetNFCATag() {
            let that = this
            this.checkAdapter()
            this.NFCATag = this.adapter.getNfcA();
        },
        handleNFCAConnectOnDiscovered() {
            let that = this
            this.checkAdapter()
            this.addListener(this.NFCATagConnect)
        },
        handleNFCAConnect() {
            let that = this
            this.checkAdapter()
            this.NFCATag.connect({
                success(res) {
                    let text = "NFCA手动连接成功 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                },
                fail(res) {
                    let text = "NFCA手动连接失败 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                }
            });
        },
        NFCATagConnect(res) {
            let that = this
            this.NFCATag.connect({
                success(res) {
                    let text = "NFCA连接成功 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                },
                fail(res) {
                    let text = "NFCA连接失败 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                }
            });
        },
        handleNFCAReadTransceive() {
            let that = this
            that.nfcaAuthCmdList = [
                new Uint8Array([0x60, 0x000,
                    this.nfcUid[0] & 0x0ff,
                    this.nfcUid[1] & 0x0ff,
                    this.nfcUid[2] & 0x0ff,
                    this.nfcUid[3] & 0x0ff,
                    0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5 // MifareClassic.KEY_MIFARE_APPLICATION_DIRECTORY
                ]).buffer
            ]
            that.nfcaReadCmdList = [
                new Uint8Array([0x30, 0x000]).buffer
            ]
            for (let i = 1; i < 64; i++) {
                that.nfcaAuthCmdList.push(new Uint8Array([0x60, i & 0x0ff,
                    this.nfcUid[0] & 0x0ff,
                    this.nfcUid[1] & 0x0ff,
                    this.nfcUid[2] & 0x0ff,
                    this.nfcUid[3] & 0x0ff,
                    0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7 // MifareClassic.KEY_NFC_FORUM
                ]).buffer)
                that.nfcaReadCmdList.push(new Uint8Array([0x30, i & 0x0ff]).buffer)
            }
            that.handleBatchNFCARead()
        },
        handleBatchNFCARead() {
            let that = this
            that.nfcaRawData = ""
            that.nfcaReadFlag = 0 // 0 auth, 1 read
            that.nfcaBlockIndex = 0
            that.nfcaReadTimer = setInterval(() => {
                if (that.nfcaReadFlag === 0 && that.techs.includes("MIFARE-Classic")) {
                    that.handleNFCAAuth()
                } else {
                    that.handleNFCARead()
                }
                if (that.nfcaBlockIndex >= that.nfcaAuthCmdList.length) {
                    clearInterval(that.nfcaReadTimer)
                    that.updateCommonInfo(that.nfcaRawData)
                }
            }, 50)
        },
        handleNFCAAuth() {
            let that = this
            that.NFCATag.transceive({
                data: that.nfcaAuthCmdList[that.nfcaBlockIndex],
                success() {
                    that.nfcaReadFlag = 1
                },
                fail(res) {
                    if (that.nfcaBlockIndex < that.nfcaAuthCmdList.length) {
                        that.updateCommonInfo("handleNFCAAuth fail " + that.nfcaBlockIndex + JSON.stringify(res))
                        that.nfcaReadFlag = 1
                    }
                },
            });
        },
        handleNFCARead() {
            let that = this
            that.NFCATag.transceive({
                data: that.nfcaReadCmdList[that.nfcaBlockIndex],
                success(res) {
                    that.nfcaRawData += (
                        "[" + (that.nfcaBlockIndex > 9 ? "" : "0")
                        + that.nfcaBlockIndex + "]\t"
                        + that.bytesToHex(new Uint8Array(res.data))) + "\n"
                    that.updateCommonInfo("reading block " + that.nfcaBlockIndex)
                    that.nfcaReadFlag = 0
                    that.nfcaBlockIndex++
                },
                fail(res) {
                    if (that.nfcaBlockIndex < that.nfcaAuthCmdList.length) {
                        that.updateCommonInfo("read block " + that.nfcaBlockIndex + " " + " fail " + JSON.stringify(res))
                        that.nfcaReadFlag = 0
                        that.nfcaBlockIndex++
                    }
                }
            });
        },
        handleNFCAReadOneBlock() {
            let block = (this.data.nfcaBlock - 0) & 0xff
            let key = this.hexToBytes(this.data.nfcaKey)
            let that = this
            that.nfcaAuthCmdList = [new Uint8Array([0x60, block,
                this.nfcUid[0] & 0x0ff,
                this.nfcUid[1] & 0x0ff,
                this.nfcUid[2] & 0x0ff,
                this.nfcUid[3] & 0x0ff,
                ...key
            ]).buffer]
            that.nfcaReadCmdList = [
                new Uint8Array([0x30, block]).buffer
            ]
            that.handleBatchNFCARead()
        },
        handleInputNFCABlock(e) {
            this.setData({nfcaBlock: e.detail.value})
        },
        handleInputNFCAKey(e) {
            this.setData({nfcaKey: e.detail.value})
        },
        handleInputNFCAData(e) {
            this.setData({nfcaData: e.detail.value})
        },
        handleNFCAWrite() {
            if (this.data.nfcaBlock < 4 || this.data.nfcaBlock > 39) {
                this.updateCommonInfo("为避免卡片写废，请勿写0-3区块和40以上区块！")
                this.setData({nfcaBlock: 4})
                return
            }
            let that = this
            let writeCmd = new Uint8Array([0xA0, (that.data.nfcaBlock - 0) & 0x0ff]).buffer
            let dataCmd = that.hexToBytes(that.data.nfcaData).buffer
            that.updateCommonInfo(that.data.nfcaData)
            that.NFCATag.transceive({
                data: writeCmd,
                success(res) {
                    that.NFCATag.transceive({
                        data: dataCmd,
                        success(res) {
                            that.updateCommonInfo("data success ")
                        },
                        fail(res) {
                            that.updateCommonInfo("data fail ")
                        }
                    })
                },
                fail(res) {
                    that.updateCommonInfo("write fail ")
                }
            })
        },
        NFCATagClose(res) {
            let that = this
            this.NFCATag.close({
                success(res) {
                    let text = "NFCA断开成功 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                },
                fail(res) {
                    let text = "NFCA断开失败 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                }
            })
        },
        handleGetNFCAMaxTransceiveLength() {
            let that = this
            this.NFCATag.getMaxTransceiveLength({
                success(res) {
                    that.updateCommonInfo("NFCA最大传输长度 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NFCA最大传输长度获取失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleNFCASetTimeout1() {
            let that = this
            that.NFCATag.setTimeout({
                'timeout': 1,
                success(res) {
                    that.updateCommonInfo("NFCA设置超时 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NFCA设置超时失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleNFCASetTimeout9() {
            let that = this
            that.NFCATag.setTimeout({
                'timeout': 9000,
                success(res) {
                    that.updateCommonInfo("NFCA设置超时 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NFCA设置超时失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleNFCAIsConnected() {
            let that = this
            that.NFCATag.isConnected({
                'timeout': 1,
                success(res) {
                    that.updateCommonInfo("NFCA已连接 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NFCA未连接或连接失败或其他错误 ${JSON.stringify(res)}`)
                }
            });
        },
        handleGetAtqa() {
            let that = this
            that.NFCATag.getAtqa({
                'timeout': 1,
                success(res) {
                    let atqa = new Uint8Array(res.data)
                    let atqaString = ""
                    for (let i in atqa) {
                        atqaString += atqa[i] + " "
                    }
                    that.updateCommonInfo("getAtqa成功 data: " + atqaString)
                },
                fail(res) {
                    that.updateCommonInfo(`getAtqa失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleGetSak() {
            let that = this
            that.NFCATag.getSak({
                'timeout': 1,
                success(res) {
                    that.updateCommonInfo("getSak成功 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`getSak失败 ${JSON.stringify(res)}`)
                }
            });
        },
        /**
         * MifareClassic
         */
        handleGetMCTag() {
            let that = this
            this.checkAdapter()
            this.MCTag = this.adapter.getMifareClassic();
        },
        handleMCConnectOnDiscovered() {
            let that = this
            this.checkAdapter()
            this.addListener(this.MCTagConnect)
        },
        MCTagConnect(res) {
            let that = this
            this.MCTag.connect({
                success(res) {
                    let text = "MC连接成功 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                },
                fail(res) {
                    let text = "MC连接失败 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                }
            });
        },
        handleMCReadTransceive() {
            let that = this
            that.mfAuthCmdList = [
                new Uint8Array([0x60, 0x000,
                    this.nfcUid[0] & 0x0ff,
                    this.nfcUid[1] & 0x0ff,
                    this.nfcUid[2] & 0x0ff,
                    this.nfcUid[3] & 0x0ff,
                    0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5 // MifareClassic.KEY_MIFARE_APPLICATION_DIRECTORY
                ]).buffer
            ]
            that.mfReadCmdList = [
                new Uint8Array([0x30, 0x000]).buffer
            ]
            for (let i = 1; i < 64; i++) {
                that.mfAuthCmdList.push(new Uint8Array([0x60, i & 0x0ff,
                    this.nfcUid[0] & 0x0ff,
                    this.nfcUid[1] & 0x0ff,
                    this.nfcUid[2] & 0x0ff,
                    this.nfcUid[3] & 0x0ff,
                    0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7 // MifareClassic.KEY_NFC_FORUM
                ]).buffer)
                that.mfReadCmdList.push(new Uint8Array([0x30, i & 0x0ff]).buffer)
            }
            that.mfRawData = ""
            that.mfReadFlag = 0 // 0 auth, 1 read
            that.mfBlockIndex = 0
            that.mfReadTimer = setInterval(() => {
                if (that.mfReadFlag === 0) {
                    that.mfReadFlag = 1
                    that.MCTag.transceive({
                        data: that.mfAuthCmdList[that.mfBlockIndex],
                        success(res) {
                            that.MCTag.transceive({
                                data: that.mfReadCmdList[that.mfBlockIndex],
                                success(res) {
                                    that.updateCommonInfo("mf read success " + that.mfBlockIndex)
                                    that.mfRawData += (
                                        "[" + (that.mfBlockIndex > 9 ? "" : "0")
                                        + that.mfBlockIndex + "]\t"
                                        + that.bytesToHex(new Uint8Array(res.data))) + "\n"
                                    that.mfReadFlag = 0
                                    that.mfBlockIndex++
                                },
                                fail(res) {
                                    if (that.mfBlockIndex < that.mfAuthCmdList.length) {
                                        that.updateCommonInfo("mf read fail " + that.mfBlockIndex)
                                        that.mfReadFlag = 0
                                        that.mfBlockIndex++
                                    }
                                }
                            })
                        },
                        fail(res) {
                            if (that.mfBlockIndex < that.mfAuthCmdList.length) {
                                that.updateCommonInfo("mf auth fail " + that.mfBlockIndex)
                                that.mfReadFlag = 0
                                that.mfBlockIndex++
                            }
                        }
                    })
                }
                if (that.mfBlockIndex >= that.mfReadCmdList.length) {
                    clearInterval(that.mfReadTimer)
                    that.updateCommonInfo(that.mfRawData)
                }
            }, 50)
        },
        handleInputMFCmd(e) {
            this.setData({mfCmd: e.detail.value})
        },
        handleMCWriteTransceive() {
            let that = this
            that.MCTag.transceive({
                data: that.hexToBytes(that.data.mfCmd).buffer,
                success(res) {
                    that.updateCommonInfo('写入MC成功' + res + Array.from(new Uint8Array(res.data)));
                },
                fail(res) {
                    that.updateCommonInfo(`写入MC失败 ${JSON.stringify(res)}`)
                }
            });
        },
        MCTagClose(res) {
            let that = this
            this.MCTag.close({
                success(res) {
                    let text = "MC断开成功 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                },
                fail(res) {
                    let text = "MC断开失败 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                }
            })
        },
        handleGetMCMaxTransceiveLength() {
            let that = this
            this.MCTag.getMaxTransceiveLength({
                success(res) {
                    that.updateCommonInfo("MC最大传输长度 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`MC最大传输长度获取失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleMCSetTimeout1() {
            let that = this
            that.MCTag.setTimeout({
                'timeout': 1,
                success(res) {
                    that.updateCommonInfo("MC设置超时 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`MC设置超时失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleMCSetTimeout9() {
            let that = this
            that.MCTag.setTimeout({
                'timeout': 9000,
                success(res) {
                    that.updateCommonInfo("MC设置超时 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`MC设置超时失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleMCIsConnected() {
            let that = this
            that.MCTag.isConnected({
                'timeout': 1,
                success(res) {
                    that.updateCommonInfo("MC已连接 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`MC未连接或连接失败或其他错误 ${JSON.stringify(res)}`)
                }
            });
        },
        /**
         * NFC-V
         */
        handleGetNFCVTag() {
            let that = this
            this.checkAdapter()
            this.NFCVTag = this.adapter.getNfcV();
        },
        handleNFCVConnectOnDiscovered() {
            let that = this
            this.checkAdapter()
            this.addListener(this.NFCVTagConnect)
        },
        NFCVTagConnect(res) {
            let that = this
            this.NFCVTag.connect({
                success(res) {
                    let text = "NFC-V连接成功 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                },
                fail(res) {
                    let text = "NFC-V连接失败 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                }
            });
        },
        handleNFCVReadTransceive() {
            let that = this
            that.NFCVTag.transceive({
                data: new Uint8Array([0x22, 0x20, ...this.uid, 1]).buffer,
                success(res) {
                    that.updateCommonInfo('读取NFC-V成功' + Array.from(new Uint8Array(res.data)));
                },
                fail(res) {
                    that.updateCommonInfo(`读取NFC-V失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleNFCVWriteTransceive() {
            let that = this
            that.NFCVTag.transceive({
                data: new Uint8Array([0x22, 0x21, ...this.uid, 1, 116, 105, 97, that.count++]).buffer,
                success(res) {
                    that.updateCommonInfo('写入NFC-V成功');
                },
                fail(res) {
                    that.updateCommonInfo(`写入NFC-V失败 ${JSON.stringify(res)}`)
                }
            });
        },
        NFCVTagClose(res) {
            let that = this
            this.NFCVTag.close({
                success(res) {
                    let text = "NFC-V断开成功 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                },
                fail(res) {
                    let text = "NFC-V断开失败 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                }
            })
        },
        handleGetNFCVMaxTransceiveLength() {
            let that = this
            this.NFCVTag.getMaxTransceiveLength({
                success(res) {
                    that.updateCommonInfo("NFC-V最大传输长度 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NFC-V最大传输长度获取失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleNFCVSetTimeout1() {
            let that = this
            that.NFCVTag.setTimeout({
                'timeout': 1,
                success(res) {
                    that.updateCommonInfo("NFC-V设置超时 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NFC-V设置超时失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleNFCVSetTimeout9() {
            let that = this
            that.NFCVTag.setTimeout({
                'timeout': 9000,
                success(res) {
                    that.updateCommonInfo("NFC-V设置超时 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NFC-V设置超时失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleNFCVIsConnected() {
            let that = this
            that.NFCVTag.isConnected({
                'timeout': 1,
                success(res) {
                    that.updateCommonInfo("NFC-V已连接 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NFC-V未连接或连接失败或其他错误 ${JSON.stringify(res)}`)
                }
            });
        },
        /**
         * NDEF
         */
        handleGetNDEFTag() {
            let that = this
            this.checkAdapter()
            this.NDEFTag = this.adapter.getNdef();
        },
        handleNDEFConnectOnDiscovered() {
            let that = this
            this.checkAdapter()
            this.addListener(this.NDEFTagConnect)
        },
        NDEFTagConnect(res) {
            let that = this
            this.NDEFTag.connect({
                success(res) {
                    let text = "NDEF连接成功 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                },
                fail(res) {
                    let text = "NDEF连接失败 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                }
            });
        },
        handleNDEFReadTransceive() {
            let that = this
            that.NDEFTag.transceive({
                data: new Uint8Array([0x30, 0x00]).buffer,
                success(res) {
                    that.updateCommonInfo('读取NDEF成功' + res + Array.from(new Uint8Array(res.data)));
                },
                fail(res) {
                    that.updateCommonInfo(`读取NDEF失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleNDEFWriteTransceive() {
            let that = this
            that.NDEFTag.transceive({
                data: new Uint8Array([0xA0, 0x00, 0x00]).buffer,
                success(res) {
                    that.updateCommonInfo('写入NDEF成功' + res + Array.from(new Uint8Array(res.data)));
                },
                fail(res) {
                    that.updateCommonInfo(`写入NDEF失败 ${JSON.stringify(res)}`)
                }
            });
        },
        NDEFTagClose(res) {
            let that = this
            this.NDEFTag.close({
                success(res) {
                    let text = "NDEF断开成功 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                },
                fail(res) {
                    let text = "NDEF断开失败 " + JSON.stringify(res)
                    that.updateCommonInfo(text)
                }
            })
        },
        handleGetNDEFMaxTransceiveLength() {
            let that = this
            this.NDEFTag.getMaxTransceiveLength({
                success(res) {
                    that.updateCommonInfo("NDEF最大传输长度 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NDEF最大传输长度获取失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleNDEFSetTimeout1() {
            let that = this
            that.NDEFTag.setTimeout({
                'timeout': 1,
                success(res) {
                    that.updateCommonInfo("NDEF设置超时 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NDEF设置超时失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleNDEFSetTimeout9() {
            let that = this
            that.NDEFTag.setTimeout({
                'timeout': 9000,
                success(res) {
                    that.updateCommonInfo("NDEF设置超时 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NDEF设置超时失败 ${JSON.stringify(res)}`)
                }
            });
        },
        handleNDEFIsConnected() {
            let that = this
            that.NDEFTag.isConnected({
                'timeout': 1,
                success(res) {
                    that.updateCommonInfo("NDEF已连接 " + JSON.stringify(res))
                },
                fail(res) {
                    that.updateCommonInfo(`NDEF未连接或连接失败或其他错误 ${JSON.stringify(res)}`)
                }
            });
        },

    }
)
