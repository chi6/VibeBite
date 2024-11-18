// index.js
const defaultAvatarUrl = '/images/default-avatar.png'
const api = require('../../services/api'); // 导入整个api对象

Page({
  data: {
    aiStatus: {
      mood: '加载中...',
      activity: '加载中...',
      thought: '加载中...'
    },
    agentId: '1' // 假设你有一个agent_id
  },

  onLoad() {
    this.fetchAIStatus();
  },

  fetchAIStatus() {
    const requestData = {
      agent_id: this.data.agentId // 传递agent_id
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
})
