var API = 'http://139.155.99.106:8000'

function request(path, method, data) {
  method = method || 'GET'
  return new Promise(function(resolve, reject) {
    wx.request({
      url: API + path, method: method, data: data, timeout: 10000,
      header: { 'Content-Type': 'application/json' },
      success: function(r) {
        if (r.statusCode === 200) resolve(r.data)
        else reject(r)
      },
      fail: reject,
    })
  })
}

Page({
  data: {
    tabIdx: 0,
    tabs: ['清洗看板', '归因分析', '数据血缘'],
    cleaning: null,
    attribution: null,
    lineage: [],
    showAll: false,
    loading: true,
  },

  onLoad: function() {
    this.switchTab({ currentTarget: { dataset: { index: 0 } } })
  },

  switchTab: function(e) {
    var i = e.currentTarget.dataset.index
    this.setData({ tabIdx: i, loading: true })
    var self = this
    if (i === 0) {
      request('/api/data-factory/cleaning-full').then(function(d) {
        self.setData({ cleaning: d, loading: false })
      }).catch(function() { self.setData({ loading: false }) })
    } else if (i === 1) {
      request('/api/data-factory/attribution').then(function(d) {
        self.setData({ attribution: d, loading: false })
      }).catch(function() { self.setData({ loading: false }) })
    } else {
      request('/api/data-factory/lineage-samples').then(function(d) {
        self.setData({ lineage: d.samples || [], loading: false })
      }).catch(function() { self.setData({ loading: false }) })
    }
  },

  onPullDownRefresh: function() {
    var self = this
    this.switchTab({ currentTarget: { dataset: { index: this.data.tabIdx } } })
    setTimeout(function() { wx.stopPullDownRefresh() }, 500)
  },

  loadAllLineage: function() {
    var self = this
    wx.showLoading({ title: '加载中...' })
    request('/api/data-factory/lineage-samples?limit=100').then(function(d) {
      self.setData({ lineage: d.samples || [], showAll: true })
      wx.hideLoading()
    }).catch(function() {
      wx.showToast({ title: '加载失败', icon: 'none' })
      wx.hideLoading()
    })
  },
})
