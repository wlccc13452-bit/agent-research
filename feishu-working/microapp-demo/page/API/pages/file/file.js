import i18n from "../../../i18n/index";
const iFile = i18n.file;
const userTestDir = "ttfile://user/test/dir";
const writeFilePath = `ttfile://user/example.txt`
const OPEN_DOC_DOWNLOAD_FILE_URL = 'http://tosv.byted.org/obj/larkdeveloper';
const fileSystemManager = tt.getFileSystemManager()
Page({
  onLoad: function (e) {
    this.setData({
      savedFilePath: tt.getStorageSync("savedFilePath"),
    });
  },
  data: {
    tempFilePath: "",
    savedFilePath: "",
    dialog: {
      hidden: true,
    },
    fileList: [],
    ...iFile,
    testCaseItemVisibleList: {},
    openDocumentData: {
      cloudFile: 'https://bytedance.feishu.cn/docs/doccniQHjlLnfuyPN15633dwcie',
      doc: `${OPEN_DOC_DOWNLOAD_FILE_URL}/open_doc.doc`,
      docx: `${OPEN_DOC_DOWNLOAD_FILE_URL}/open_docx.docx`,
      xls: `${OPEN_DOC_DOWNLOAD_FILE_URL}/open_xls.xls`,
      xlsx: `${OPEN_DOC_DOWNLOAD_FILE_URL}/open_xlsx.xlsx`,
      ppt: `${OPEN_DOC_DOWNLOAD_FILE_URL}/open_ppt.ppt`,
      pptx: `${OPEN_DOC_DOWNLOAD_FILE_URL}/open_ppt.pptx`,
      pdf: `${OPEN_DOC_DOWNLOAD_FILE_URL}/open_pdf.pdf`,
      eml: 'https://sf3-cn.feishucdn.com/obj/open-platform-opendoc/cbf20702d9c17662e0461b096c86f5ba_Ku2dSHZjve.eml'
    },
    isLocalFilePath: false,
    filePath: "",
    localFilePath: "",
    fileTypes: [
      { value: 'doc', name: 'doc', checked: 'true' },
      { value: 'docx', name: 'docx' },
      { value: 'xls', name: 'xls' },
      { value: 'xlsx', name: 'xlsx' },
      { value: 'ppt', name: 'ppt' },
      { value: 'pptx', name: 'pptx' },
      { value: 'pdf', name: 'pdf' },
      { value: 'eml', name: 'eml' }
    ],
    showMenu: true
  },
  chooseImage: function (e) {
    tt.chooseImage({
      count: 1,
      success: (res) => {
        console.log(JSON.stringify(res));
        this.setData({
          tempFilePath: res.tempFilePaths[0],
        });
      },
    });
  },
  saveFileSync: function () {
    if (!this.checkTestFile()) {
      return;
    }
    try {
      const savedFilePath = fileSystemManager.saveFileSync(this.data.tempFilePath)
      tt.showToast({
        title: 'saveFileSync success'
      });
    } catch (err) {
      console.log(err)
      tt.showToast({
        title: 'saveFileSync error'
      });
    }
  },
  saveFile: function (e) {
    if (this.data.tempFilePath.length > 0) {
      tt.saveFile({
        tempFilePath: this.data.tempFilePath,
        success: (res) => {
          console.log(JSON.stringify(res));
          this.setData({
            savedFilePath: res.savedFilePath,
          });
          tt.setStorageSync("savedFilePath", res.savedFilePath);
          this.setData({
            dialog: {
              title: "Save Success",
              content: "The file will restore when you enter app next time.",
              hidden: false,
            },
          });
        },
        fail: (res) => {
          console.log(JSON.stringify(res));
          this.setData({
            dialog: {
              title: "Save Failed",
              content: "may be have some bug",
              hidden: false,
            },
          });
        },
      });
    } else {
      tt.showToast({
        title: "please select file first",
      });
    }
  },
  clear: function (e) {
    tt.setStorageSync("savedFilePath", "");
    this.setData({
      tempFilePath: "",
      savedFilePath: "",
    });
  },
  docsPickerLark: function (e) {
    tt.docsPicker({
      maxNum: 2,
      pickerTitle: "Pick Docs",
      pickerConfirm: "OKay",
      success: (res) => {
        console.log(JSON.stringify(res));
        this.setData({
          fileList: res.fileList,
        });
      },
      fail: (res) => {
        console.log(JSON.stringify(res));
        tt.showToast({
          title: "Choose attachment failed.",
          icon: "none",
          image: "",
          duration: 1500,
        });
      },
    });
  },
  filePickerLark: function (e) {
    tt.filePicker({
      maxNum: 2,
      success: (res) => {
        console.log(JSON.stringify(res));
        this.setData({
          fileList: res.list,
        });
      },
      fail: (res) => {
        console.log(JSON.stringify(res));
        tt.showToast({
          title: "Choose attachment failed.",
          icon: "none",
          image: "",
          duration: 1500,
        });
      },
    });
  },
  filePickerSystem: function (e) {
    tt.filePicker({
      isSystem: true,
      success: (res) => {
        console.log(JSON.stringify(res));
        this.setData({
          fileList: res.list,
        });
      },
      fail: (res) => {
        console.log(JSON.stringify(res));
        tt.showToast({
          title: "Choose attachment failed.",
          icon: "none",
          image: "",
          duration: 1500,
        });
      },
    });
  },
  openDocument: function (e) {
    const preStatus = this.data.testCaseItemVisibleList.openDocument;
    this.setData({
      testCaseItemVisibleList: { openDocument: !preStatus },
    });
  },
  openDocumentImpl: function (fileType) {
    const openDocClz = (filePath) => {
      tt.openDocument({
        filePath,
        fileType,
        showMenu: this.data.showMenu,
        success: (res) => {
          console.log('openDocumentImpl success');
        },
        fail: (res) => {
          console.log('openDocumentImpl fail res=' + JSON.stringify(res));
          tt.showToast({
            title: 'openDocumentImpl failed',
            icon: ''
          })
        }
      });
    }
    console.log('openDocumentImpl fileType=' + fileType)
    const documentUrl = this.data.openDocumentData[fileType];
    if (fileType === 'cloudFile') {
      openDocClz(documentUrl);
      return;
    }
    const storagePath = `ttfile://user/a.${fileType}`;
    tt.downloadFile({
      url: documentUrl,
      filePath: storagePath,
      success: (res) => {
        console.log('openDocumentImpl downloadFile success filePath=' + storagePath);
        openDocClz(storagePath)
      },
      fail: (res) => {
        console.log('openDocumentImpl download file failed res=' + JSON.stringify(res));
        tt.showToast({
          title: 'openDocument download failed',
          icon: ''
        })
      }
    });
  },
  openCloudFile: function (e) {
    this.openDocumentImpl('cloudFile')
  },
  openDoc: function (e) {
    this.openDocumentImpl('doc')
  },
  openDocx: function (e) {
    this.openDocumentImpl('docx')
  },
  openPpt: function (e) {
    this.openDocumentImpl('ppt')
  },
  openPptx: function (e) {
    this.openDocumentImpl('pptx')
  },
  openPdf: function (e) {
    this.openDocumentImpl('pdf')
  },
  openXls: function (e) {
    this.openDocumentImpl('xls')
  },
  openXlsx: function (e) {
    this.openDocumentImpl('xlsx')
  },
  openEml: function (e) {
    this.openDocumentImpl('eml')
  },
  checkTestFile: function () {
    const path = this.data.tempFilePath;
    if (!path || path.length <= 0) {
      tt.showToast({
        title: "please choose file first",
      });
      return false;
    }
    return true;
  },
  accessFile: function (e) {
    if (!this.checkTestFile()) {
      return;
    }
    tt.getFileSystemManager().access({
      path: this.data.tempFilePath,
      success: (res) => {
        tt.showToast({
          title: "success accessFile",
        });
        console.log("accessFile success res=" + JSON.stringify(res));
      },
      fail: (error) => {
        tt.showToast({
          title: "failed accessFile",
        });
        console.error("accessFile failed error=" + JSON.stringify(error));
      },
    });
  },
  accessFileSync: function (e) {
    if (!this.checkTestFile()) {
      return;
    }
    try {
      tt.getFileSystemManager().accessSync(this.data.tempFilePath)
      tt.showToast({
        title: "success accessFileSync",
      });
    } catch (err) {
      tt.showToast({
        title: 'error accessFileSync'
      });
    }
  },
  copyFileSync: function (e) {
    if (!this.checkTestFile()) {
      return;
    }
    const filePaths = this.data.tempFilePath.split("/");
    const fileName = filePaths[filePaths.length - 1];
    const destPath = `ttfile://user/${fileName}_${Date.now()}.copy`;
    try {
      fileSystemManager.copyFileSync(this.data.tempFilePath, destPath)
      tt.showToast({
        title: "success copyFileSync",
      });
    } catch (error) {
      console.log(error)
      tt.showToast({
        title: "failed copyFileSync",
      });
    }
  },
  copyFile: function (e) {
    if (!this.checkTestFile()) {
      return;
    }
    const filePaths = this.data.tempFilePath.split("/");
    const fileName = filePaths[filePaths.length - 1];
    const destPath = `ttfile://user/${fileName}_${Date.now()}.copy`;
    tt.getFileSystemManager().copyFile({
      srcPath: this.data.tempFilePath,
      destPath,
      success: (res) => {
        tt.showToast({
          title: "success copyFile",
        });
        console.log("copyFile success res=" + JSON.stringify(res));
      },
      fail: (error) => {
        tt.showToast({
          title: "failed copyFile",
        });
        console.debug("copyFile failed error=" + JSON.stringify(error));
      },
    });
  },
  getFileInfo: function (e) {
    if (!this.checkTestFile()) {
      return;
    }
    tt.getFileSystemManager().getFileInfo({
      filePath: this.data.tempFilePath,
      success: (res) => {
        tt.showToast({
          title: "success getFileInfo",
        });
        console.log("getFileInfo success res=" + JSON.stringify(res));
      },
      fail: (error) => {
        tt.showToast({
          title: "failed getFileInfo",
        });
        console.debug("getFileInfo failed error=" + JSON.stringify(error));
      },
    });
  },
  getSavedFileList: function (e) {
    tt.getFileSystemManager().getSavedFileList({
      success: (res) => {
        this.setData({ savedFileList: res.fileList });
        tt.showToast({
          title: "success getSavedFileList",
        });
        console.log("getSavedFileList success res=" + JSON.stringify(res));
      },
      fail: (error) => {
        tt.showToast({
          title: "failed getSavedFileList",
        });
        console.debug("getSavedFileList failed error=" + JSON.stringify(error));
      },
    });
  },
  mkdirSync: function (e) {
    const recursive = true;
    try {
      fileSystemManager.mkdirSync(userTestDir, recursive)
      tt.showToast({
        title: "success mkDirSync",
      });
    } catch (error) {
      tt.showToast({
        title: "failed mkDirSync",
      });
    }
  },
  mkDir: function (e) {
    const recursive = true;
    tt.getFileSystemManager().mkdir({
      dirPath: userTestDir,
      recursive,
      success: (res) => {
        tt.showToast({
          title: "success mkDir",
        });
        console.log("mkDir success res=" + JSON.stringify(res));
      },
      fail: (error) => {
        tt.showToast({
          title: "failed mkDir",
        });
        console.debug("mkDir failed error=" + JSON.stringify(error));
      },
    });
  },
  checkSavedFileList: function () {
    if (!this.data.savedFileList || this.data.savedFileList.length <= 0) {
      tt.showToast({
        title: "savedFiles empty",
      });
      return false;
    }
    return true;
  },
  removeSavedFile: function (e) {
    const preStatus = this.data.testCaseItemVisibleList.removeSavedFile;
    this.setData({
      testCaseItemVisibleList: { removeSavedFile: !preStatus },
    });
  },
  rename: function (e) {
    if (!this.checkSavedFileList()) {
      return;
    }
    const paths = this.data.savedFileList[0].filePath.split("/");
    const fileName = paths[paths.length - 1];
    tt.getFileSystemManager().rename({
      oldPath: this.data.savedFileList[0].filePath,
      newPath: `ttfile://user/${fileName}.rename`,
      success: (res) => {
        tt.showToast({
          title: "success rename",
        });
        console.log("rename success res=" + JSON.stringify(res));
      },
      fail: (error) => {
        tt.showToast({
          title: "failed rename",
        });
        console.debug("rename failed error=" + JSON.stringify(error));
      },
    });
  },
  renameSync() {
    if (!this.checkSavedFileList()) {
      return;
    }
    const paths = this.data.savedFileList[0].filePath.split("/");
    const fileName = paths[paths.length - 1];
    try {
      fileSystemManager.renameSync(this.data.savedFileList[0].filePath, `ttfile://user/${fileName}.renameSync`)
      tt.showToast({
        title: "success renameSync",
      });
    } catch (err) {
      console.log(err)
      tt.showToast({
        title: "error renameSync",
      });
    }
  },
  rmDir: function (e) {
    tt.getFileSystemManager().rmdir({
      dirPath: userTestDir,
      recursive: true,
      success: (res) => {
        tt.showToast({
          title: "success rmDir",
        });
        console.log("rmDir success res=" + JSON.stringify(res));
      },
      fail: (error) => {
        tt.showToast({
          title: "failed rmDir",
        });
        console.debug("rmDir failed error=" + JSON.stringify(error));
      },
    });
  },
  readDirSync: function (e) {
    try {
      const files = fileSystemManager.readdirSync(userTestDir)
      console.log("readDirSync success res=" + JSON.stringify(files));
      tt.showToast({
        title: "success readDirSync",
      });
    } catch (err) {
      console.log(err)
      tt.showToast({
        title: "failed readDirSync",
      });
    }
  },
  readDir: function (e) {
    tt.getFileSystemManager().readdir({
      dirPath: userTestDir,
      success: (res) => {
        tt.showToast({
          title: "success readDir",
        });
        console.log("readDir success res=" + JSON.stringify(res));
      },
      fail: (error) => {
        tt.showToast({
          title: "failed readDir",
        });
        console.debug("readDir failed error=" + JSON.stringify(error));
      },
    });
  },
  rmDirSync() {
    try {
      fileSystemManager.rmdirSync(userTestDir)
      tt.showToast({
        title: "success readDirSync",
      });
    } catch (err) {
      console.log(err)
      tt.showToast({
        title: "error readDirSync",
      });
    }
  },
  confirm: function (e) {
    this.setData({
      "dialog.hidden": true,
    });
  },
  inputDocFilePath: function (e) {
    console.log("filePath=" + e.detail.value)
    this.setData({
      filePath: e.detail.value
    });
  },
  fileTypeChange: function (e) {
    console.log('fileType=' + e.detail.value)

    const items = this.data.fileTypes
    for (let i = 0, len = items.length; i < len; ++i) {
      items[i].checked = items[i].value === e.detail.value
    }

    this.setData({
      fileTypes: items,
      fileType: e.detail.value
    })
  },
  switchShowMenu: function (e) {
    console.log("showMenu=" + e.detail.value)
    this.setData({
      showMenu: e.detail.value
    });
  },
  open: function (e) {
    const filePath = this.data.filePath;
    const fileType = this.data.fileType;
    const showMenu = this.data.showMenu;
    if (!filePath) {
      this.openDocumentImpl(fileType);
      return;
    }
    console.log(`打开文档 filePath=${filePath} fileType=${fileType} showMenu=${showMenu}`)

    const openDocClz = (filePath, fileType, showMenu) => {
      tt.openDocument({
        filePath,
        fileType,
        showMenu,
        success: (res) => {
          console.log('openDocumentImpl success');
        },
        fail: (res) => {
          console.log('openDocumentImpl fail res=' + JSON.stringify(res));
          tt.showToast({
            title: 'openDocumentImpl failed',
            icon: ''
          })
        }
      });
    }

    openDocClz(filePath, fileType, showMenu);
  },
  inputFilePathForRemove: function (e) {
    this.data.filePathForRemove = e.detail.value;
  },
  remove: function (e) {
    const filePath = this.data.filePathForRemove;
    console.log("删除文件 filePath=" + filePath);
    tt.getFileSystemManager().removeSavedFile({
      filePath,
      success: (res) => {
        tt.showToast({
          title: "success",
        });
        console.log("removeSavedFile success res=" + JSON.stringify(res));
      },
      fail: (error) => {
        tt.showToast({
          title: "failed",
        });
        console.debug("removeSavedFile failed error=" + JSON.stringify(error));
      },
    });
  },
  unlink: function (e) {
    let saveFilePath = tt.getStorageSync("savedFilePath");
    if (!saveFilePath) {
      return;
    }

    tt.getFileSystemManager().unlink({
      filePath: saveFilePath,
      success: (res) => {
        tt.showToast({
          title: "success unlink",
        });
        console.log("unlink success res=" + JSON.stringify(res));
      },
      fail: (error) => {
        tt.showToast({
          title: "failed unlink",
        });
        console.debug("unlink failed error=" + JSON.stringify(error));
      },
    });
  },
  unlinkSync() {
    let saveFilePath = tt.getStorageSync("savedFilePath");
    if (!saveFilePath) {
      return;
    }
    try {
      fileSystemManager.unlinkSync(saveFilePath)
      tt.showToast({
        title: "success unlinkSync",
      });
    } catch (err) {
      console.log(err)
      tt.showToast({
        title: "success unlinkError",
      });
    }
  },
  unzipFile: function (e) {
    const unzipFile = this.data.testCaseItemVisibleList.unzipFile;
    this.setData({
      testCaseItemVisibleList: { unzipFile: !unzipFile },
    });
  },
  inputFilePathForUnzip: function (e) {
    this.data.filePathForUnzip = e.detail.value;
  },
  unzip: function (e) {
    const filePath = this.data.filePathForUnzip;
    const fileName = filePath.substring(filePath.lastIndexOf('/') + 1);
    const lastPath = fileName.substring(0, fileName.lastIndexOf('.'));
    console.log("解压 filePath=" + filePath + " lastItem=" + lastPath);
    tt.getFileSystemManager().unzip({
      zipFilePath: filePath,
      targetPath: `ttfile://user/${lastPath}`,
      success: (res) => {
        tt.showToast({
          title: "success",
        });
        console.log("unzip success res=" + JSON.stringify(res));
      },
      fail: (error) => {
        console.log(error)
        tt.showToast({
          title: "failed",
        });
        console.debug("unzip failed error=" + JSON.stringify(error));
      },
    });
  },
  readFile() {
    if (!this.checkTestFile()) {
      return
    }
    fileSystemManager.readFile({
      filePath: this.data.tempFilePath,
      encoding: 'utf8',
      success(res) {
        console.log(res.data)
        tt.showToast({
          title: "readFile success",
        });
      },
      fail(error) {
        console.log(error)
        tt.showToast({
          title: "readFile error",
        });
      }
    })
  },
  readFileSync() {
    if (!this.checkTestFile()) {
      return
    }
    try {
      const data = fileSystemManager.readFileSync(this.data.tempFilePath)
      console.log(data)
      tt.showToast({
        title: "readFileSync success",
      });
    } catch (error) {
      onsole.log(error)
      tt.showToast({
        title: "readFileSync error",
      });
    }
  },
  stat() {
    if (!this.checkTestFile()) {
      return
    }
    fileSystemManager.stat({
      path: this.data.tempFilePath,
      success(res) {
        tt.showModal({
          content: `是否是文件:${res.stat.isFile()}\n是否是目录:${res.stat.isDirectory()}`
        })
      },
      fail(error) {
        onsole.log(error)
        tt.showToast({
          title: 'stat fail'
        })
      }
    })
  },
  statSync() {
    if (!this.checkTestFile()) {
      return
    }
    try {
      const stat = fileSystemManager.statSync(this.data.tempFilePath)
      tt.showModal({
        content: `是否是文件:${stat.isFile()}\n是否是目录:${stat.isDirectory()}`
      })
    } catch (error) {
      console.log(error)
      tt.showToast({
        title: 'statSync fail'
      })
    }
  },
  writeFile() {
    fileSystemManager.writeFile({
      filePath: writeFilePath,
      encoding: 'utf8',
      data: 'example content',
      success(res) {
        tt.showToast({
          title: 'writeFile success'
        })
      },
      fail(err) {
        tt.showModal({
          content: `${JSON.stringify(err)}`
        })
      }
    })
  },
  writeFileSync() {
    try {
      fileSystemManager.writeFileSync(writeFilePath, 'example content', 'utf8')
      const data = fileSystemManager.readFileSync(writeFilePath);
      console.log(data)
      tt.showToast({
        title: 'writeFileSync success'
      })
    } catch (error) {
      console.log(error)
      tt.showToast({
        title: 'writeFileSync error'
      })
    }
  }
});
