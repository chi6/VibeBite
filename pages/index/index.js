// index.js
const api = require('../../services/api');

Page({
  data: {
    aiStatus: {
      mood: '加载中...',
      activity: '加载中...',
      thought: '加载中...',
      name: '加载中...'
    },
    openid: '',
    preferences: {
      summary: '加载中...'
    }
  },

  onLoad() {
    wx.login({
      success: (res) => {
        if (res.code) {
          api.request('/api/wx/openid', {
            method: 'POST',
            data: { code: res.code }
          }).then(openidRes => {
            this.setData({ openid: openidRes.openid });
            this.fetchAIStatus();
            this.fetchPreferencesSummary();
            this.fetchAISettings();
          }).catch(err => {
            console.error('获取openid失败:', err);
          });
        }
      }
    });
  },

  fetchAIStatus() {
    const requestData = {
      openid: this.data.openid
    };
    api.getAIStatus(requestData).then(status => {
      this.setData({
        aiStatus: {
          mood: status.mood || '未知',
          activity: status.activity || '未知',
          thought: status.thought || '未知'
        }
      });
    }).catch(error => {
      console.error('获取AI状态失败:', error);
      wx.showToast({
        title: '获取AI状态失败',
        icon: 'none'
      });
    });
  },

  fetchPreferencesSummary() {
    wx.showLoading({
      title: '加载中...',
      mask: true
    });

    api.getPreferencesSummary().then(res => {
      wx.hideLoading();
      if (res.success && res.data) {
        try {
          const preferencesData = JSON.parse(res.data.summary);
          this.setData({
            preferences: {
              diningFeatures: preferencesData["主要用餐特征和场景偏好"],
              tastePreferences: preferencesData["口味和用餐方式特点"],
              drinkPreferences: preferencesData["饮品选择倾向"],
              recommendations: preferencesData["个性化推荐建议"]
            }
          });
        } catch (e) {
          console.error('解析偏好数据失败:', e);
          this.setData({
            'preferences.summary': '数据解析失败，请稍后重试'
          });
        }
      } else {
        throw new Error('获取数据失败');
      }
    }).catch(error => {
      wx.hideLoading();
      console.error('获取餐饮喜好总结失败:', error);
      this.setData({
        'preferences.summary': '获取信息失败，请稍后重试'
      });
    });
  },

  fetchAISettings() {
    api.getAISettings().then(res => {
      if (res.success && res.data) {
        this.setData({
          'aiStatus.name': res.data.name || 'AI智能助手'
        });
      }
    }).catch(err => {
      console.error('获取AI设置失败:', err);
    });
  },

  goToAIChat() {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        const location = {
          latitude: res.latitude,
          longitude: res.longitude
        };
        
        api.updatePreferences(this.data.openid, location).then(() => {
          wx.navigateTo({
            url: `/pages/ai-chat/ai-chat?openid=${this.data.openid}&aiName=${this.data.aiStatus.name || 'AI 助手'}`,
            fail: (err) => {
              console.error('跳转失败:', err);
              wx.showToast({
                title: '页面跳转失败',
                icon: 'none'
              });
            }
          });
        }).catch(error => {
          console.error('更新偏好失败:', error);
          wx.showToast({
            title: '更新偏好失败',
            icon: 'none'
          });
        });
      },
      fail: (err) => {
        console.error('获取位置失败:', err);
        wx.showToast({
          title: '获取位置失败',
          icon: 'none'
        });
      }
    });
  }
});
