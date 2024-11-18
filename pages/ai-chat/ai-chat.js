import api from '../../services/api';

Page({
  data: {
    messages: [],
    inputMessage: '',
    scrollToMessage: '',
    isLoading: false,
    location: null,
  },

  onLoad: function() {
    wx.setNavigationBarTitle({
      title: 'AI 助手'
    });
    
    // 添加初始消息
    this.addMessage('ai', '你好！我是你的AI助手。我可以帮你推荐餐厅，你想吃什么类型的食物？');
  },

  // 获取位置信息
  getLocation: function() {
    wx.getLocation({
      type: 'wgs84', // 返回可以用于 `wx.openLocation` 的 GPS 坐标
      success: (res) => {
        const { latitude, longitude } = res;
        this.setData({
          location: { latitude, longitude }
        });
        console.log('当前位置：', latitude, longitude);
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
        if (response.taskInvoker) {
          console.log('Task Invoker:', response.taskInvoker);
        } else {
          console.warn('Task Invoker is undefined');
        }
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
  }
});
