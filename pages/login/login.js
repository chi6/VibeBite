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
            // 先进行登录
            api.login(res.code, e.detail.userInfo)
              .then(loginRes => {
                if (loginRes.success) {
                  // 登录成功后，获取用户设置
                  return Promise.all([
                    api.getAISettings()
                  ]);
                } else {
                  throw new Error('登录失败');
                }
              })
              .then(([aiSettings]) => {
                if (aiSettings.success && aiSettings.data && aiSettings.data.name !== "默认助手") {
                    wx.navigateTo({
                      url: '/pages/preferences/preferences'
                    }); 
                } else {
                    wx.navigateTo({
                      url: '/pages/ai-customization/ai-customization'
                    });
                }
              })
              .catch(error => {
                console.error('登录或检查用户设置失败:', error);
                wx.showToast({
                  title: '登录失败，请重试',
                  icon: 'none'
                });
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
