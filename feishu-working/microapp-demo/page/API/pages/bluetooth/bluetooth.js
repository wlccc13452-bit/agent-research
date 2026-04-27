import i18n from '../../../i18n/index'
const iBluetooth = i18n.bluetooth
Page({
  data: {
    devices: [],
    deviceIndex: 0,
    showDevices: [],
    deviceId: '',

    services: [],
    showServices: [],
    serviceId: '',
    serviceIndex: 0,

    charId: '',
    chars: [],
    charIndex: [],
    showChars: [],
    ...iBluetooth,
  },
  openBluetoothAdapter() {
    tt.openBluetoothAdapter({
      success: () => {
        tt.showModal({ content: iBluetooth.initSuccess })
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      },
    });
  },
  closeBluetoothAdapter() {
    tt.closeBluetoothAdapter({
      success: () => {
        tt.showModal({ content: iBluetooth.closeSuccess });
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      },
    });
  },
  getBluetoothAdapterState() {
    tt.getBluetoothAdapterState({
      success: res => {
        if (!res.available) {
          tt.showModal({ content: iBluetooth.bluetoothNoWork });
          return;
        }
        tt.showModal({ content: JSON.stringify(res) });
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      },
    });
  },
  startBluetoothDevicesDiscovery() {
    tt.startBluetoothDevicesDiscovery({
      allowDuplicatesKey: false,
      success: (res) => {
        tt.showModal({ content: iBluetooth.startDiscoverSuccess + JSON.stringify(res) });
      },
      fail: error => {
        tt.showModal({ content: iBluetooth.startDiscoverFail + JSON.stringify(error) });
      },
    });
  },
  stopBluetoothDevicesDiscovery() {
    tt.stopBluetoothDevicesDiscovery({
      success: () => {
        tt.showModal({ content: iBluetooth.success });
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      },
    });
  },
  getBluetoothDevices() {
    tt.getBluetoothDevices({
      success: res => {
        tt.showModal({ content: JSON.stringify(res) });
        const devices = res.devices.filter(device => device.deviceId);
        const showDevices = devices.map(device => `${device.localName || ''}-${device.deviceId}`);
        this.setData({ devices, showDevices: showDevices });
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      },
    });
  },
  getConnectedBluetoothDevices() {
    tt.getConnectedBluetoothDevices({
      services: [],
      success: res => {
        if (res.devices.length === 0) {
          tt.showModal({ content: iBluetooth.noConnection });
          return;
        }
        tt.showModal({ content: JSON.stringify(res) });
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      },
    });
  },
  // setSpecialData() {
  //   const { devices } = this.data;
  //   const special = devices.filter(device => {
  //     return device.advertisServiceUUIDs[0] === "0000fe3c-0000-1000-8000-00805f9b34fb"
  //   });
  //   tt.connectBLEDevice({
  //     deviceId: special[0].deviceId,
  //     success: res => {
  //       tt.showModal({ content: `连接成功` });
  //       this.setData({
  //         deviceId: special[0].deviceId
  //       });
  //     },
  //     fail: error => {
  //       tt.showModal({ content: JSON.stringify(error) });
  //     },
  //   });
  // },
  connectBLEDevice(e) {
    const { devices } = this.data;
    const index = e.detail.value;
    const device = devices[index];
    tt.connectBLEDevice({
      deviceId: device.deviceId,
      success: res => {
        tt.showModal({ content: `${iBluetooth.connectSuccess}${JSON.stringify(device)}` });
        this.setData({
          deviceId: device.deviceId
        });
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      },
    });
  },
  disconnectBLEDevice() {
    tt.disconnectBLEDevice({
      deviceId: this.data.deviceId,
      success: () => {
        tt.showModal({ content: iBluetooth.disconnectSuccess });
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      },
    });
  },
  setBLEMTU() {
    tt.setBLEMTU({
      deviceId: this.data.deviceId,
      mtu: 200,
      success: () => {
        tt.showModal({ content: 'success' })
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      }
    })
  },
  getBLEDeviceServices() {
    tt.getBLEDeviceServices({
      deviceId: this.data.deviceId,
      success: res => {
        tt.showModal({ content: JSON.stringify(res) });
        this.setData({
          services: res.services,
          showServices: res.services.map(service => `${service.serviceId}`),
        });
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      },
    });
  },
  getBLEDeviceCharacteristics() {
    tt.getBLEDeviceCharacteristics({
      deviceId: this.data.deviceId,
      serviceId: this.data.serviceId,
      success: res => {
        tt.showModal({ content: JSON.stringify(res) });
        this.setData({
          chars: res.characteristics,
          showChars: res.characteristics.map(char => `${char.properties.read} ${char.properties.write} ${char.properties.notify}`)
        });
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      },
    });
  },
  selectCharId(e) {
    const index = e.detail.value;
    const { chars } = this.data;
    this.setData({
      charId: chars[index].characteristicId,
      charIndex: index,
    })
  },
  selectServiceId(e) {
    const index = e.detail.value;
    const { services } = this.data;
    this.setData({
      serviceId: services[index].serviceId,
      serviceIndex: index,
    })
  },
  notifyBLECharacteristicValueChange() {
    tt.notifyBLECharacteristicValueChange({
      state: true,
      deviceId: this.data.deviceId,
      serviceId: this.data.serviceId,
      characteristicId: this.data.charId,
      success: () => {
        //监听特征值变化的事件
        tt.onBLECharacteristicValueChange(res => {
          tt.showModal({ content: iBluetooth.getObserverData + res.value });
        });
        tt.showModal({ content: iBluetooth.observerSuccess });
      },
      fail: error => {
        tt.showModal({ content: iBluetooth.observerFail + JSON.stringify(error) });
      },
    });
  },
  readBLECharacteristicValue() {
    tt.readBLECharacteristicValue({
      deviceId: this.data.deviceId,
      serviceId: this.data.serviceId,
      characteristicId: this.data.charId,
      success: res => {
        tt.showModal({ content: JSON.stringify(res) });
      },
      fail: error => {
        tt.showModal({ content: iBluetooth.readFail + JSON.stringify(error) });
      },
    });
  },
  writeBLECharacteristicValue() {
    tt.writeBLECharacteristicValue({
      deviceId: this.data.deviceId,
      serviceId: this.data.serviceId,
      characteristicId: this.data.charId,
      value: 'FF',
      success: res => {
        tt.showModal({ content: iBluetooth.writeSuccess });
      },
      fail: error => {
        tt.showModal({ content: JSON.stringify(error) });
      },
    });
  },
  offBLECharacteristicValueChange() {
    tt.offBLECharacteristicValueChange();
  },
  bluetoothAdapterStateChange() {
    tt.onBluetoothAdapterStateChange(this.onBluetoothAdapterStateChange);
  },
  onBluetoothAdapterStateChange(res) {
    if (res.error) {
      tt.showModal({ content: JSON.stringify(error) });
    } else {
      tt.showModal({ content: iBluetooth.statusChange + JSON.stringify(res) });
    }
  },
  offBluetoothAdapterStateChange() {
    tt.offBluetoothAdapterStateChange(this.onBluetoothAdapterStateChange);
  },
  BLEConnectionStateChanged() {
    tt.onBLEConnectionStateChange(this.onBLEConnectionStateChanged);
  },
  onBLEConnectionStateChanged(res) {
    if (res.error) {
      tt.showModal({ content: JSON.stringify(error) });
    } else {
      tt.showModal({ content: iBluetooth.connectStatusChange + JSON.stringify(res) });
    }
  },
  offBLEConnectionStateChanged() {
    tt.offBLEConnectionStateChange(this.onBLEConnectionStateChanged);
  },
  onUnload() {
    this.offBLEConnectionStateChanged();
    this.offBLECharacteristicValueChange();
    this.offBluetoothAdapterStateChange();
    this.closeBluetoothAdapter();
  },
})
