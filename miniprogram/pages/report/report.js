var api = require('../../utils/api')

Page({
  data: { activeReport: null, sections: [], reportHtml: '', history: [], generating: false },
  onLoad: function() { this.loadHistory() },
  async loadHistory() {
    try { var h = await api.getReportHistory(); this.setData({ history: h }) } catch (e) {}
  },
  async generateReport(e) {
    var type = e.currentTarget.dataset.type || 'daily'
    this.setData({ generating: true, activeReport: type })
    try {
      var result = await api.generateReport(type)
      var sections = result.sections || []
      if (!sections.length) sections = [{ title: '报告内容', icon: '📄', items: [(result.content || '').replace(/<[^>]+>/g,' ').substring(0, 500)] }]
      this.setData({ sections: sections, reportHtml: result.content, generating: false })
      this.loadHistory()
      wx.showToast({ title: '报告生成成功', icon: 'success' })
    } catch (e) {
      this.setData({ generating: false })
      wx.showToast({ title: '生成失败，请确认后端已启动', icon: 'none' })
    }
  },
  async viewHistory(e) {
    var item = e.currentTarget.dataset.item
    wx.showLoading({ title: '加载中...' })
    try {
      var detail = await api.getReportDetail(item.id)
      var sections = detail.sections
      if (!sections || !sections.length) {
        sections = [{ title: '报告内容', icon: '📄', items: [(detail.content || '').replace(/<[^>]+>/g,' ').substring(0, 500)] }]
      }
      this.setData({ activeReport: item.type, sections: sections, reportHtml: detail.content || item.content || '' })
    } catch (e) {
      this.setData({ activeReport: item.type, sections: [{ title: '报告内容', icon: '📄', items: [(item.content || '').substring(0, 200)] }], reportHtml: item.content || '' })
    }
    wx.hideLoading()
  },
  onPullDownRefresh: function() { this.loadHistory().then(function() { wx.stopPullDownRefresh() }) },
})
