var API = 'http://192.168.1.7:8000'

function sreq(method, path, data) {
  return new Promise(function(resolve, reject) {
    wx.request({
      url: API + path, method: method, data: data, timeout: 10000,
      header: { 'Content-Type': 'application/json' },
      success: function(r) { r.statusCode === 200 ? resolve(r.data) : reject(r) },
      fail: reject
    })
  })
}

Page({
  data: {
    keywords: [],
    brands: [],
    notifyEnabled: true,
    alerts: [],
    alertCount: 0,
    keywordList: [],
    brandList: [],
    _rawKeywords: ['零添加', '有机酱油', '减盐', '生抽', '老抽', '蚝油'],
    _rawBrands: ['海天', '千禾', '李锦记', '厨邦', '加加'],
  },

  onLoad: function() {
    this.initLists()
    this.loadSubscription()
    this.checkAlerts()
  },

  onShow: function() { this.checkAlerts() },

  initLists: function() {
    var self = this
    this.setData({
      keywordList: this.data._rawKeywords.map(function(k) {
        return { name: k, selected: false }
      }),
      brandList: this.data._rawBrands.map(function(b) {
        return { name: b, selected: false }
      }),
    })
  },

  _refreshLists: function() {
    var keys = this.data.keywords
    var brs = this.data.brands
    this.setData({
      keywordList: this.data._rawKeywords.map(function(k) {
        return { name: k, selected: keys.indexOf(k) > -1 }
      }),
      brandList: this.data._rawBrands.map(function(b) {
        return { name: b, selected: brs.indexOf(b) > -1 }
      }),
    })
  },

  async loadSubscription() {
    try {
      var sub = await sreq('GET', '/api/notify/subscription')
      this.setData({
        keywords: sub.keywords || [],
        brands: sub.brands || [],
        notifyEnabled: sub.notify_enabled !== false,
      })
      this._refreshLists()
    } catch(e) { console.error('加载订阅失败', e) }
  },

  async checkAlerts() {
    try {
      var res = await sreq('GET', '/api/notify/alerts')
      this.setData({ alerts: res.alerts || [], alertCount: res.count || 0 })
    } catch(e) {}
  },

  toggleKeyword: function(e) {
    var kw = e.currentTarget.dataset.value
    var list = this.data.keywords.slice()
    var idx = list.indexOf(kw)
    if (idx > -1) { list.splice(idx, 1) }
    else { list.push(kw) }
    this.setData({ keywords: list })
    this._refreshLists()
    sreq('POST', '/api/notify/subscription', {
      keywords: list, brands: this.data.brands, notify_enabled: this.data.notifyEnabled
    }).catch(function(){})
  },

  toggleBrand: function(e) {
    var brand = e.currentTarget.dataset.value
    var list = this.data.brands.slice()
    var idx = list.indexOf(brand)
    if (idx > -1) { list.splice(idx, 1) }
    else { list.push(brand) }
    this.setData({ brands: list })
    this._refreshLists()
    sreq('POST', '/api/notify/subscription', {
      keywords: this.data.keywords, brands: list, notify_enabled: this.data.notifyEnabled
    }).catch(function(){})
  },

  toggleNotify: function() {
    var enabled = !this.data.notifyEnabled
    this.setData({ notifyEnabled: enabled })
    sreq('POST', '/api/notify/subscription', {
      keywords: this.data.keywords, brands: this.data.brands, notify_enabled: enabled
    }).catch(function(){})
  },

  manualCheck: function() {
    var self = this
    wx.showLoading({ title: '检测中...' })
    sreq('GET', '/api/notify/check').then(function() {
      self.checkAlerts()
      wx.hideLoading()
      wx.showToast({ title: '检测完成', icon: 'success' })
    }).catch(function() { wx.hideLoading() })
  },

  navToProduct: function(e) {
    var id = e.currentTarget.dataset.id
    if (id) wx.navigateTo({ url: '/pages/product-detail/product-detail?id=' + id })
  },
})
