Page({
  data: {
    moods: [
      { name: '轻松', icon: 'mood-relaxed.png' },
      { name: '冒险', icon: 'mood-adventure.png' },
      { name: '浪漫', icon: 'mood-romantic.png' },
      { name: '欢乐', icon: 'mood-happy.png' },
      { name: '安静', icon: 'mood-quiet.png' },
      { name: '精致', icon: 'mood-elegant.png' }
    ],
    selectedMood: null
  },

  selectMood(e) {
    const mood = e.currentTarget.dataset.mood;
    this.setData({ selectedMood: mood });
  },

  confirmMood() {
    if (this.data.selectedMood) {
      // 将选择的心情存储到全局数据或本地存储中
      getApp().globalData.selectedMood = this.data.selectedMood;
      // 跳转到餐厅推荐页面
      wx.navigateTo({
        url: '/pages/recommendation/recommendation'
      });
    }
  }
});
