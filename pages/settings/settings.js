const app = getApp()

Page({
  data: {
    userInfo: {}
  },

  onLoad() {
    this.getUserInfo()
  },

  onShow() {
    this.getUserInfo()
  },

  getUserInfo() {
    // 从全局获取用户信息
    const userInfo = app.globalData.userInfo
    console.log('全局用户信息:', app.globalData.userInfo)
    
    // 从存储获取用户信息
    const storageUserInfo = wx.getStorageSync('userInfo')
    console.log('存储用户信息:', storageUserInfo)
    
    if (userInfo) {
      this.setData({
        userInfo: userInfo
      })
    } else if (storageUserInfo) {
      this.setData({
        userInfo: storageUserInfo
      })
      // 同步到全局数据
      app.globalData.userInfo = storageUserInfo
    }

    // 打印当前页面的数据
    console.log('当前页面数据:', this.data.userInfo)
  },

  handleAccount() {
    wx.navigateTo({
      url: '/pages/ai-customization/ai-customization',
    })
  },

  handlePrivacy() {
    wx.navigateTo({
      url: '/pages/privacy/privacy',
    })
  },

  handleNotification() {
    wx.getSetting({
      success: (res) => {
        if (!res.authSetting['scope.notifications']) {
          wx.requestSubscribeMessage({
            tmplIds: ['your_template_id'], // 需要替换为您的模板ID
            success: (res) => {
              wx.showToast({
                title: '通知已开启',
                icon: 'success'
              })
            },
            fail: (err) => {
              wx.showToast({
                title: '请在系统设置中开启通知权限',
                icon: 'none'
              })
            }
          })
        } else {
          wx.openSetting({
            success: (res) => {
              console.log('通知设置状态：', res.authSetting['scope.notifications'])
            }
          })
        }
      }
    })
  },

  handleAbout() {
    wx.navigateTo({
      url: '/pages/about/about'
    })
  },

  handleAICustomization() {
    wx.switchTab({
      url: '/pages/ai-customization/ai-customization'
    })
  },

  handleClearCache() {
    wx.showModal({
      title: '清除缓存',
      content: '确定要清除所有缓存数据吗？',
      success: (res) => {
        if (res.confirm) {
          wx.clearStorage({
            success: () => {
              wx.showToast({
                title: '缓存已清除',
                icon: 'success'
              })
            }
          })
        }
      }
    })
  },

  handleFeedback() {
    wx.navigateTo({
      url: '/pages/feedback/feedback'
    })
  },

  handleLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          // 清除本地存储的用户信息
          wx.removeStorageSync('userInfo')
          wx.removeStorageSync('token')
          
          // 跳转到登录页
          wx.reLaunch({
            url: '/pages/login/login'
          })
        }
      }
    })
  }
}) 