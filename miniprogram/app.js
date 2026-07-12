App({
  globalData: {
    apiBase: 'http://localhost:8000',
    userInfo: null,
  },
  onLaunch() {
    wx.getSystemInfo({
      success: (res) => {
        this.globalData.systemInfo = res
      }
    })
  }
})
