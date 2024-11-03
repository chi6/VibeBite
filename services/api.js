// 配置 API 基础 URL
const BASE_URL = 'http://192.168.0.102:5000';  // 生产环境

const api = {
  // 基础请求方法
  async request(url, options = {}) {
    const token = wx.getStorageSync('token');
    
    const defaultOptions = {
      url: `${BASE_URL}${url}`,
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      ...options
    };

    console.log('请求的 URL:', defaultOptions.url); // 添加调试信息
    console.log('请求的选项:', defaultOptions); // 添加调试信息

    try {
      const response = await new Promise((resolve, reject) => {
        wx.request({
          ...defaultOptions,
          success: resolve,
          fail: reject
        });
      });
      console.log('完整响应：', response); // 打印完整响应
      console.log('返回状态码：', response.statusCode); // 打印状态码
      console.log('返回数据：', response.data); // 打印返回的数据
      if (response.statusCode === 200) {
        return response.data;
      } else {
        console.error('请求失败，状态码:', response.statusCode);
        throw new Error(response.data ? response.data.message : '请求失败');
      }
    } catch (error) {
      console.error('API请求失败:', error);
      throw error; // 继续抛出错误以便在调用处处理
    }
  },

  // AI聊天
  aiChat(data) {
    return this.request('/chat_agent', {
      method: 'POST',
      data
    });
  },

  // 验证token
  validateToken(token) {
    return this.request('/validate-token', {
      method: 'POST',
      data: { token }
    });
  },

  // 登录
  login(code) {
    return this.request('/api/login', {
      method: 'POST',
      data: { code }
    });
  },

  // 启动模拟讨论
  startSimulation(data) {
    return this.request('/simulation', {
      method: 'POST',
      data
    });
  }
};

export default api; 