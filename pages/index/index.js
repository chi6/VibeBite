// index.js
const api = require('../../services/api');

Page({
  data: {
    aiStatus: {
      mood: '加载中...',
      activity: '加载中...',
      thought: '加载中...',
      name: '加载中...'
    },
    openid: '',
    preferences: {
      summary: '加载中...'
    }
  },

  onLoad() {
    wx.login({
      success: (res) => {
        if (res.code) {
          api.request('/api/wx/openid', {
            method: 'POST',
            data: { code: res.code }
          }).then(openidRes => {
            this.setData({ openid: openidRes.openid });
            this.fetchAIStatus();
            this.fetchPreferencesSummary();
            this.fetchAISettings();
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

  fetchPreferencesSummary() {
    wx.showLoading({
      title: '加载中...',
      mask: true
    });

    api.getPreferencesSummary().then(res => {
      wx.hideLoading();
      if (res.success && res.data) {
        try {
          const summaryText = res.data.summary;
          const recommendationItems = [];
          
          // 使用正则表达式匹配每个部分
          const sections = summaryText.split(/\n*-\s*\*\*([^*]+)\*\*：/).filter(Boolean);
          
          for (let i = 0; i < sections.length - 1; i += 2) {
            const type = sections[i];
            const content = sections[i + 1].trim();
            
            // 将内容按分号分割成多个建议
            const suggestions = content.split('；').filter(Boolean);
            const items = suggestions.map(suggestion => {
              const text = suggestion.trim();
              
              // 提取加粗文本作为高亮标签
              const highlights = [];
              let boldMatch;
              const boldRegex = /\*\*([^*]+)\*\*/g;
              
              while ((boldMatch = boldRegex.exec(text)) !== null) {
                highlights.push(boldMatch[1]);
              }
              
              // 将加粗文本转换为带样式的文本
              const formattedText = text.replace(/\*\*([^*]+)\*\*/g, '$1');
              
              // 如果是最后一个建议且没有分号结尾，添加句号
              const finalText = formattedText.endsWith('。') ? formattedText : formattedText + '。';
              
              return {
                description: finalText,
                highlights: highlights
              };
            });

            if (items.length > 0) {
              recommendationItems.push({
                type: type,
                items: items,
                icon: this.getIconForType(type)
              });
            }
          }

          this.setData({
            preferences: {
              recommendations: recommendationItems
            }
          });
          
          console.log('解析后的偏好数据:', this.data.preferences);
        } catch (e) {
          console.error('解析偏好数据失败:', e);
          this.setData({
            preferences: {
              recommendations: []
            }
          });
        }
      } else {
        throw new Error('获取数据失败');
      }
    }).catch(error => {
      wx.hideLoading();
      console.error('获取餐饮喜好总结失败:', error);
      this.setData({
        preferences: {
          recommendations: []
        }
      });
    });
  },

  fetchAISettings() {
    api.getAISettings().then(res => {
      console.log('AI设置响应:', res);
      if (res.success && res.data) {
        this.setData({
          'aiStatus.name': res.data.name || 'AI智能助手'
        });
        console.log('更新后的AI名字:', this.data.aiStatus.name);
      } else {
        this.setData({
          'aiStatus.name': 'AI智能助手'
        });
      }
    }).catch(err => {
      console.error('获取AI设置失败:', err);
      this.setData({
        'aiStatus.name': 'AI智能助手'
      });
    });
  },

  goToAIChat() {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        const location = {
          latitude: res.latitude,
          longitude: res.longitude
        };
        
        api.updatePreferences(this.data.openid, location).then(() => {
          wx.navigateTo({
            url: `/pages/ai-chat/ai-chat?openid=${this.data.openid}&aiName=${this.data.aiStatus.name || 'AI 助手'}`,
            fail: (err) => {
              console.error('跳转失败:', err);
              wx.showToast({
                title: '页面跳转失败',
                icon: 'none'
              });
            }
          });
        }).catch(error => {
          console.error('更新偏好失败:', error);
          wx.showToast({
            title: '更新偏好失败',
            icon: 'none'
          });
        });
      },
      fail: (err) => {
        console.error('获取位置失败:', err);
        wx.showToast({
          title: '获取位置失败',
          icon: 'none'
        });
      }
    });
  },

  // 根据类型返回对应的图标
  getIconForType(type) {
    const iconMap = {
      '猜你喜欢': '🤔',
      '奇思妙想': '💡',
      '火锅': '🍲',
      '酒吧': '🍷',
      '饮品': '🥤',
      '咖啡': '☕',
      '甜品': '🍰',
      '烧烤': '🍖',
      '海鲜': '🦞',
      '音乐': '🎵'
    };

    // 遍历 iconMap 找到类型中包含的关键词
    for (const [key, value] of Object.entries(iconMap)) {
      if (type.includes(key)) {
        return value;
      }
    }
    
    return '🎉'; // 默认图标
  }
});
