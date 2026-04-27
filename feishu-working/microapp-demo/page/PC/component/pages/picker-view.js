const contentBehavior = require('../../common/component/Content/content-behavior')

const date = new Date()
const years = []
const months = []
const days = []

for (let i = 1990; i <= date.getFullYear(); i++) {
	years.push(i)
}

for (let i = 1; i <= 12; i++) {
	months.push(i)
}

for (let i = 1; i <= 31; i++) {
	days.push(i)
}

Component({
  behaviors: [contentBehavior],
  relations: {
    '../../common/component/Content/Content': {
      type: 'parent',
    }
  },
  data: {
		years: years,
		year: date.getFullYear(),
		months: months,
		month: 2,
		days: days,
		day: 2,
		year: date.getFullYear(),
		value: [9999, 1, 1],
	},
  methods: {
    bindChange: function (e) {
      const val = e.detail.value
      this.setData({
        year: this.data.years[val[0]],
        month: this.data.months[val[1]],
        day: this.data.days[val[2]]
      })
    }
  }
})