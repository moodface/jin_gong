const app = getApp()

Page({
  data: {
    item: null,
    loading: true,
    maxPrice: 1,
  },

  onLoad(options) {
    const itemId = options.id
    if (itemId) {
      this.loadDetail(itemId)
    }
  },

  async loadDetail(itemId) {
    this.setData({ loading: true })
    try {
      const res = await this._request(`/api/monitor/competitor/${itemId}`)
      const maxPrice = Math.max(
        ...(res.price_history || []).map(p => p.price),
        ...(res.same_category || []).map(c => c.price || 0),
        1
      )
      this.setData({ item: res, maxPrice, loading: false })
    } catch (e) {
      console.error('加载详情失败', e)
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  _request(path) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: `http://192.168.1.7:8000${path}`,
        timeout: 10000,
        success(res) {
          if (res.statusCode === 200) resolve(res.data)
          else reject(res)
        },
        fail: reject,
      })
    })
  },

  viewCompetitor(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/product-detail/product-detail?id=${id}` })
  },

  openSourceUrl(e) {
    const url = e.currentTarget.dataset.url
    if (url) {
      wx.showModal({
        title: '跳转到数据来源',
        content: '将打开外部链接查看原始数据',
        success: function(res) {
          if (res.confirm) {
            wx.setClipboardData({ data: url, success: function() {
              wx.showToast({ title: '链接已复制，请到浏览器打开', icon: 'none', duration: 3000 })
            }})
          }
        }
      })
    } else {
      wx.showToast({ title: '当前为模拟数据，无外部来源', icon: 'none' })
    }
  },
})
