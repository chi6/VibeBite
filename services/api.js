// 配置 API 基础 URL
const BASE_URL = 'http://127.0.0.1:5000';  // 生产环境

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
  },

  // 获取AI状态
  getAIStatus(data) {
    return this.request('/ai_status', {
      method: 'POST',
      data
    });
  },

  async getMeituanRecommendations(params) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: 'https://api.meituan.com/recommendations', // 替换为实际的美团API URL
        method: 'GET',
        data: params,
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data);
          } else {
            reject(new Error('Failed to fetch recommendations'));
          }
        },
        fail: (err) => {
          reject(err);
        }
      });
    });
  },

  async getRestaurants(params) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: 'https://newapi.ele.me/v2/restaurants/', // 替换为最新的饿了么API URL
        method: 'GET',
        data: params,
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data);
          } else {
            reject(new Error('Failed to fetch restaurants'));
          }
        },
        fail: (err) => {
          reject(err);
        }
      });
    });
  },

  async getNearbyRestaurants(params) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: 'http://apis.juhe.cn/catering/query', // 聚合数据API的基础URL,
        method: 'GET',
        data: {
          ...params,
          key: 'your_app_key', // 替换为你的聚合数据APPKEY
          dtype: 'json' // 返回数据格式
        },
        success: (res) => {
          if (res.statusCode === 200 && res.data.error_code === 0) {
            resolve(res.data.result);
          } else {
            reject(new Error(res.data.reason || 'Failed to fetch restaurants'));
          }
        },
        fail: (err) => {
          reject(err);
        }
      });
    });
  }
};

module.exports = api; 