const api = require('../../utils/api')

Page({
  data: {
    activeReport: null,
    sections: [],
    reportHtml: '',
    history: [],
    generating: false,
  },

  onLoad() {
    this.loadHistory()
  },

  async loadHistory() {
    try {
      const history = await api.getReportHistory()
      this.setData({ history })
    } catch (e) {
      console.error('加载历史报告失败', e)
    }
  },

  async generateReport(e) {
    const type = e.currentTarget.dataset.type || 'daily'
    this.setData({ generating: true, activeReport: type })

    try {
      const result = await api.generateReport(type)
      const sections = result.sections || this._parseHtmlToSections(result.content)

      this.setData({
        sections,
        reportHtml: result.content,
        generating: false,
      })
      this.loadHistory()
      wx.showToast({ title: '报告生成成功', icon: 'success' })
    } catch (e) {
      console.error('报告生成失败', e)
      this.setData({ generating: false })
      wx.showToast({ title: '生成失败，请确认后端已启动', icon: 'none' })
    }
  },

  _parseHtmlToSections(html) {
    const sections = []
    const divRegex = /<h[23][^>]*>(.*?)<\/h[23]>/gi
    const liRegex = /<li[^>]*>(.*?)<\/li>/gi
    const cleaned = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
    sections.push({
      title: '报告内容',
      icon: '📄',
      items: [cleaned.substring(0, 500)],
    })
    return sections
  },

  async viewHistory(e) {
    const item = e.currentTarget.dataset.item
    wx.showLoading({ title: '加载中...' })
    try {
      const detail = await api.getReportDetail(item.id)
      // 优先使用后端存储的 structured sections
      let sections = detail.sections
      if (!sections || sections.length === 0) {
        sections = this._parseHtmlToSections(detail.content || '')
      }
      this.setData({
        activeReport: item.type,
        sections,
        reportHtml: detail.content || item.content || '',
      })
    } catch (e) {
      const sections = this._parseHtmlToSections(item.content || '')
      this.setData({
        activeReport: item.type,
        sections,
        reportHtml: item.content || '',
      })
    }
    wx.hideLoading()
  },

  getSectionColor(index) {
    const colors = ['#C8102E', '#FF6B35', '#4ECDC4', '#722ED1', '#FAAD14']
    return colors[index % colors.length]
  },

  onPullDownRefresh() {
    this.loadHistory().then(() => wx.stopPullDownRefresh())
  },
})
