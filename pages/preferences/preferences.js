import api from '../../services/api';

Page({
  data: {
    userInput: '',
    inputPlaceholder: '例如:"想和朋友一起吃火锅,预算人均100左右,最好是安静的环境"',
    historyList: [],
    suggestions: [
      {
        text: '想找一家适合约会的餐厅，环境安静，有情调',
        icon: '💑'
      },
      {
        text: '朋友生日聚会，需要一个能唱生日歌的餐厅',
        icon: '🎂'
      },
      {
        text: '公司团建，需要能容纳20人的包间',
        icon: '👥'
      },
      {
        text: '想吃创意菜，预算充足，追求特别的体验',
        icon: '✨'
      }
    ],
    aiStatus: {
      name: '加载中...',
      mood: '加载中...',
      activity: '加载中...',
      thought: '加载中...'
    },
    openid: '',
    activeTab: 'history',
    currentDate: '',
    showHistory: false,
    showSuggestions: false
  },

  onLoad() {
    const now = new Date();
    const dateStr = `${now.getFullYear()}.${now.getMonth() + 1}.${now.getDate()}`;
    this.setData({
      currentDate: dateStr
    });
    
    this.loadHistory();
    wx.login({
      success: (res) => {
        if (res.code) {
          api.request('/api/wx/openid', {
            method: 'POST',
            data: { code: res.code }
          }).then(openidRes => {
            this.setData({ openid: openidRes.openid });
            this.fetchAIStatus();
          }).catch(err => {
            console.error('获取openid失败:', err);
          });
        }
      }
    });
  },

  fetchAIStatus() {
    const requestData = {
      openid: this.data.openid
    };
    api.getAIStatus(requestData).then(status => {
      this.setData({
        'aiStatus.name': status.name || '未知',
        'aiStatus.mood': status.mood || '未知',
        'aiStatus.activity': status.activity || '未知',
        'aiStatus.thought': status.thought || '未知'
      });
    }).catch(error => {
      console.error('获取AI状态失败:', error);
      wx.showToast({
        title: '获取AI状态失败',
        icon: 'none'
      });
    });
  },

  onShow() {
    this.loadHistory();
    if(this.data.openid) {
      this.fetchAIStatus();
    }
  },

  loadHistory() {
    wx.showLoading({
      title: '加载中...',
      mask: true
    });

    api.getPreferencesHistory()
      .then(res => {
        const historyList = res.data?.history?.map(item => ({
          id: item.id,
          text: item.description,
          timestamp: new Date(item.createdAt).getTime(),
          createdAt: item.createdAt
        })) || [];

        historyList.sort((a, b) => b.timestamp - a.timestamp);

        this.setData({ 
          historyList: historyList.slice(0, 4)
        });
      })
      .catch(error => {
        console.error('获取历史记录失败:', error);
        wx.showToast({
          title: '获取历史记录失败',
          icon: 'none'
        });
      })
      .finally(() => {
        wx.hideLoading();
      });
  },

  handleInputChange(e) {
    this.setData({
      userInput: e.detail.value
    });
  },

  handleHistoryTap(e) {
    const { index, text } = e.currentTarget.dataset;
    
    this.setData({
      [`historyList[${index}].isActive`]: true
    });

    setTimeout(() => {
      this.setData({
        [`historyList[${index}].isActive`]: false,
        userInput: text
      });
    }, 200);
  },

  handleDeleteHistory(e) {
    const { index } = e.currentTarget.dataset;
    const historyItem = this.data.historyList[index];
    
    wx.showLoading({
      title: '删除中...',
      mask: true
    });

    api.deletePreferenceHistory(historyItem.id)
      .then(() => {
        const newHistory = [...this.data.historyList];
        newHistory.splice(index, 1);
        this.setData({ historyList: newHistory });
        
        wx.showToast({
          title: '删除成功',
          icon: 'success'
        });
      })
      .catch(error => {
        console.error('删除失败:', error);
        wx.showToast({
          title: '删除失败',
          icon: 'none'
        });
      })
      .finally(() => {
        wx.hideLoading();
      });
  },

  handleSubmit() {
    const { userInput } = this.data;
    
    if (!userInput.trim()) {
      wx.showToast({
        title: '请输入您的用餐需求',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({
      title: '正在规划...'
    });

    api.submitPreferences({ userInput })
      .then(() => {
        this.loadHistory();
        
        wx.hideLoading();
        wx.navigateTo({
          url: '/pages/index/index',
          success: () => {
            wx.showToast({
              title: '正在为您规划',
              icon: 'success'
            });
          }
        });
      })
      .catch(error => {
        console.error('提交失败:', error);
        wx.hideLoading();
        wx.showToast({
          title: '提交失败，请重试',
          icon: 'none'
        });
      });
  },

  handleSuggestionTap(e) {
    const { text } = e.currentTarget.dataset;
    
    this.setData({
      [`suggestions[${e.currentTarget.dataset.index}].isActive`]: true
    });

    setTimeout(() => {
      this.setData({
        [`suggestions[${e.currentTarget.dataset.index}].isActive`]: false,
        userInput: text
      });
    }, 200);
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({
      activeTab: tab
    });
  },

  toggleHistory() {
    this.setData({
      showHistory: !this.data.showHistory,
      showSuggestions: false
    });
  },

  toggleSuggestions() {
    this.setData({
      showSuggestions: !this.data.showSuggestions,
      showHistory: false
    });
  }
}); 