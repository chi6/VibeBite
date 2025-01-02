// app.js

App({
  globalData: {
    userInfo: null
  },
  
  onLaunch() {
    // 启动时从本地存储恢复用户信息
    const userInfo = wx.getStorageSync('userInfo')
    if (userInfo) {
      this.globalData.userInfo = userInfo
    }
  }
})
