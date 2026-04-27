import i18n from '../../../i18n/index'
const iPicker = i18n.picker

var ms = [
	[// 0
		'plant',
		'animal'
	],
	[// 1
		[// 1 0
			'tree',
			'grass',
			'vine',
			'flower',
			'leaf'
		],
		[// 1 1
			'fish',
			'amphibian',
			'reptile',
			'test'
		]
	],
	[// 2
		[// 2 0
			['pine', 'sycamore'],
			['rice'],
			['morning glory', 'creeper'],
			['chrysanthemum', 'Overlord flower', 'orchid'],
			['Maple leaf', 'coniferous']
		],
		[// 2 1
			['squid', 'Pike'],
			['frag', 'daxie'],
			['lizard', 'tortoise', 'gecko'],
			[]
		]
	]
];

Page({
	data: {
		array: ['USA', 'China', 'Brasil', 'Japan'],
		index: 0,
		objectArray: [
			{
				id: 0,
				name: 'USA',
				en: 'USA'
			},
			{
				id: 1,
				name: 'China',
				en: 'China'
			},
			{
				id: 2,
				name: 'Brasil',
				en: "Brasil"
			},
			{
				id: 3,
				name: 'Japan',
				en: "Japan"
			}
		],
		objectIndex: 0,
		multiArray: [
			[
				'plant',
				'animal'
			],
			[// 1 0
				'tree',
				'grass',
				'vine',
				'flower',
				'leaf'
			],
			[
				'pine',
				'sycamore'
			],
		],
		multiIndex: [0, 0, 0],
		objectMultiIndex: [0, 0, 0],
		yearDate: '2016',
		monthDate: '2016-09',
		dayDate: '2016-09-01',
		time: '12:01',
		region: ["Beijing", "Beijing", "Chao Yang District"],
		customItem: '--',
		timeStart: '09:01',
		timeEnd: '21:01',
		...iPicker
	},
	topButtopClick() {
		console.log('tappend');
		setTimeout(() => {
			this.setData({
				index: 4,
				array: ['USA', 'China', 'Brasil', 'Japan', 'France'],
				timeStart: "09:03",
				multiIndex: [1, 1, 1]
			})
			console.log('changed');
		}, 5000);
	},
	bindPickerChange: function (e) {
		console.log('picker send value:', e.detail.value)
		this.setData({
			index: e.detail.value
		})
	},
	bindObjectPickerChange: function (e) {
		console.log('picker send value:', e.detail.value)
		this.setData({
			objectIndex: e.detail.value
		})
	},
	bindMultiPickerChange: function (e) {
		console.log('picker send value:', e.detail.value)
		this.setData({
			multiIndex: e.detail.value
		})
	},
	bindMultiPickerColumnChange: function (e) {
		// return;
		console.log('Modified Column:', e.detail.column, '，Value:', e.detail.value);
		var data = {
			multiArray: this.data.multiArray,
			multiIndex: this.data.multiIndex
		};
		switch (e.detail.column) {
			case 0:
				data.multiIndex[0] = e.detail.value;
				data.multiIndex[1] = 0;
				data.multiIndex[2] = 0;

				data.multiArray[1] = ms[1][data.multiIndex[0]];
				data.multiArray[2] = ms[2][data.multiIndex[0]][data.multiIndex[1]];
				break;
			case 1:
				data.multiIndex[1] = e.detail.value;
				data.multiIndex[2] = 0;

				data.multiArray[2] = ms[2][data.multiIndex[0]][data.multiIndex[1]];
				break;
			case 2:
				data.multiIndex[2] = e.detail.value;
				break;
		}
		this.setData(data);
	},
	bindYearDateChange: function (e) {
		console.log('picker send value:', e.detail.value)
		this.setData({
			yearDate: e.detail.value
		})
	},
	bindMonthDateChange: function (e) {
		console.log('picker send value:', e.detail.value)
		this.setData({
			monthDate: e.detail.value
		})
	},
	bindDayDateChange: function (e) {
		console.log('picker send value:', e.detail.value)
		this.setData({
			dayDate: e.detail.value
		})
	},
	bindTimeChange: function (e) {
		console.log('picker send value:', e.detail.value)
		this.setData({
			time: e.detail.value
		})
	},
	bindRegionChange: function (e) {
		console.log('picker send value:', e.detail.value)
		this.setData({
			region: e.detail.value
		})
	}
})
