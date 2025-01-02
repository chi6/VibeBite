Page({
  data: {
    version: '1.0.0',
    appInfo: {
      name: 'VibeBite',
      description: '您的个性化美食推荐助手',
      features: [
        '智能推荐',
        'AI对话',
        '个性化定制'
      ]
    }
  },

  handleUpdate() {
    wx.showToast({
      title: '已是最新版本',
      icon: 'success'
    })
  }
}) 