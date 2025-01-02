import api from '../../services/api';
const app = getApp();

const QQ_MAP_KEY = '7D5BZ-ZRJWW-3W4RU-32FEM-ZLXLJ-77BOA';

Page({
  data: {
    isLoading: false
  },

  handleWechatLogin(e) {
    if (this.data.isLoading) return;
    
    this.setData({ isLoading: true });

    if (e.detail.userInfo) {
      // 保存微信返回的用户信息
      const wxUserInfo = e.detail.userInfo;
      console.log('微信返回的用户信息：', wxUserInfo);

      wx.login({
        success: (res) => {
          if (res.code) {
            // 获取用户位置信息
            wx.getLocation({
              type: 'gcj02',
              success: (locationRes) => {
                console.log("locationRes", locationRes);
                // 使用腾讯地图逆地理编码服务
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
                      console.log("geoRes", geoRes);
                      if (geoRes.data.status === 0 && geoRes.data.result) {
                        const addressComponent = geoRes.data.result.address_component;
                        locationInfo = [
                          addressComponent.province,
                          addressComponent.city,
                          addressComponent.district
                        ].filter(Boolean).join(',');
                      }
                    } catch (err) {
                      console.error('解析位置信息失败:', err);
                    }

                    // 调用登录接口
                    api.login(res.code, wxUserInfo, locationInfo)
                      .then(loginRes => {
                        console.log('登录返回数据:', loginRes);
                        
                        if (loginRes.success && loginRes.data) {
                          // 构建完整的用户信息
                          const userInfo = {
                            ...loginRes.data,
                            nickName: wxUserInfo.nickName,
                            avatarUrl: wxUserInfo.avatarUrl,
                            gender: wxUserInfo.gender,
                            country: wxUserInfo.country,
                            province: wxUserInfo.province,
                            city: wxUserInfo.city,
                            language: wxUserInfo.language
                          };

                          // 保存用户信息
                          app.globalData.userInfo = userInfo;
                          wx.setStorageSync('userInfo', userInfo);
                          wx.setStorageSync('token', loginRes.data.token);

                          console.log('保存的用户信息：', userInfo);
                          
                          // 获取AI设置
                          return api.getAISettings();
                        } else {
                          throw new Error('登录返回数据无效');
                        }
                      })
                      .then(aiSettings => {
                        if (aiSettings.success && aiSettings.data && aiSettings.data.name !== "默认助手") {
                          wx.switchTab({
                            url: '/pages/index/index'
                          });
                        } else {
                          wx.navigateTo({
                            url: '/pages/ai-customization/ai-customization'
                          });
                        }
                      })
                      .catch(error => {
                        console.error('登录过程出错:', error);
                        wx.showToast({
                          title: '登录失败，请重试',
                          icon: 'none'
                        });
                      })
                      .finally(() => {
                        this.setData({ isLoading: false });
                      });
                  },
                  fail: (error) => {
                    console.error('获取地理位置详情失败:', error);
                    this.continueLoginWithoutLocation(res.code, wxUserInfo);
                  }
                });
              },
              fail: (error) => {
                console.error('获取位置失败:', error);
                this.continueLoginWithoutLocation(res.code, wxUserInfo);
              }
            });
          } else {
            console.error('获取登录凭证失败:', res);
            wx.showToast({
              title: '登录失败，请重试',
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

  continueLoginWithoutLocation(code, wxUserInfo) {
    api.login(code, wxUserInfo)
      .then(loginRes => {
        if (loginRes.success && loginRes.data) {
          // 构建完整的用户信息
          const userInfo = {
            ...loginRes.data,
            nickName: wxUserInfo.nickName,
            avatarUrl: wxUserInfo.avatarUrl,
            gender: wxUserInfo.gender,
            country: wxUserInfo.country,
            province: wxUserInfo.province,
            city: wxUserInfo.city,
            language: wxUserInfo.language
          };

          // 保存用户信息
          app.globalData.userInfo = userInfo;
          wx.setStorageSync('userInfo', userInfo);
          wx.setStorageSync('token', loginRes.data.token);

          console.log('保存的用户信息（无位置）：', userInfo);
          
          return api.getAISettings();
        } else {
          throw new Error('登录返回数据无效');
        }
      })
      .then(aiSettings => {
        if (aiSettings.success && aiSettings.data && aiSettings.data.name !== "默认助手") {
          wx.switchTab({
            url: '/pages/index/index'
          });
        } else {
          wx.navigateTo({
            url: '/pages/ai-customization/ai-customization'
          });
        }
      })
      .catch(error => {
        console.error('登录过程出错:', error);
        wx.showToast({
          title: '登录失败，请重试',
          icon: 'none'
        });
      })
      .finally(() => {
        this.setData({ isLoading: false });
      });
  },

  showPrivacyPolicy() {
    wx.navigateTo({
      url: '/pages/privacy/privacy'
    });
  }
});
