const api = require('../../services/api');

Page({
  data: {
    aiName: '',
    personality: '开朗',
    speakingStyle: '可爱',
    memories: '',
    personalities: ['开朗', '温柔', '活泼', '稳重', '傲娇'],
    speakingStyles: ['可爱', '正经', '俏皮', '温和', '幽默'],
    isCustomizing: false
  },

  onLoad() {
    this.fetchAISettings();
  },

  fetchAISettings() {
    // 获取已有设置
    api.getAISettings().then(res => {
      if (res.success) {
        this.setData({
          aiName: res.data.name || '',
          personality: res.data.personality || '开朗',
          speakingStyle: res.data.speakingStyle || '可爱',
          memories: res.data.memories || ''
        });
      }
    });
  },

  onNameInput(e) {
    this.setData({
      aiName: e.detail.value
    });
  },

  onPersonalityChange(e) {
    this.setData({
      personality: this.data.personalities[e.detail.value]
    });
  },

  onStyleChange(e) {
    this.setData({
      speakingStyle: this.data.speakingStyles[e.detail.value]
    });
  },

  onMemoriesInput(e) {
    this.setData({
      memories: e.detail.value
    });
  },

  onCustomizeStart() {
    this.setData({ isCustomizing: true });
    wx.vibrateShort({ type: 'medium' });
  },

  onCustomizeEnd() {
    this.setData({ isCustomizing: false });
  },

  saveSettings() {
    wx.showLoading({ title: '保存中...' });
    
    const settings = {
      name: this.data.aiName,
      personality: this.data.personality,
      speakingStyle: this.data.speakingStyle,
      memories: this.data.memories
    };

    api.updateAISettings(settings).then(() => {
      wx.hideLoading();
      wx.showToast({
        title: '设置成功',
        icon: 'success'
      });
      setTimeout(() => {
        wx.reLaunch({
          url: '/pages/preferences/preferences',
          fail: (err) => {
            console.error('跳转失败:', err);
            wx.showToast({
              title: '页面跳转失败',
              icon: 'none'
            });
          }
        });
      }, 1500);
    }).catch(() => {
      wx.hideLoading();
      wx.showToast({
        title: '保存失败',
        icon: 'error'
      });
    });
  }
}); 