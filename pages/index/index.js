// index.js
const api = require('../../services/api');

Page({
  data: {
    aiStatus: {
      name: '加载中...',
      mood: '加载中...',
      activity: '加载中...',
      thought: '加载中...',
      name: '加载中...'
    },
    openid: '',
    preferences: {
      summary: '加载中...'
    },
    editingItem: null,
    currentTab: 0
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
          const recommendations = [];
          
          // 分割猜你喜欢和奇思妙想
          const sections = summaryText.split(/- \*\*([^*]+)\*\*：/).filter(Boolean);
          
          for (let i = 0; i < sections.length - 1; i += 2) {
            const type = sections[i];
            const content = sections[i + 1];
            
            // 根据类型设置不同的图标
            const icon = type === '猜你喜欢' ? '💭' : '✨';
            
            // 将内容按句号或分号分割成多个项目
            const items = content.split(/[。；]/).filter(item => item.trim());
            
            const formattedItems = items.map(item => {
              // 提取描述中的加粗文本
              const highlights = [];
              let boldMatch;
              const boldRegex = /「([^」]+)」|『([^』]+)』|\*\*([^*]+)\*\*/g;
              
              while ((boldMatch = boldRegex.exec(item)) !== null) {
                highlights.push(boldMatch[1] || boldMatch[2] || boldMatch[3]);
              }
              
              // 将加粗文本转换为带样式的文本
              const formattedDesc = item.trim()
                .replace(/「([^」]+)」|『([^』]+)』|\*\*([^*]+)\*\*/g, 
                  '<text class="highlight">$1$2$3</text>');

              return {
                description: formattedDesc,
                highlights: highlights
              };
            }).filter(item => item.description);

            if (formattedItems.length > 0) {
              recommendations.push({
                type: type,
                items: formattedItems,
                icon: icon
              });
            }
          }

          this.setData({
            preferences: {
              recommendations: recommendations
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

  handleEdit(e) {
    if (!this.data.openid) return;
    
    const { categoryIndex, itemIndex } = e.currentTarget.dataset;
    console.log('开始编辑:', categoryIndex, itemIndex);
    
    const currentItem = this.data.preferences.recommendations[categoryIndex].items[itemIndex];
    // 移除HTML标签和多余空格
    const plainText = currentItem.description
      .replace(/<[^>]+>/g, '')
      .replace(/&nbsp;/g, ' ')
      .trim();
    
    console.log('编辑文本:', plainText); // 添加日志
    
    this.setData({
      editingItem: {
        categoryIndex,
        itemIndex,
        originalText: plainText
      }
    }, () => {
      // 确保状态更新后再次检查
      console.log('当前编辑状态:', this.data.editingItem);
    });
  },

  handleInput(e) {
    const { value } = e.detail;
    console.log('输入内容:', value); // 添加日志
    
    this.setData({
      'editingItem.originalText': value
    });
  },

  handleSave(e) {
    if (!this.data.editingItem) return;
    
    const newText = this.data.editingItem.originalText;
    const { categoryIndex, itemIndex } = this.data.editingItem;
    
    if (!newText || !newText.trim()) {
      wx.showToast({
        title: '内容不能为空',
        icon: 'none'
      });
      return;
    }
    
    // 更新本地数据
    const recommendations = [...this.data.preferences.recommendations];
    recommendations[categoryIndex].items[itemIndex].description = newText;
    
    // 将数据转换为指定格式
    const formattedData = recommendations.map(category => {
      const items = category.items.map(item => item.description).join('；');
      return `- **${category.type}**：${items}`;
    }).join('\n');
    
    console.log('格式化后的数据:', formattedData); // 添加日志
    
    // 保存更改
    wx.showLoading({ title: '保存中...' });
    api.updatePreferences(
      this.data.openid,
      location,
      formattedData  // 发送格式化后的数据
    ).then(() => {
      this.setData({
        'preferences.recommendations': recommendations,
        editingItem: null
      });
      wx.showToast({ 
        title: '保存成功',
        icon: 'success'
      });
    }).catch(err => {
      console.error('保存失败:', err);
      this.setData({
        editingItem: null
      });
      wx.showToast({ 
        title: '保存失败',
        icon: 'none'
      });
    }).finally(() => {
      wx.hideLoading();
    });
  },

  handleCancel() {
    this.setData({
      editingItem: null
    });
  },

  handleDelete(e) {
    const { categoryIndex, itemIndex } = e.currentTarget.dataset;
    const recommendations = [...this.data.preferences.recommendations];
    const category = recommendations[categoryIndex];
    
    // 检查是否只剩一个项目
    if (category.items.length <= 1) {
      wx.showToast({
        title: '至少保留一项内容',
        icon: 'none'
      });
      return;
    }
    
    // 显示确认对话框
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条内容吗？',
      success: (res) => {
        if (res.confirm) {
          // 删除项目
          category.items.splice(itemIndex, 1);
          
          // 将数据转换为指定格式
          const formattedData = recommendations.map(category => {
            const items = category.items.map(item => item.description).join('；');
            return `- **${category.type}**：${items}`;
          }).join('\n');
          
          // 保存更改
          wx.showLoading({ title: '保存中...' });
          api.updatePreferences(
            this.data.openid,
            location,
            formattedData
          ).then(() => {
            this.setData({
              'preferences.recommendations': recommendations
            });
            wx.showToast({ 
              title: '删除成功',
              icon: 'success'
            });
          }).catch(err => {
            console.error('删除失败:', err);
            wx.showToast({ 
              title: '删除失败',
              icon: 'none'
            });
          }).finally(() => {
            wx.hideLoading();
          });
        }
      }
    });
  },

  handleAdd(e) {
    const { categoryIndex } = e.currentTarget.dataset;
    const recommendations = [...this.data.preferences.recommendations];
    const category = recommendations[categoryIndex];
    
    // 添加新项目
    category.items.push({
      description: '新的推荐内容',
      highlights: []
    });
    
    // 将数据转换为指定格式
    const formattedData = recommendations.map(category => {
      const items = category.items.map(item => item.description).join('；');
      return `- **${category.type}**：${items}`;
    }).join('\n');
    
    // 保存更改
    wx.showLoading({ title: '保存中...' });
    api.updatePreferences(
      this.data.openid,
      location,
      formattedData
    ).then(() => {
      this.setData({
        'preferences.recommendations': recommendations
      });
      // 自动开始编辑新添加的项目
      this.handleEdit({
        currentTarget: {
          dataset: {
            categoryIndex: categoryIndex,
            itemIndex: category.items.length - 1
          }
        }
      });
    }).catch(err => {
      console.error('添加失败:', err);
      wx.showToast({ 
        title: '添加失败',
        icon: 'none'
      });
    }).finally(() => {
      wx.hideLoading();
    });
  },

  switchTab(e) {
    const index = e.currentTarget.dataset.index;
    this.setData({
      currentTab: index
    });
  }
});
