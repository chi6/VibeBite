Page({
  onGetUserInfo(e) {
    if (e.detail.userInfo) {
      // 用户同意授权
      wx.login({
        success: (res) => {
          if (res.code) {
            // 发送 res.code 到后端换取 openId, sessionKey, unionId
            // 这里需要调用您的后端 API
            wx.navigateTo({
              url: '/pages/index/index'
            })
          } else {
            console.log('登录失败！' + res.errMsg)
          }
        }
      })
    } else {
      // 用户拒绝授权
      wx.showToast({
        title: '需要授权才能使用',
        icon: 'none'
      })
    }
  }
})
