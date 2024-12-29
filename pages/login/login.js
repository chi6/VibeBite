import api from '../../services/api';

const QQ_MAP_KEY = '7D5BZ-ZRJWW-3W4RU-32FEM-ZLXLJ-77BOA'; // 请替换为实际的腾讯地图密钥

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
            // 获取用户位置信息
            wx.getLocation({
              type: 'gcj02',  // 使用国测局坐标系
              success: (locationRes) => {
                // 使用腾讯地图逆地理编码服务
                console.log("locationRes", locationRes)
                wx.request({
                  url: `https://apis.map.qq.com/ws/geocoder/v1/`,
                  data: {
                    location: `${locationRes.latitude},${locationRes.longitude}`,
                    key: QQ_MAP_KEY,
                    get_poi: 0
                  },
                  success: (geoRes) => {
                    let locationInfo = '';
                    try {
                      console.log("geoRes", geoRes)
                      if (geoRes.data.status === 0 && geoRes.data.result) {
                        const addressComponent = geoRes.data.result.address_component;
                        // 组合省市区信息
                        locationInfo = [
                          addressComponent.province,
                          addressComponent.city,
                          addressComponent.district
                        ].filter(Boolean).join(',');
                      }
                    } catch (err) {
                      console.error('解析位置信息失败:', err);
                    }
                    console.log("locationInfo", locationInfo)
                    // 进行登录，并传递位置信息
                    api.login(res.code, e.detail.userInfo, locationInfo)
                      .then(loginRes => {
                        if (loginRes.success) {
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
                  },
                  fail: (error) => {
                    console.error('获取地理位置详情失败:', error);
                    // 如果获取详细地址失败，仍然继续登录流程，但不带位置信息
                    this.continueLoginWithoutLocation(res.code, e.detail.userInfo);
                  }
                });
              },
              fail: (error) => {
                console.error('获取位置失败:', error);
                // 如果用户拒绝位置权限，仍然继续登录流程
                this.continueLoginWithoutLocation(res.code, e.detail.userInfo);
              }
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

  // 在获取位置失败时继续登录的辅助方法
  continueLoginWithoutLocation(code, userInfo) {
    api.login(code, userInfo)
      .then(loginRes => {
        if (loginRes.success) {
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
  },

  showPrivacyPolicy() {
    wx.navigateTo({
      url: '/pages/privacy/privacy'
    });
  }
});
