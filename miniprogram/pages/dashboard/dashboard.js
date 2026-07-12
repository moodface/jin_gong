// 营销战情室 - CSS 可视化 (无需 ECharts，兼容性最佳)
var api = require('../../utils/api')

Page({
  data: {
    totalGMV: '',
    gmvGrowthText: '',
    gmvGrowthUp: true,
    alertCount: 0,
    updateTime: '',
    platformData: [],
    sentimentData: [],
    gmvTrend: [],
    brandList: [],
    alerts: [],
    loading: true,
    showContent: false,
    error: '',
  },

  onLoad: function() { this.loadData() },
  onPullDownRefresh: function() {
    this.loadData().then(function() { wx.stopPullDownRefresh() })
  },

  async loadData() {
    this.setData({ loading: true, error: '', showContent: false })
    var data
    try { data = await api.getDashboard() }
    catch (e) {
      this.setData({ loading: false, error: '数据加载失败，请确认后端已启动' })
      return
    }
    var alerts = []
    try { if (data.alert_count > 0) alerts = await api.getAlerts() || [] } catch (e) {}

    // ---- GMV 趋势 ----
    var maxGmv = Math.max.apply(null, data.gmv_trend.map(function(i) { return i.value })) || 1
    var gmvTrend = data.gmv_trend.map(function(item) {
      return {
        date: item.date.substring(3),
        displayValue: (item.value / 10000).toFixed(1) + '万',
        pct: Math.round(item.value / maxGmv * 100),
      }
    })
    var latest = gmvTrend.length ? data.gmv_trend[gmvTrend.length - 1].value : 0
    var prev = gmvTrend.length > 1 ? data.gmv_trend[gmvTrend.length - 2].value : latest
    var growth = ((latest - prev) / (prev || 1) * 100).toFixed(1)
    var growthUp = parseFloat(growth) >= 0
    var gmvGrowthText = (growthUp ? '+' : '') + growth + '%'

    // ---- 平台流量 ----
    var maxTraffic = Math.max.apply(null, data.platform_traffic.map(function(i) { return i.count })) || 1
    var platformData = data.platform_traffic.map(function(item) {
      var barPct = Math.round(item.count / maxTraffic * 100)
      var color = item.platform === '抖音' ? '#111' : item.platform === '小红书' ? '#FF2442' : item.platform === '天猫' ? '#FF0036' : '#E3312B'
      var icon = item.platform === '抖音' ? '🎵' : item.platform === '小红书' ? '📕' : item.platform === '天猫' ? '🐱' : '🐶'
      return { platform: item.platform, count: item.count, ratio: item.ratio, barPct: barPct, color: color, icon: icon }
    })

    // ---- 竞品价格 ----
    var brands = ['海天', '千禾', '李锦记', '厨邦', '加加']
    var brandPrices = brands.map(function(b) {
      var items = data.competitor_prices.filter(function(i) { return i.brand === b })
      return items.length ? (items.reduce(function(s, i) { return s + i.price }, 0) / items.length).toFixed(1) : 0
    })
    var maxPrice = Math.max.apply(null, brandPrices.map(Number)) || 1
    var brandList = brands.map(function(brand, idx) {
      var items = data.competitor_prices.filter(function(i) { return i.brand === brand })
      var avgPrice = brandPrices[idx]
      var barPct = Math.round(parseFloat(avgPrice) / maxPrice * 80)
      var products = items.map(function(i) { return i.product })
      return { brand: brand, avgPrice: avgPrice, barPct: barPct, products: products }
    })

    // ---- 舆情 ----
    var sentimentData = data.sentiment_trend.map(function(item) {
      return {
        keyword: item.keyword, mentions: item.mentions,
        pos: Math.round(item.positive || 0),
        neu: Math.round(item.neutral || 0),
        neg: Math.round(item.negative || 0),
      }
    })

    this.setData({
      totalGMV: (data.total_gmv / 10000).toFixed(0),
      gmvGrowthText: gmvGrowthText, gmvGrowthUp: growthUp,
      alertCount: data.alert_count, updateTime: data.update_time,
      platformData: platformData, sentimentData: sentimentData,
      gmvTrend: gmvTrend, brandList: brandList, alerts: alerts.slice(0, 5),
      loading: false, showContent: true,
    })
  },

  refresh: function() { this.loadData() },

  onAlertTap: function(e) {
    var id = e.currentTarget.dataset.id
    var url = e.currentTarget.dataset.url
    if (id) {
      wx.navigateTo({ url: '/pages/product-detail/product-detail?id=' + id })
    }
  },
})
