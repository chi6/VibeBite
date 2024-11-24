const { userApi } = require('../../services/api')

Page({
  data: {
    userInfo: null
  },

  onLoad() {
    this.getUserInfo()
  },

  async getUserInfo() {
    try {
      const res = await userApi.getUserInfo()
      this.setData({
        userInfo: res.data
      })
    } catch (error) {
      wx.showToast({
        title: '获取用户信息失败',
        icon: 'none'
      })
    }
  },

  async handleUpdateUserInfo() {
    try {
      const userInfo = await wx.getUserProfile({
        desc: '用于完善用户资料'
      })
      
      await userApi.updateUserInfo(userInfo.userInfo)
      this.getUserInfo()
      
      wx.showToast({
        title: '更新成功',
        icon: 'success'
      })
    } catch (error) {
      wx.showToast({
        title: '更新失败',
        icon: 'none'
      })
    }
  }
}) 