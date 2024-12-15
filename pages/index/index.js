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
        'aiStatus.mood': status.mood || '未知',
        'aiStatus.activity': status.activity || '未知',
        'aiStatus.thought': status.thought || '未知'
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
          const summaryText = res.data.summary;
          
          // 解析返回的文本内容
          const sections = summaryText.split(/\d+\.\s+/).filter(Boolean);
          const preferences = {
            diningFeatures: sections[0]?.trim() || '暂无场景偏好',
            tastePreferences: sections[1]?.trim() || '暂无口味偏好',
            drinkPreferences: sections[2]?.trim() || '暂无饮品偏好',
            recommendations: sections[3]?.trim() || '暂无个性化推荐'
          };

          // 移除标题部分
          preferences.diningFeatures = preferences.diningFeatures.replace('用户主要用餐特征和场景偏好：', '');
          preferences.tastePreferences = preferences.tastePreferences.replace('口味和用餐方式特点：', '');
          preferences.drinkPreferences = preferences.drinkPreferences.replace('饮品选择倾向：', '');
          preferences.recommendations = preferences.recommendations.replace('个性化推荐建议：', '')
            .replace(/\s+- /g, '\n• '); // 将破折号替换为圆点，并添加换行

          this.setData({ preferences });
          console.log('解析后的偏好数据:', preferences);
        } catch (e) {
          console.error('解析偏好数据失败:', e);
          this.setData({
            preferences: {
              diningFeatures: '数据解析失败',
              tastePreferences: '数据解析失败',
              drinkPreferences: '数据解析失败',
              recommendations: '数据解析失败'
            }
          });
        }
      } else {
        throw new Error('获取数据失败');
      }
    }).catch(error => {
      wx.hideLoading();
      console.error('获取餐饮喜好总结失败:', error);
      this.setData({
        preferences: {
          diningFeatures: '获取信息失败',
          tastePreferences: '获取信息失败',
          drinkPreferences: '获取信息失败',
          recommendations: '获取信息失败'
        }
      });
    });
  },

  fetchAISettings() {
    api.getAISettings().then(res => {
      console.log('AI设置响应:', res);
      if (res.success && res.data) {
        this.setData({
          'aiStatus.name': res.data.name || 'AI智能助手'
        });
        console.log('更新后的AI名字:', this.data.aiStatus.name);
      } else {
        this.setData({
          'aiStatus.name': 'AI智能助手'
        });
      }
    }).catch(err => {
      console.error('获取AI设置失败:', err);
      this.setData({
        'aiStatus.name': 'AI智能助手'
      });
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
