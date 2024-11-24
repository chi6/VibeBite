Page({
  data: {
    userInfo: {
      nickName: '',
      gender: 0,
      language: '',
      city: '',
      province: '',
      country: '',
      avatarUrl: ''
    }
  },

  onLoad(options) {
    // 从上一个页面传递的用户信息
    if (options.userInfo) {
      this.setData({
        userInfo: JSON.parse(options.userInfo)
      });
    }
  },

  handleInputChange(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({
      [`userInfo.${field}`]: e.detail.value
    });
  },

  handleSubmit() {
    const { userInfo } = this.data;
    // 调用登录接口
    api.login(userInfo.code, userInfo)
      .then(res => {
        if (res.success) {
          wx.setStorageSync('userInfo', res.userInfo);
          wx.setStorageSync('token', res.token);
          wx.showToast({
            title: '登录成功',
            icon: 'success'
          });
          wx.reLaunch({
            url: '/pages/index/index'
          });
        } else {
          wx.showToast({
            title: '登录失败，请重试',
            icon: 'none'
          });
        }
      })
      .catch(error => {
        console.error('登录失败:', error);
        wx.showToast({
          title: '登录失败，请重试',
          icon: 'none'
        });
      });
  }
}); 