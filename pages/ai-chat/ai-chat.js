import api from '../../services/api';

Page({
  data: {
    messages: [],
    inputMessage: '',
    scrollToMessage: '',
    isLoading: false,
    location: null,
    aiInteractionContent: '欢迎来到AI互动区域',
    recommendations: [
      {
        id: 1,
        tag: '测试推荐',
        title: '推荐主题1',
        description: '这是一条测试推荐内容'
      },
      {
        id: 2,
        tag: '热门推荐',
        title: '推荐主题2',
        description: '这是另一条测试推荐内容'
      }
    ],
    showRecommendations: false
  },

  onLoad: function() {
    wx.setNavigationBarTitle({
      title: 'AI 助手'
    });
    
    // 添加初始消息
    this.addMessage('ai', '你好！我是你的AI助手。我可以帮你推荐餐厅，你想吃什么类型的食物？');

    // 获取位置信息后获取推荐内容
    this.getLocation();
  },

  // 获取位置信息 TODO:页面跳转不过来了
  getLocation: function() {
    wx.getLocation({
      type: 'wgs84',
      success: (res) => {
        const { latitude, longitude } = res;
        this.setData({
          location: { latitude, longitude }
        });
        console.log('当前位置：', latitude, longitude);
        // 使用腾讯地图 SDK 搜索附近餐厅
        //this.searchNearbyRestaurants(latitude, longitude);
      },
      fail: (err) => {
        console.error('获取位置信息失败:', err);
        wx.showToast({
          title: '无法获取位置信息',
          icon: 'none'
        });
      }
    });
  },

  onInputChange: function(e) {
    this.setData({
      inputMessage: e.detail.value
    });
  },

  async sendMessage() {
    const { inputMessage, isLoading, location } = this.data;
    if (inputMessage.trim() === '' || isLoading) return;

    this.addMessage('user', inputMessage);
    this.setData({ 
      inputMessage: '',
      isLoading: true 
    });

    try {
      const response = await api.aiChat({
        message: inputMessage,
        taskName: 'chat',
        agentId: '1',
        groupId: 'main_group',
        location
      });

      if (response && response.response) {
        this.addMessage('ai', response.response);
        
        // 分析AI响应，更新推荐内容
        await this.updateRecommendations(response);
        
        // 显示推荐窗口
        this.setData({
          showRecommendations: true
        });

      } else {
        throw new Error('Invalid response from AI');
      }
    } catch (error) {
      console.error('AI响应失败:', error);
      wx.showToast({
        title: 'AI响应失败',
        icon: 'none'
      });
      this.addMessage('ai', '抱歉，我现在遇到了一些问题。请稍后再试。');
    } finally {
      this.setData({ isLoading: false });
    }
  },

  addMessage: function(type, content) {
    const { messages } = this.data;
    const newMessage = {
      id: messages.length + 1,
      type,
      content
    };
    
    messages.push(newMessage);
    this.setData({ 
      messages,
      scrollToMessage: `msg-${newMessage.id}`
    });
  },

  async searchNearbyRestaurants(latitude, longitude) {
    try {
      const response = await api.searchNearby({
        latitude,
        longitude,
        radius: 1000, // 搜索半径
        keyword: '餐厅',
        page_size: 10,
        page_index: 1,
        key: 'YOUR_API_KEY' // 替换为你的腾讯地图 API 密钥
      });

      if (response && response.data) {
        this.setData({
          recommendations: response.data.map(item => ({
            id: item.id,
            title: item.title,
            description: item.address || '暂无描述'
          }))
        });
      } else {
        console.warn('未能获取推荐内容');
      }
    } catch (error) {
      console.error('搜索餐厅失败:', error);
      wx.showToast({
        title: '搜索餐厅失败',
        icon: 'none'
      });
    }
  },

  toggleRecommendations() {
    const { showRecommendations } = this.data;
    console.log('切换推荐窗口状态:', !showRecommendations);
    this.setData({
      showRecommendations: !showRecommendations
    });
  },

  autoHideRecommendations() {
    setTimeout(() => {
      this.setData({
        showRecommendations: false
      });
    }, 10000); // 10秒后自动隐藏
  },

  startVoiceInput() {
    // 实现语音输入逻辑
  },

  async updateRecommendations(aiResponse) {
    try {
      // 这里可以根据AI响应来生成推荐内容
      const recommendations = [
        {
          id: 1,
          tag: '基于对话分析',
          title: '推荐主题1',
          description: '根据您的偏好，为您推荐...'
        },
        {
          id: 2,
          tag: '热门推荐',
          title: '推荐主题2',
          description: '大家都在看...'
        }
      ];

      this.setData({
        recommendations,
        showRecommendations: true  // 确保设置后立即显示
      });
      console.log('更新推荐内容成功，当前状态:', this.data.showRecommendations);
    } catch (error) {
      console.error('更新推荐失败:', error);
    }
  }
});
