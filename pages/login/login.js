import api from '../../services/api';

Page({
  data: {
    isLoading: false
  },

  handleWechatLogin(e) {
    if (this.data.isLoading) return;
    
    this.setData({ isLoading: true });

    if (e.detail.userInfo) {
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

                  // 检查用户是否已经填写过餐饮喜好
                  api.getPreferences()
                    .then(preferences => {
                      console.log('preferences', preferences, 'nickname', preferences.data.preferences.nickname);
                      if (preferences && preferences.data.preferences.nickname) {
                        // 如果已经填写过，直接跳转到首页
                        wx.reLaunch({
                          url: '/pages/index/index'
                        });
                      } else {
                        // 否则跳转到餐饮喜好填写页面
                        wx.navigateTo({
                          url: '/pages/preferences/preferences'
                        });
                      }
                    })
                    .catch(error => {
                      console.error('获取餐饮喜好信息失败:', error);
                      wx.showToast({
                        title: '获取餐饮喜好信息失败',
                        icon: 'none'
                      });
                    });
                } else {
                  wx.showToast({
                    title: '登录失败，请重试',
                    icon: 'none'
                  });
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
