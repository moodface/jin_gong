const app = getApp()

// 后端 API 地址 - 根据实际环境修改
const API_BASE = 'http://192.168.1.7:8000'

function request(path, options = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE}${path}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      timeout: 30000,
      success(res) {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          reject(res)
        }
      },
      fail(err) {
        reject(err)
      },
    })
  })
}

module.exports = {
  getDashboard: () => request('/api/dashboard'),
  getCompetitors: () => request('/api/monitor/competitors'),
  getSentiment: () => request('/api/monitor/sentiment'),
  getAlerts: () => request('/api/monitor/alerts'),
  getTasks: () => request('/api/monitor/tasks'),
  triggerScrape: (platform) => request(`/api/monitor/scrape/${platform}`, { method: 'POST' }),
  triggerJdScrape: () => request('/api/monitor/scrape/jd', { method: 'POST' }),
  getThirdParty: (source) => request(`/api/monitor/third-party/${source}`),
  getCleaningDashboard: () => request('/api/cleaning/dashboard'),
  generateReport: (type = 'daily') => request('/api/report/generate', {
    method: 'POST',
    data: { report_type: type },
  }),
  getReportHistory: () => request('/api/report/history'),
  getReportDetail: (id) => request(`/api/report/${id}`),
}
