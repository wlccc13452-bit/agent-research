import React from 'react'

interface PMRInfo {
  pmr: number
  rating: string
  trend?: string
  suggestion?: string
}

interface PMRDataTableProps {
  data: {
    MA5?: PMRInfo
    MA10?: PMRInfo
    MA20?: PMRInfo
    MA30?: PMRInfo
    MA60?: PMRInfo
  }
}

const getRatingColor = (rating: string): string => {
  switch (rating) {
    case '很强':
      return 'text-red-600 font-bold'
    case '强':
      return 'text-orange-600 font-semibold'
    case '中性偏强':
      return 'text-blue-600'
    case '中性':
      return 'text-gray-600'
    case '弱':
      return 'text-green-600'
    default:
      return 'text-gray-400'
  }
}

const getRatingBackground = (rating: string): string => {
  switch (rating) {
    case '很强':
      return 'bg-red-50'
    case '强':
      return 'bg-orange-50'
    case '中性偏强':
      return 'bg-blue-50'
    case '中性':
      return 'bg-gray-50'
    case '弱':
      return 'bg-green-50'
    default:
      return 'bg-white'
  }
}

export const PMRDataTable: React.FC<PMRDataTableProps> = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return <div className="text-gray-400 text-center py-4">暂无 PMR 数据</div>
  }

  const periods: Array<keyof PMRDataTableProps['data']> = ['MA5', 'MA10', 'MA20', 'MA30', 'MA60']

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-gray-200">
        <thead>
          <tr className="bg-gradient-to-r from-blue-50 to-indigo-50">
            <th className="border border-gray-200 px-4 py-3 text-left text-sm font-semibold text-gray-700">
              周期
            </th>
            <th className="border border-gray-200 px-4 py-3 text-center text-sm font-semibold text-gray-700">
              PMR 值
            </th>
            <th className="border border-gray-200 px-4 py-3 text-center text-sm font-semibold text-gray-700">
              评级
            </th>
            <th className="border border-gray-200 px-4 py-3 text-left text-sm font-semibold text-gray-700">
              趋势判断
            </th>
            <th className="border border-gray-200 px-4 py-3 text-left text-sm font-semibold text-gray-700">
              操作建议
            </th>
          </tr>
        </thead>
        <tbody>
          {periods.map((period) => {
            const info = data[period]
            if (!info) return null

            return (
              <tr key={period} className={`hover:bg-gray-50 ${getRatingBackground(info.rating)}`}>
                <td className="border border-gray-200 px-4 py-3 text-sm font-medium text-gray-900">
                  {period}
                </td>
                <td className="border border-gray-200 px-4 py-3 text-center text-sm">
                  <span className={getRatingColor(info.rating)}>
                    {info.pmr.toFixed(2)}
                  </span>
                </td>
                <td className="border border-gray-200 px-4 py-3 text-center">
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getRatingColor(
                      info.rating
                    )}`}
                  >
                    {info.rating}
                  </span>
                </td>
                <td className="border border-gray-200 px-4 py-3 text-sm text-gray-700">
                  {info.trend || '-'}
                </td>
                <td className="border border-gray-200 px-4 py-3 text-sm text-gray-600">
                  {info.suggestion || '-'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default PMRDataTable
