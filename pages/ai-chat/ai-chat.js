import api from '../../services/api';

Page({
  data: {
    openid: '',
    messages: [],
    inputValue: '',
    scrollTop: 0,
    isLoading: false,
    location: null,
    aiInteractionContent: '欢迎来到AI互动区域',
    recommendations: [],
    relatedSearches: [],
    showRecommendations: false,
    lastRecommendationTime: 0,
    forceUpdate: false,
    shareId: '',
    isSharedSession: false,
    originalUser: null,
    organizedPlan: '',
    intents: [],
    recommendationHistory: [],
    groupedRecommendations: [],
    showFeedbackModal: false,
    feedbackContent: '',
    feedbackType: '', // 'positive' 或 'negative'
    showFloatingWindow: false,
    contactInfo: ''
  },

  onLoad: function(options) {
    // 从options中获取传递的openid和AI名字
    if (options.openid) {
      this.setData({ openid: options.openid });
    } else {
      // 如果没有传递openid，则重新获取
      wx.login({
        success: (res) => {
          if (res.code) {
            api.request('/api/wx/openid', {
              method: 'POST',
              data: { code: res.code }
            }).then(openidRes => {
              this.setData({ openid: openidRes.openid });
            }).catch(err => {
              console.error('获取openid失败:', err);
            });
          }
        }
      });
    }

    // 获取位置信息
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          location: {
            latitude: res.latitude,
            longitude: res.longitude
          }
        });
      },
      fail: (err) => {
        console.error('获取位置失败:', err);
      }
    });

    // 设置导航栏标题为传入的AI名字
    if (options.aiName) {
      wx.setNavigationBarTitle({
        title: options.aiName
      });
    } else {
      wx.setNavigationBarTitle({
        title: 'AI 助手'
      });
    }
    
    if (options.shareId) {
      this.setData({
        shareId: options.shareId,
        isSharedSession: true
      });
      this.loadSharedSession(options.shareId);
    } else {
      this.addMessage('ai', '你好！我是你的AI助手。我可以帮你推荐餐厅，你想吃什么类型的食物？');
    }
  },

  onUnload() {
    // 如果有其他清理代码，保留在这里
  },

  async fetchLatestRecommendations() {
    // 如果没有位置信息，尝试重新获取
    if (!this.data.location) {
      try {
        const locationRes = await new Promise((resolve, reject) => {
          wx.getLocation({
            type: 'gcj02',
            success: resolve,
            fail: reject
          });
        });
        
        this.setData({
          location: {
            latitude: locationRes.latitude,
            longitude: locationRes.longitude
          }
        });
      } catch (error) {
        console.error('获取位置失败:', error);
      }
    }

    // 如果没有 openid，先获取
    if (!this.data.openid) {
      try {
        const loginRes = await new Promise((resolve, reject) => {
          wx.login({
            success: resolve,
            fail: reject
          });
        });

        if (loginRes.code) {
          const openidRes = await api.request('/api/wx/openid', {
            method: 'POST',
            data: { code: loginRes.code }
          });
          this.setData({ openid: openidRes.openid });
        } else {
          throw new Error('获取登录凭证失败');
        }
      } catch (error) {
        console.error('获取openid失败:', error);
        wx.showToast({
          title: '获取用户信息失败',
          icon: 'none'
        });
        return;
      }
    }

    try {
      wx.showLoading({
        title: '更新推荐中...',
        mask: true
      });

      const response = await api.getRecommendations({
        location: this.data.location,
        messages: this.data.messages.slice(-5),
        openid: this.data.openid,
        timestamp: Date.now()
      });

      if (response.success && response.data) {
        const recommendationsList = response.data.recommendations.original_recommendations || [];
        const rawPlan = response.data.recommendations.organized_plan || '';
        const intents = response.data.recommendations.intents || [];
        
        const formattedPlan = this.formatOrganizedPlan(rawPlan);
        
        const newRecommendations = recommendationsList.map((item, index) => ({
          ...item,
          uniqueId: `${Date.now()}_${index}`,
          formattedDate: new Date().toLocaleDateString('zh-CN'),
          timestamp: Date.now(),
          distance: this.calculateDistance(item.location),
          snapshot: this.validateImageUrl(item.webSnapshot || item.snapshot || item.image),
          domain: this.extractDomain(item.link),
          description: item.description || item.summary || '',
          title: item.title || this.extractTitle(item.link) || '推荐内容'
        }));

        // 直接将新推荐添加到历史记录末尾，保持原始顺序
        const updatedHistory = [...this.data.recommendationHistory, ...newRecommendations];

        // 按日期分组，保持原始顺序
        const groupedRecommendations = this.groupRecommendationsByDate(updatedHistory);

        this.setData({
          recommendations: newRecommendations,
          recommendationHistory: updatedHistory,
          groupedRecommendations,
          organizedPlan: formattedPlan,
          intents,
          lastRecommendationTime: Date.now(),
          forceUpdate: false
        });

        console.log('推荐更新成功，历史记录数:', updatedHistory.length);
        console.log('分组后的推荐:', groupedRecommendations);
      }

      wx.hideLoading();
    } catch (error) {
      console.error('获取推荐失败:', error);
      wx.hideLoading();
      wx.showToast({
        title: '获取推荐失败',
        icon: 'none'
      });
      this.setData({ forceUpdate: false });
    }
  },

  calculateDistance(locationStr) {
    if (!this.data.location || !locationStr) return '未知距离';
    return '1.2km';
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
      inputValue: searchTerm
    });
    this.sendMessage();
  },

  async sendMessage() {
    const { inputValue, isLoading, isSharedSession, originalUser } = this.data;
    if (inputValue.trim() === '' || isLoading) return;

    this.addMessage('user', inputValue);
    this.setData({ 
      inputValue: '',
      isLoading: true 
    });

    try {
      if (isSharedSession) {
        const [myResponse, originalResponse] = await Promise.all([
          api.aiChat({
            openid: this.data.openid,
            message: inputValue,
            taskName: 'chat',
            location: this.data.location
          }),
          api.aiChat({
            openid: originalUser.openid,
            message: inputValue,
            taskName: 'chat',
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
          openid: this.data.openid,
          message: inputValue,
          taskName: 'chat',
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

  addMessage(type, content, sender = '') {
    const { messages } = this.data;
    const newMessage = {
      id: messages.length + 1,
      type,
      content: typeof content === 'string' ? content : JSON.stringify(content),
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
      // 显示加载中提示
      wx.showLoading({
        title: '获取推荐中...',
        mask: true
      });
      
      // 获取新的推荐
      this.fetchLatestRecommendations().then(() => {
        this.setData({
          showRecommendations: true
        });
        wx.hideLoading();
      }).catch(error => {
        console.error('获取新推荐失败:', error);
        wx.hideLoading();
        wx.showToast({
          title: '获取推荐失败',
          icon: 'none'
        });
      });
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
      inputValue: e.detail.value
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
          originalUser: {
            ...originalUser,
            openid: originalUser.openid
          }
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
  },

  formatOrganizedPlan(rawPlan) {
    if (!rawPlan) return null;

    try {
      const sections = rawPlan.split(/\d+\.\s+/).filter(Boolean);
      
      return sections.map(section => {
        const lines = section.trim().split('\n');
        const title = lines[0].trim().replace(/\*\*/g, '');
        const details = lines.slice(1)
          .map(line => line.trim())
          .filter(Boolean)
          .map(line => {
            let content = line.replace(/^-\s*/, '');
            content = content.replace(/\*\*/g, '');
            
            let detail = {
              type: line.startsWith('-') ? 'detail' : 'text',
              content: content,
              highlights: [],
            };

            if (content.includes('照片') || content.includes('实拍')) {
              const imageMatch = content.match(/(\d+)\s*张.*?照片/);
              if (imageMatch) {
                detail.imageCount = parseInt(imageMatch[1], 10);
                detail.images = [];
              }
            }

            return detail;
          });

        return {
          title,
          details,
          titleHighlights: lines[0].match(/\*\*(.*?)\*\*/g)?.map(match => 
            match.replace(/\*\*/g, '')
          ) || []
        };
      });
    } catch (error) {
      console.error('格式化计划失败:', error);
      return [{
        title: '推荐建议',
        details: [{
          type: 'text',
          content: rawPlan,
          images: []
        }]
      }];
    }
  },

  extractSnapshots(text) {
    const snapshotRegex = /\[snapshot\](.*?)\[\/snapshot\]/g;
    const snapshots = [];
    let match;

    while ((match = snapshotRegex.exec(text)) !== null) {
      try {
        const snapshotData = JSON.parse(match[1]);
        snapshots.push({
          url: snapshotData.url,
          image: snapshotData.image,
          title: snapshotData.title
        });
      } catch (error) {
        console.error('解析快照数据失败:', error);
      }
    }

    return snapshots;
  },

  groupRecommendationsByDate(recommendations) {
    const groups = {};
    const today = new Date().toLocaleDateString('zh-CN');
    
    // 按日期分组，保持原始顺序
    recommendations.forEach(item => {
      const date = item.formattedDate || today;
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push({...item});
    });
    
    // 转换为数组格式
    const result = Object.entries(groups).map(([date, items]) => ({
      date,
      // 保持每组内的原始顺序
      items: items
    }));
    
    // 按日期正序排序（早的日期在前）
    result.sort((a, b) => {
      const dateA = new Date(a.date.replace(/年|月|日/g, '/'));
      const dateB = new Date(b.date.replace(/年|月|日/g, '/'));
      return dateA - dateB;
    });
    
    return result;
  },

  // 添加处理链接点击的方法
  handleLinkTap(e) {
    const { url, snapshot } = e.currentTarget.dataset;
    
    // 如果有快照图片，先预览图片
    if (snapshot) {
      wx.previewImage({
        current: snapshot,
        urls: [snapshot],
        success: () => {
          // 预览后可以选择是否要打开链接
          wx.showActionSheet({
            itemList: ['打开链接', '取消'],
            success: (res) => {
              if (res.tapIndex === 0 && url) {
                this.openWebView(url);
              }
            }
          });
        }
      });
    } else if (url) {
      this.openWebView(url);
    }
  },

  // 封装打开网页的方法
  openWebView(url) {
    wx.navigateTo({
      url: `/pages/webview/webview?url=${encodeURIComponent(url)}`,
      fail: (err) => {
        console.error('打开链接失败:', err);
        wx.showToast({
          title: '打开链接失败',
          icon: 'none'
        });
      }
    });
  },

  // 添加提取网页标题的方法
  extractTitle(url) {
    if (!url) return '';
    try {
      const urlObj = new URL(url);
      const pathParts = urlObj.pathname.split('/').filter(Boolean);
      return pathParts[pathParts.length - 1] || urlObj.hostname;
    } catch (error) {
      return '';
    }
  },

  // 优化提取域名的方法
  extractDomain(url) {
    if (!url) return '';
    try {
      const domain = new URL(url).hostname;
      // 移除 www 前缀并限制长度
      const cleanDomain = domain.replace(/^www\./, '');
      return cleanDomain.length > 20 ? cleanDomain.substring(0, 20) + '...' : cleanDomain;
    } catch (error) {
      return '';
    }
  },

  handleSnapshotTap(e) {
    const { url, images } = e.currentTarget.dataset;
    
    if (Array.isArray(images) && images.length > 0) {
      const imageUrls = images
        .filter(item => item && item.image && typeof item.image === 'string')
        .map(item => item.image);
      
      if (imageUrls.length > 0) {
        const current = images.find(item => item.url === url)?.image || imageUrls[0];
        
        wx.previewImage({
          current,
          urls: imageUrls,
          fail: (err) => {
            console.error('预览图片失败:', err);
            wx.showToast({
              title: '图片预览失败',
              icon: 'none'
            });
          }
        });
      } else {
        this.handleUrlNavigation(url);
      }
    } else {
      this.handleUrlNavigation(url);
    }
  },

  handleUrlNavigation(url) {
    if (url && typeof url === 'string') {
      wx.navigateTo({
        url: `/pages/webview/webview?url=${encodeURIComponent(url)}`,
        fail: (err) => {
          console.error('打开链接失败:', err);
          wx.showToast({
            title: '打开链接失败',
            icon: 'none'
          });
        }
      });
    }
  },

  // 添加图片错误处理函数
  handleImageError(e) {
    console.error('图片加载失败:', e);
    const defaultImage = '/images/default-image.png';
    
    // 如果是列表中的图片
    if (e.target.dataset.index !== undefined) {
      const index = e.target.dataset.index;
      const newMessages = [...this.data.messages];
      if (newMessages[index] && newMessages[index].type === 'image') {
        newMessages[index].content = defaultImage;
        this.setData({ messages: newMessages });
      }
    }
    
    // 如果是推荐列表中的图片
    if (e.target.dataset.recommendIndex !== undefined) {
      const index = e.target.dataset.recommendIndex;
      const newRecommendations = [...this.data.recommendations];
      if (newRecommendations[index]) {
        newRecommendations[index].snapshot = defaultImage;
        this.setData({ recommendations: newRecommendations });
      }
    }
  },

  // 添加验证图片URL的辅助方法
  validateImageUrl(url) {
    if (!url) return '';
    if (typeof url !== 'string') return '';
    if (!url.startsWith('http') && !url.startsWith('/')) return '';
    return url;
  },

  // 显示反馈窗口
  showFeedback(e) {
    const { type } = e.currentTarget.dataset;
    this.setData({
      showFeedbackModal: true,
      feedbackType: type
    });
  },

  // 关闭反馈窗口
  closeFeedback() {
    this.setData({
      showFeedbackModal: false,
      feedbackContent: ''
    });
  },

  // 处理反馈内容变化
  onFeedbackInput(e) {
    this.setData({
      feedbackContent: e.detail.value
    });
  },

  // 提交反馈
  async submitFeedback() {
    if (!this.data.feedbackContent.trim()) {
      wx.showToast({
        title: '请输入反馈内容',
        icon: 'none'
      });
      return;
    }
    
    try {
      wx.showLoading({
        title: '提交中...'
      });

      const response = await api.submitFeedback({
        openid: this.data.openid,
        content: this.data.feedbackContent,
        contactInfo: this.data.contactInfo,
        timestamp: Date.now()
      });

      wx.hideLoading();
      
      if (response.success) {
        wx.showToast({
          title: '感谢您的反馈！',
          icon: 'success'
        });
        
        // 清空输入内容并关闭窗口
        this.setData({
          showFloatingWindow: false,
          feedbackContent: '',
          contactInfo: ''
        });
      } else {
        throw new Error(response.message || '提交失败');
      }
    } catch (error) {
      console.error('提交反馈失败:', error);
      wx.hideLoading();
      wx.showToast({
        title: error.message || '提交失败，请重试',
        icon: 'none'
      });
    }
  },

  toggleFloatingWindow() {
    this.setData({
      showFloatingWindow: !this.data.showFloatingWindow
    });
  },

  handleFloatingItemTap(e) {
    const { id } = e.currentTarget.dataset;
    // 处理点击事件
    console.log('点击了项目:', id);
    // 这里可以添加具体的处理逻辑
  },

  onContactInput(e) {
    this.setData({
      contactInfo: e.detail.value
    });
  }
});
