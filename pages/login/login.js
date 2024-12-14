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
            // 获取openid
            api.request('/api/wx/openid', {
              method: 'POST',
              data: { code: res.code }
            }).then(openidRes => {
              // 获取用户设置
              return Promise.all([
                api.getPreferences(),  // 获取偏好设置
                api.getAISettings()    // 获取AI设置
              ]);
            }).then(([preferences, aiSettings]) => {
              if (preferences.success && aiSettings.success && 
                  preferences.data && aiSettings.data && 
                  aiSettings.data.name) {  // 检查是否已设置AI名字
                // 如果已经设置过AI和偏好，直接跳转到首页
                wx.reLaunch({
                  url: '/pages/index/index'
                });
              } else {
                // 否则跳转到餐饮喜好填写页面
                wx.navigateTo({
                  url: '/pages/preferences/preferences'
                });
              }
            }).catch(error => {
              console.error('检查用户设置失败:', error);
              // 出错时默认跳转到偏好设置页
              wx.navigateTo({
                url: '/pages/preferences/preferences'
              });
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
