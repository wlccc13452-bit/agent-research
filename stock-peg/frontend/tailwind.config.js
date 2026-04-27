/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 自定义股票涨跌颜色
        'stock-up': '#ef4444',  // 红色-涨
        'stock-down': '#22c55e', // 绿色-跌
      },
    },
  },
  plugins: [],
}
