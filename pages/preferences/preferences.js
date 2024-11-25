import api from '../../services/api';

Page({
  data: {
    preferences: {
      diningScene: '',
      diningStyles: [],
      flavorPreferences: [],
      alcoholAttitude: '',
      restrictions: '',
      customDescription: '',
      extractedKeywords: []
    },
    diningScenes: [
      '舒适居家餐',
      '和朋友一起热闹吃饭',
      '一个人快速解决一餐',
      '想尝试新鲜特别的东西',
      '不确定，随便推荐'
    ],
    diningStyleOptions: [
      '外卖/堂食快餐',
      '正餐（如中餐、西餐）',
      '夜宵小吃',
      '咖啡甜点',
      '酒吧或酒馆'
    ],
    flavorOptions: [
      '惊喜浓烈（如辣、鲜、重口味）',
      '清淡健康（如沙拉、低脂餐）',
      '温暖治愈（如汤品、炖菜）',
      '甜蜜快乐（如甜点、果味）'
    ],
    alcoholOptions: [
      '喜欢搭配酒精饮品',
      '只喝无酒精饮品',
      '视情况而定'
    ]
  },

  handleSceneChange(e) {
    this.setData({
      'preferences.diningScene': e.detail.value
    });
  },

  handleStylesChange(e) {
    this.setData({
      'preferences.diningStyles': e.detail.value
    });
  },

  handleFlavorChange(e) {
    this.setData({
      'preferences.flavorPreferences': e.detail.value
    });
  },

  handleAlcoholChange(e) {
    this.setData({
      'preferences.alcoholAttitude': e.detail.value
    });
  },

  handleRestrictionsInput(e) {
    this.setData({
      'preferences.restrictions': e.detail.value
    });
  },

  handleCustomDescriptionInput(e) {
    const description = e.detail.value;
    this.setData({
      'preferences.customDescription': description
    });
    this.extractKeywords(description);
  },

  extractKeywords(text) {
    const keywords = text
      .split(/[,，。.、\s]/)
      .filter(word => word.length > 1)
      .slice(0, 3);
    
    this.setData({
      'preferences.extractedKeywords': keywords
    });
  },

  handleSubmit() {
    const { preferences } = this.data;
    
    if (!preferences.diningScene) {
      wx.showToast({
        title: '请选择饮食场景',
        icon: 'none'
      });
      return;
    }

    wx.showLoading({
      title: '保存中...'
    });

    // 调用API保存用户偏好
    api.submitPreferences(preferences)
      .then(() => {
        wx.hideLoading();
        wx.reLaunch({
          url: '/pages/index/index'
        });
      })
      .catch(error => {
        console.error('保存偏好失败:', error);
        wx.hideLoading();
        wx.showToast({
          title: '保存失败，请重试',
          icon: 'none'
        });
      });
  }
}); 