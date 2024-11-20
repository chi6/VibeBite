import api from '../../services/api';

Page({
  data: {
    isLoading: false
  },

  handleWechatLogin(e) {
    if (this.data.isLoading) return;
    
    this.setData({ isLoading: true });

    if (e.detail.userInfo) {
      // 用户同意授权
      wx.login({
        success: (res) => {
          if (res.code) {
            // 调用登录接口
            api.login(res.code, e.detail.userInfo)
              .then(loginResult => {
                if (loginResult.success) {
                  // 存储用户信息和token
                  wx.setStorageSync('userInfo', loginResult.userInfo);
                  wx.setStorageSync('token', loginResult.token);
                  
                  // 显示成功提示
                  wx.showToast({
                    title: '登录成功',
                    icon: 'success',
                    duration: 1500
                  });

                  // 延迟跳转到首页
                  setTimeout(() => {
                    wx.reLaunch({
                      url: '/pages/index/index'
                    });
                  }, 1500);
                } else {
                  throw new Error('登录失败');
                }
              })
              .catch(error => {
                console.error('登录失败:', error);
                wx.showToast({
                  title: '登录失败，请重试',
                  icon: 'none'
                });
              })
              .finally(() => {
                this.setData({ isLoading: false });
              });
          } else {
            wx.showToast({
              title: '获取用户信息失败',
              icon: 'none'
            });
            this.setData({ isLoading: false });
          }
        },
        fail: (error) => {
          console.error('wx.login 失败:', error);
          wx.showToast({
            title: '登录失败，请重试',
            icon: 'none'
          });
          this.setData({ isLoading: false });
        }
      });
    } else {
      // 用户拒绝授权
      wx.showToast({
        title: '需要授权才能使用',
        icon: 'none'
      });
      this.setData({ isLoading: false });
    }
  },

  showPrivacyPolicy() {
    wx.navigateTo({
      url: '/pages/privacy/privacy'
    });
  }
});
