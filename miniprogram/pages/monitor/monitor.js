var api = require('../../utils/api')

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

  onLoad: function() {
    this.switchTab({ currentTarget: { dataset: { index: 0 } } })
  },

  switchTab: function(e) {
    var i = e.currentTarget.dataset.index
    this.setData({ tabIndex: i, loading: true })
    var loaders = [this.loadCompetitors, this.loadSentiments, this.loadAlerts, this.loadTasks]
    loaders[i].call(this)
  },

  async loadCompetitors() {
    try {
      var data = await api.getCompetitors()
      var list = data.map(function(item) {
        var urls = { '京东': 'https://search.jd.com/Search?keyword=', '天猫': 'https://list.tmall.com/search_product.htm?q=', '抖音': 'https://www.douyin.com/search/', '小红书': 'https://www.xiaohongshu.com/search_result?keyword=' }
        return {
          id: item.id, brand: item.brand, platform: item.platform,
          product_name: item.product_name, price: item.price,
          promo_info: item.promo_info, rating: item.rating,
          review_count: item.review_count, update_time: item.update_time,
          data_source: item.data_source,
          _sourceTag: item.data_source === '真实API' ? 'real' : 'market',
          _updateShort: (item.update_time || '').substring(5, 16),
          _priceDisplay: item.price ? item.price.toFixed(1) : '0.0',
          _clickable: item.data_source === '真实API' || item.data_source === '市场参考价',
          _sourceUrl: (urls[item.platform] || '') + (item.product_name || ''),
        }
      })
      this.setData({ competitors: list, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  async loadSentiments() {
    try {
      var data = await api.getSentiment()
      var list = data.map(function(item) {
        return {
          id: item.id, keyword: item.keyword, platform: item.platform,
          mention_count: item.mention_count, data_source: item.data_source,
          positive_ratio: item.positive_ratio, negative_ratio: item.negative_ratio,
          _sourceTag: 'ai',
          _posW: Math.round(item.positive_ratio * 100),
          _negW: Math.round(item.negative_ratio * 100),
          _posPct: Math.round(item.positive_ratio * 100),
          _negPct: Math.round(item.negative_ratio * 100),
        }
      })
      this.setData({ sentiments: list, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  async loadAlerts() {
    try {
      var data = await api.getAlerts()
      this.setData({ alerts: data, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  async loadTasks() {
    try {
      var data = await api.getTasks()
      var list = data.map(function(item) {
        var st = '运行中'
        if (item.status === 'completed') st = '完成'
        else if (item.status === 'failed') st = '失败'
        else if (item.status === 'partial') st = '部分成功'
        return {
          id: item.id, platform: item.platform, status: item.status,
          start_time: item.start_time, records_fetched: item.records_fetched,
          _statusText: st,
        }
      })
      this.setData({ tasks: list, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  async triggerScrape(e) {
    var p = e.currentTarget.dataset.platform || 'all'
    wx.showLoading({ title: '已提交...' })
    try {
      await api.triggerScrape(p)
      wx.showToast({ title: '后台执行中', icon: 'success' })
      var self = this
      setTimeout(function() { self.loadTasks() }, 3000)
    } catch (e) {
      wx.showToast({ title: '提交失败', icon: 'error' })
    }
    wx.hideLoading()
  },

  viewProduct: function(e) {
    var id = e.currentTarget.dataset.id
    if (id) wx.navigateTo({ url: '/subpkg/pages/product-detail/product-detail?id=' + id })
  },

  openSourceUrl: function(e) {
    var url = e.currentTarget.dataset.url
    if (url) {
      wx.setClipboardData({
        data: url,
        success: function() { wx.showToast({ title: '链接已复制', icon: 'none', duration: 2500 }) }
      })
    } else {
      wx.showToast({ title: '模拟数据', icon: 'none' })
    }
  },
})
