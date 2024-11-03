// index.js
const defaultAvatarUrl = '/images/default-avatar.png'

Page({
  data: {
    currentMood: '',
    currentMode: '',
    showMoodInput: false,
    showModeInput: false,
    tempMood: '',
    tempMode: ''
  },

  onLoad() {
    const app = getApp();
    this.setData({
      currentMood: app.globalData.selectedMood || '未设置',
      currentMode: app.globalData.selectedMode || '未设置'
    });
  },

  showMoodInput() {
    this.setData({
      showMoodInput: true,
      showModeInput: false,
      tempMood: this.data.currentMood === '未设置' ? '' : this.data.currentMood
    });
  },

  showModeInput() {
    this.setData({
      showModeInput: true,
      showMoodInput: false,
      tempMode: this.data.currentMode === '未设置' ? '' : this.data.currentMode
    });
  },

  onMoodInput(e) {
    this.setData({
      tempMood: e.detail.value
    });
  },

  onModeInput(e) {
    this.setData({
      tempMode: e.detail.value
    });
  },

  confirmMood(e) {
    const mood = e.detail.value.trim();
    if (mood) {
      this.setData({
        currentMood: mood,
        showMoodInput: false
      });
      getApp().globalData.selectedMood = mood;
    }
  },

  confirmMode(e) {
    const mode = e.detail.value.trim();
    if (mode) {
      this.setData({
        currentMode: mode,
        showModeInput: false
      });
      getApp().globalData.selectedMode = mode;
    }
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
