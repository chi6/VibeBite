// index.js
const defaultAvatarUrl = '/images/default-avatar.png'
const api = require('../../services/api');

Page({
  data: {
    aiStatus: {
      mood: '加载中...',
      activity: '加载中...',
      thought: '加载中...'
    },
    agentId: '1',
    preferences: {
      summary: '加载中...'
    }
  },

  onLoad() {
    this.fetchAIStatus();
    this.fetchPreferencesSummary();
  },

  fetchAIStatus() {
    const requestData = {
      agent_id: this.data.agentId
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
        this.setData({
          'preferences.summary': res.data.summary || '暂无餐饮喜好信息'
        });
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

  goToAIChat() {
    wx.navigateTo({
      url: '/pages/ai-chat/ai-chat',
      fail: (err) => {
        console.error('跳转失败:', err);
        wx.showToast({
          title: '页面跳转失败',
          icon: 'none'
        });
      }
    });
  }
});
