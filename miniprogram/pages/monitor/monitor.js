const api = require('../../utils/api')

Page({
  data: {
    tabIndex: 0,
    tabs: ['竞品监控', '舆情分析', '预警信息', '爬取任务'],
    competitors: [],
    sentiments: [],
    alerts: [],
    tasks: [],
    loading: true,
  },

  onLoad() {
    this.switchTab({ currentTarget: { dataset: { index: 0 } } })
  },

  switchTab(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ tabIndex: idx, loading: true })
    const loaders = [this.loadCompetitors, this.loadSentiments, this.loadAlerts, this.loadTasks]
    loaders[idx].call(this)
  },

  async loadCompetitors() {
    try {
      const data = await api.getCompetitors()
      const competitors = data.map(item => ({
        ...item,
        _sourceTag: item.data_source === '真实API' ? 'real' : item.data_source === '市场参考价' ? 'market' : 'ai',
        _updateShort: (item.update_time || '').substring(5, 16),
        _priceDisplay: item.price ? item.price.toFixed(1) : '0.0',
        _clickable: item.data_source === '真实API' || item.data_source === '市场参考价',
        _sourceUrl: (function() {
          var urls = { '京东': 'https://search.jd.com/Search?keyword=', '天猫': 'https://list.tmall.com/search_product.htm?q=', '抖音': 'https://www.douyin.com/search/', '小红书': 'https://www.xiaohongshu.com/search_result?keyword=' }
          return (urls[item.platform] || '') + (item.product_name || '')
        })(),
      }))
      this.setData({ competitors, loading: false })
    } catch (e) {
      console.error(e)
      this.setData({ loading: false })
    }
  },

  async loadSentiments() {
    try {
      const data = await api.getSentiment()
      const sentiments = data.map(item => ({
        ...item,
        _sourceTag: item.data_source === '真实API' ? 'real' : 'ai',
        _posW: Math.round(item.positive_ratio * 100),
        _neuW: Math.round(item.neutral_ratio * 100),
        _negW: Math.round(item.negative_ratio * 100),
        _posPct: Math.round(item.positive_ratio * 100),
        _negPct: Math.round(item.negative_ratio * 100),
      }))
      this.setData({ sentiments, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  async loadAlerts() {
    try {
      const data = await api.getAlerts()
      this.setData({ alerts: data, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  async loadTasks() {
    try {
      const data = await api.getTasks()
      const tasks = data.map(item => {
        let statusText = '运行中'
        if (item.status === 'completed') statusText = '完成'
        else if (item.status === 'failed') statusText = '失败'
        else if (item.status === 'partial') statusText = '部分成功'
        return { ...item, _statusText: statusText }
      })
      this.setData({ tasks, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  async triggerScrape(e) {
    const platform = e.currentTarget.dataset.platform || '微博+百度'
    wx.showLoading({ title: '任务已提交...' })
    try {
      await api.triggerScrape(platform)
      wx.showToast({ title: '后台执行中，稍候刷新', icon: 'success' })
      setTimeout(() => this.loadTasks(), 3000)
      setTimeout(() => this.loadCompetitors(), 3000)
    } catch (e) {
      wx.showToast({ title: '提交失败', icon: 'error' })
    }
    wx.hideLoading()
  },

  async fetchThirdParty(e) {
    const source = e.currentTarget.dataset.platform
    wx.showLoading({ title: '查询中...' })
    try {
      const data = await api.getThirdParty(source)
      console.log('第三方数据:', data)
      wx.showModal({
        title: `${source} 数据`,
        content: `数据源: ${data.source}\n状态: ${data.auth_status}`,
        showCancel: false,
      })
    } catch (e) {
      wx.showToast({ title: '查询失败', icon: 'error' })
    }
    wx.hideLoading()
  },

  onPullDownRefresh() {
    const loaders = [this.loadCompetitors, this.loadSentiments, this.loadAlerts, this.loadTasks]
    loaders[this.data.tabIndex].call(this).then(() => wx.stopPullDownRefresh())
  },

  viewProduct(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/product-detail/product-detail?id=${id}` })
  },

  openSourceUrl(e) {
    e.stopPropagation && e.stopPropagation()
    const url = e.currentTarget.dataset.url
    if (url) {
      wx.setClipboardData({ data: url, success: function() {
        wx.showToast({ title: '链接已复制，请到浏览器打开', icon: 'none', duration: 2500 })
      }})
    } else {
      wx.showToast({ title: '当前为模拟数据', icon: 'none' })
    }
  },
})
