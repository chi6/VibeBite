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
    currentTab: 'restaurants',
    forceUpdate: false,
    shareId: '',
    isSharedSession: false,
    originalUser: null,
    agentId: '1'
  },

  onLoad: function(options) {
    wx.setNavigationBarTitle({
      title: 'AI 助手'
    });
    
    if (options.shareId) {
      this.setData({
        shareId: options.shareId,
        isSharedSession: true
      });
      this.loadSharedSession(options.shareId);
    } else {
      this.setData({
        agentId: '1'
      });
      this.addMessage('ai', '你好！我是你的AI助手。我可以帮你推荐餐厅，你想吃什么类型的食物？');
    }
    
    this.startPeriodicRecommendations();
  },

  startPeriodicRecommendations() {
    this.recommendationTimer = setInterval(() => {
      this.checkAndUpdateRecommendations();
    }, 30000);
  },

  onUnload() {
    if (this.recommendationTimer) {
      clearInterval(this.recommendationTimer);
    }
  },

  async checkAndUpdateRecommendations() {
    const currentTime = Date.now();
    if (
      currentTime - this.data.lastRecommendationTime > 120000 && 
      (this.shouldUpdateRecommendations() || this.data.forceUpdate)
    ) {
      await this.fetchLatestRecommendations();
      this.setData({ forceUpdate: false });
    }
  },

  shouldUpdateRecommendations() {
    const recentMessages = this.data.messages.slice(-5);
    const triggerKeywords = ['推荐', '建议'];
    return recentMessages.some(msg => 
      triggerKeywords.some(keyword => 
        msg.content.includes(keyword)
      )
    );
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
        agentId: this.data.agentId,
        timestamp: Date.now()
      });

      if (response.success && response.data) {
        const recommendationsList = response.data.recommendations.original_recommendations || [];
        
        const recommendations = recommendationsList.map(item => ({
          ...item,
          formattedDate: new Date().toLocaleDateString('zh-CN'),
          distance: this.calculateDistance(item.location),
          snapshotImages: Array.isArray(item.snapshotImages) ? item.snapshotImages : []
        }));

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
    return '1.2km';
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
          const restaurant = this.data.recommendations.find(r => r.link === link);
          if (restaurant && restaurant.snapshotImages && restaurant.snapshotImages.length > 0) {
            wx.previewImage({
              current: restaurant.snapshotImages[0],
              urls: restaurant.snapshotImages
            });
          } else {
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
    const { inputMessage, isLoading, isSharedSession, originalUser } = this.data;
    if (inputMessage.trim() === '' || isLoading) return;

    this.addMessage('user', inputMessage);
    this.setData({ 
      inputMessage: '',
      isLoading: true 
    });

    try {
      if (isSharedSession) {
        const [myResponse, originalResponse] = await Promise.all([
          api.aiChat({
            message: inputMessage,
            taskName: 'chat',
            agentId: '1',
            groupId: 'main_group',
            location: this.data.location
          }),
          api.aiChat({
            message: inputMessage,
            taskName: 'chat',
            agentId: originalUser.agentId,
            groupId: originalUser.groupId,
            location: this.data.location
          })
        ]);

        if (myResponse.response) {
          this.addMessage('ai', myResponse.response);
        }
        if (originalResponse.response) {
          this.addMessage('original-ai', originalResponse.response, originalUser.nickName);
        }
      } else {
        const response = await api.aiChat({
          message: inputMessage,
          taskName: 'chat',
          agentId: '1',
          groupId: 'main_group',
          location: this.data.location
        });

        if (response.response) {
          this.addMessage('ai', response.response);
        }
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

  addMessage: function(type, content, sender = '') {
    const { messages } = this.data;
    const newMessage = {
      id: messages.length + 1,
      type,
      content,
      sender,
      time: new Date().toLocaleTimeString()
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
        radius: 1000,
        keyword: '餐厅',
        page_size: 10,
        page_index: 1,
        key: 'YOUR_API_KEY'
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
      this.setData({
        forceUpdate: true,
        showRecommendations: true
      });
      this.checkAndUpdateRecommendations();
    } else {
      this.setData({
        showRecommendations: false
      });
    }
  },

  autoHideRecommendations() {
    setTimeout(() => {
      this.setData({
        showRecommendations: false
      });
    }, 10000);
  },

  startVoiceInput() {
    // 实现语音输入逻辑
  },

  async updateRecommendations(aiResponse) {
    try {
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
        showRecommendations: true
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
  },

  async loadSharedSession(shareId) {
    try {
      wx.showLoading({ title: '加载中...' });
      const response = await api.getSharedSession(shareId);
      
      if (response.success) {
        const { messages, recommendations, originalUser } = response.data;
        
        this.setData({
          messages: messages.map(msg => ({
            ...msg,
            isOriginal: true
          })),
          recommendations,
          originalUser,
        });

        this.addMessage('system', `以上是 ${originalUser.nickName} 的聊天记录，开始你的对话吧！`);
      }
      wx.hideLoading();
    } catch (error) {
      console.error('加载分享会话失败:', error);
      wx.hideLoading();
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    }
  },

  onShareAppMessage: function() {
    const shareId = this.generateShareId();
    
    this.saveSessionForSharing(shareId);
    
    return {
      title: '来看看AI给我推荐的美食！',
      path: `/pages/ai-chat/ai-chat?shareId=${shareId}`,
      imageUrl: '/images/share-cover.png'
    };
  },

  generateShareId() {
    return `share_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  },

  async saveSessionForSharing(shareId) {
    try {
      await api.saveSharedSession({
        shareId,
        messages: this.data.messages,
        recommendations: this.data.recommendations,
        timestamp: Date.now()
      });
    } catch (error) {
      console.error('保存分享会话失败:', error);
    }
  }
});
