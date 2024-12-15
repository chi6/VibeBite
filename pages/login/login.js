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
                    api.getPreferences(),
                    api.getAISettings()
                  ]);
                } else {
                  throw new Error('登录失败');
                }
              })
              .then(([preferences, aiSettings]) => {
                if (preferences.success && preferences.data) {
                  console.log("preferences.data:", preferences.data);
                  // 检查所有偏好字段是否为空
                  const isPreferencesEmpty = 
                    !preferences.data.alcoholAttitude &&
                    !preferences.data.customDescription &&
                    !preferences.data.diningScene &&
                    preferences.data.diningStyles.length === 0 &&
                    preferences.data.extractedKeywords.length === 0 &&
                    preferences.data.flavorPreferences.length === 0 &&
                    !preferences.data.restrictions;

                  if (isPreferencesEmpty) {
                    // 如果偏好内容都为空，跳转到偏好设置页面
                    wx.navigateTo({
                      url: '/pages/preferences/preferences'
                    });
                  } else if (aiSettings.success && aiSettings.data && aiSettings.data.name) {
                    // 如果已经设置过AI和偏好，直接跳转到首页
                    wx.reLaunch({
                      url: '/pages/index/index'
                    });
                  } else {
                    // 如果有偏好但没有AI设置，跳转到AI设置页面
                    wx.navigateTo({
                      url: '/pages/ai-customization/ai-customization'
                    });
                  }
                } else {
                  // 如果获取偏好失败，默认跳转到偏好设置页面
                  wx.navigateTo({
                    url: '/pages/preferences/preferences'
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
