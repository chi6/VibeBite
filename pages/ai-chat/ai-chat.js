import api from '../../services/api';

Page({
  data: {
    messages: [],
    inputMessage: '',
    scrollToMessage: '',
    isLoading: false,
    location: null,
    aiInteractionContent: '欢迎来到AI互动区域',
    recommendations: [],
    images: [],
    relatedQuestions: [],
    relatedSearches: [],
    showRecommendations: false,
    lastRecommendationTime: 0,
    currentTab: 'restaurants'
  },

  onLoad: function() {
    wx.setNavigationBarTitle({
      title: 'AI 助手'
    });
    
    this.addMessage('ai', '你好！我是你的AI助手。我可以帮你推荐餐厅，你想吃什么类型的食物？');
    // this.getLocation();
    
    // 开始定期获取推荐
    this.startPeriodicRecommendations();
  },

  // 定期获取推荐的功能
  startPeriodicRecommendations() {
    // 每30秒检查一次是否需要更新推荐
    this.recommendationTimer = setInterval(() => {
      this.checkAndUpdateRecommendations();
    }, 30000);
  },

  onUnload() {
    // 清除定时器
    if (this.recommendationTimer) {
      clearInterval(this.recommendationTimer);
    }
  },

  async checkAndUpdateRecommendations() {
    const currentTime = Date.now();
    // 如果距离上次更新超过2分钟，则更新推荐
    if (currentTime - this.data.lastRecommendationTime > 120000) {
      await this.fetchLatestRecommendations();
    }
  },

  async fetchLatestRecommendations() {
    try {
      wx.showLoading({
        title: '更新推荐中...',
        mask: true
      });

      const response = await api.getRecommendations({
        location: this.data.location,
        messages: this.data.messages.slice(-5),
        timestamp: Date.now()
      });

      if (response.success && response.data) {
        // 处理推荐数据
        const recommendations = response.data.recommendations.map(item => ({
          ...item,
          formattedDate: new Date(item.timestamp).toLocaleDateString('zh-CN'),
          distance: this.calculateDistance(item.location),
          // 确保快照图片是数组
          snapshotImages: Array.isArray(item.snapshotImages) ? item.snapshotImages : []
        }));

        // 更新数据
        this.setData({
          recommendations,
          images: response.data.images || [],
          searchParameters: response.data.searchParameters || {},
          lastRecommendationTime: Date.now(),
          showRecommendations: true
        });

        console.log('推荐更新成功，响应时间:', response.response_time);
      }

      wx.hideLoading();
    } catch (error) {
      console.error('获取推荐失败:', error);
      wx.hideLoading();
      wx.showToast({
        title: '获取推荐失败',
        icon: 'none'
      });
    }
  },

  calculateDistance(locationStr) {
    if (!this.data.location || !locationStr) return '未知距离';
    // TODO: 实现实际的距离计算逻辑
    return '1.2km'; // 临时返回固定值
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({
      currentTab: tab
    });
  },

  handleRecommendationTap(e) {
    const { type, link } = e.currentTarget.dataset;
    if (link) {
      switch (type) {
        case 'restaurant':
          // 检查是否有快照图片
          const restaurant = this.data.recommendations.find(r => r.link === link);
          if (restaurant && restaurant.snapshotImages && restaurant.snapshotImages.length > 0) {
            // 如果有快照图片，显示图片预览
            wx.previewImage({
              current: restaurant.snapshotImages[0], // 显示第一张图片
              urls: restaurant.snapshotImages // 所有图片URL数组
            });
          } else {
            // 如果没有快照图片，跳转到详情页
            wx.navigateTo({
              url: `/pages/restaurant-detail/restaurant-detail?url=${encodeURIComponent(link)}`
            });
          }
          break;
        case 'image':
          wx.previewImage({
            urls: [link]
          });
          break;
        default:
          wx.showToast({
            title: '功能开发中',
            icon: 'none'
          });
      }
    }
  },

  handleSearchTap(e) {
    const searchTerm = e.currentTarget.dataset.term;
    this.setData({
      inputMessage: searchTerm
    });
    this.sendMessage();
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
        
        // 发送消息后立即获取新的推荐
        await this.fetchLatestRecommendations();
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
    if (!showRecommendations) {
      // 如果要显示推荐，先更新内容
      this.fetchLatestRecommendations();
    }
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
  },

  onInputChange(e) {
    this.setData({
      inputMessage: e.detail.value
    });
  }
});
