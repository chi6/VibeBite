Page({
  onGetUserInfo(e) {
    if (e.detail.userInfo) {
      // 用户同意授权
      wx.login({
        success: (res) => {
          if (res.code) {
            // 发送 res.code 到后端换取 openId, sessionKey, unionId
            // 这里需要调用您的后端 API
            wx.request({
              url: 'https://your-backend-api.com/login', // 替换为你的后端登录API
              method: 'POST',
              data: {
                code: res.code,
                userInfo: e.detail.userInfo
              },
              success: (response) => {
                if (response.statusCode === 200) {
                  // 登录成功，保存token或其他信息
                  wx.setStorageSync('token', response.data.token);
                  wx.navigateTo({
                    url: '/pages/index/index'
                  });
                } else {
                  console.error('登录失败:', response.data.message);
                  wx.showToast({
                    title: '登录失败，请重试',
                    icon: 'none'
                  });
                }
              },
              fail: (err) => {
                console.error('请求失败:', err);
                wx.showToast({
                  title: '网络错误，请重试',
                  icon: 'none'
                });
              }
            });
          } else {
            console.log('登录失败！' + res.errMsg);
            wx.showToast({
              title: '登录失败，请重试',
              icon: 'none'
            });
          }
        }
      });
    } else {
      // 用户拒绝授权
      wx.showToast({
        title: '需要授权才能使用',
        icon: 'none'
      });
    }
  }
})
