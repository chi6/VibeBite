export function getUserInfo() {
  try {
    const userInfo = wx.getStorageSync('userInfo');
    if (!userInfo) {
      // 如果没有用户信息，重定向到登录页
      wx.redirectTo({
        url: '/pages/login/login'
      });
      return null;
    }
    return userInfo;
  } catch (error) {
    console.error('获取用户信息失败:', error);
    return null;
  }
} 