Page({
  data: {
    selectedMood: null,
    recommendedRestaurant: null,
    recommendationReason: ''
  },

  onLoad() {
    // 从全局数据或本地存储中获取选择的心情
    const selectedMood = getApp().globalData.selectedMood;
    this.setData({ selectedMood });
    this.getRecommendation();
  },

  getRecommendation() {
    wx.request({
      url: 'https://your-api-domain.com/api/recommend',
      method: 'POST',
      data: {
        mood: this.data.selectedMood.name,
        // 可以添加其他参数，如用户位置等
      },
      success: (res) => {
        if (res.statusCode === 200) {
          this.setData({
            recommendedRestaurant: res.data.restaurant,
            recommendationReason: res.data.reason
          });
        } else {
          wx.showToast({
            title: '获取推荐失败',
            icon: 'none'
          });
        }
      },
      fail: (err) => {
        console.error('API调用失败', err);
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        });
      }
    });
  },

  getNewRecommendation() {
    // 重新获取推荐
    this.getRecommendation();
  },

  viewDetails() {
    // 这里应该跳转到美团或大众点评的详情页
    // 由于无法直接跳转到第三方小程序，我们可以打开一个webview页面
    wx.navigateTo({
      url: `/pages/webview/webview?url=${encodeURIComponent('https://example.com/restaurant-details')}`
    });
  }
});
