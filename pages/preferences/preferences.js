import api from '../../services/api';

Page({
  data: {
    userInput: '',
    inputPlaceholder: '例如:"想和朋友一起吃火锅,预算人均100左右,最好是安静的环境"'
  },

  handleInputChange(e) {
    this.setData({
      userInput: e.detail.value
    });
  },

  handleSubmit() {
    const { userInput } = this.data;
    
    if (!userInput.trim()) {
      wx.showToast({
        title: '请输入您的用餐需求',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({
      title: '正在规划...'
    });

    api.submitPreferences({ userInput })
      .then(() => {
        wx.hideLoading();
        wx.navigateTo({
          url: '/pages/index/index',
          success: () => {
            wx.showToast({
              title: '正在为您规划',
              icon: 'success'
            });
          }
        });
      })
      .catch(error => {
        console.error('提交失败:', error);
        wx.hideLoading();
        wx.showToast({
          title: '提交失败，请重试',
          icon: 'none'
        });
      });
  }
}); 