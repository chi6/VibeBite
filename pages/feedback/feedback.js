Page({
  data: {
    feedbackContent: '',
    contactInfo: '',
    feedbackTypes: ['功能建议', '问题反馈', '其他'],
    selectedType: '功能建议'
  },

  handleTypeChange(e) {
    this.setData({
      selectedType: this.data.feedbackTypes[e.detail.value]
    })
  },

  handleContentInput(e) {
    this.setData({
      feedbackContent: e.detail.value
    })
  },

  handleContactInput(e) {
    this.setData({
      contactInfo: e.detail.value
    })
  },

  submitFeedback() {
    if (!this.data.feedbackContent) {
      wx.showToast({
        title: '请输入反馈内容',
        icon: 'none'
      })
      return
    }

    // 这里添加提交反馈的API调用
    wx.showLoading({
      title: '提交中...'
    })

    setTimeout(() => {
      wx.hideLoading()
      wx.showToast({
        title: '反馈已提交',
        icon: 'success'
      })
      
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    }, 1000)
  }
}) 