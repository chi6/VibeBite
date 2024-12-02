const BASE_URL = 'http://106.52.168.146:80';  // 生产环境

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

    console.log('请求的 URL:', defaultOptions.url);
    console.log('请求的选项:', defaultOptions);

    try {
      const response = await new Promise((resolve, reject) => {
        wx.request({
          ...defaultOptions,
          success: resolve,
          fail: reject
        });
      });
      console.log('完整响应：', response);
      console.log('返回状态码：', response.statusCode);
      console.log('返回数据：', response.data);
      if (response.statusCode === 200) {
        return response.data;
      } else {
        console.error('请求失败，状态码:', response.statusCode);
        throw new Error(response.data ? response.data.message : '请求失败');
      }
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  },

  // AI聊天
  aiChat(data) {
    return this.request('/chat_agent', {
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

  // 验证token
  validateToken(token) {
    return this.request('/validate-token', {
      method: 'POST',
      data: { token }
    });
  },

  // 登录
  login(code, userInfo) {
    return this.request('/api/login', {
      method: 'POST',
      data: {
        code: code,
        userInfo: {
          nickName: userInfo.nickName,
          gender: userInfo.gender,
          language: userInfo.language,
          city: userInfo.city,
          province: userInfo.province,
          country: userInfo.country,
          avatarUrl: userInfo.avatarUrl
        }
      }
    });
  },

  // 启模拟讨论
  startSimulation(data) {
    return this.request('/simulation', {
      method: 'POST',
      data
    });
  },

  async getMeituanRecommendations(params) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: 'https://api.meituan.com/recommendations',
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
        url: 'https://newapi.ele.me/v2/restaurants/',
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
        url: 'http://apis.juhe.cn/catering/query',
        method: 'GET',
        data: {
          ...params,
          key: 'your_app_key',
          dtype: 'json'
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
  },

  // 提交餐饮喜好信息
  submitPreferences(preferences) {
    return this.request('/api/preferences', {
      method: 'POST',
      data: {
        preferences,
        timestamp: Date.now()
      }
    });
  },

  // 获取餐饮喜好信息
  getPreferences() {
    return this.request('/api/preferences', {
      method: 'GET'
    });
  },

  // 获取餐饮喜好总结
  getPreferencesSummary() {
    return this.request('/api/preferences/summary', {
      method: 'POST',
      data: {}
    });
  },

  // 获取基于对话的推荐
  getRecommendations(data) {
    return this.request('/api/recommendations', {
      method: 'POST',
      data: {
        location: data.location,
        messages: data.messages,
        agentId: data.agentId,
        timestamp: Date.now()
      }
    });
  },

  // 保存分享会话
  saveSharedSession(data) {
    return this.request('/api/share/save', {
      method: 'POST',
      data
    });
  },

  // 获取分享会话
  getSharedSession(shareId) {
    return this.request(`/api/share/${shareId}`, {
      method: 'GET'
    });
  },

  // 添加更新偏好的 API 方法
  updatePreferences(agentId, location) {
    return this.request('/api/update_pref', {
      method: 'POST',
      data: {
        agent_id: agentId,
        location: location
      }
    });
  }
};

module.exports = api; 