const api = require('../../services/api');

Page({
  data: {
    pets: [
      {
        id: 1,
        name: '小花猫',
        type: '猫咪',
        description: '活泼可爱的猫咪,喜欢高蛋白食物',
        image: '/images/cat.png',
        dietPreference: '高蛋白',
        recommendedFoods: ['鱼类', '鸡肉', '牛肉'],
        personality: '活泼'
      },
      {
        id: 2, 
        name: '小狗旺财',
        type: '狗狗',
        description: '温顺的狗狗,喜欢营养均衡的食物',
        image: '/images/dog.png',
        dietPreference: '营养均衡',
        recommendedFoods: ['狗粮', '鸡肉', '蔬菜'],
        personality: '温顺'
      },
      {
        id: 3,
        name: '小兔子',
        type: '兔子', 
        description: '可爱的兔子,偏爱素食',
        image: '/images/rabbit.png',
        dietPreference: '素食',
        recommendedFoods: ['胡萝卜', '生菜', '水果'],
        personality: '安静'
      }
    ],
    selectedPet: null,
    isSelecting: false,
    showCustomModal: false,
    customPet: {
      name: '',
      type: '',
      personality: '',
      dietPreference: '',
      foods: '',
      description: ''
    },
    showDetailModal: false,
    currentPet: null
  },

  onLoad() {
    // 修改为正确的方法名
    api.getAISettings().then(res => {
      if(res && res.data) {  // 简化条件判断
        this.setData({
          selectedPet: res.data
        });
      }
    }).catch(err => {
      console.error('获取AI设置失败:', err);
    });
  },

  onPetSelect(e) {
    const petId = e.currentTarget.dataset.id;
    const pet = this.data.pets.find(p => p.id === petId);
    
    this.setData({ 
      currentPet: pet,
      showDetailModal: true
    });
    
    wx.vibrateShort({ type: 'medium' });
  },

  showCustomPetModal() {
    this.setData({
      showCustomModal: true
    });
  },

  hideCustomPetModal() {
    this.setData({
      showCustomModal: false,
      customPet: {
        name: '',
        type: '',
        personality: '',
        dietPreference: '',
        foods: '',
        description: ''
      }
    });
  },

  createCustomPet() {
    const { customPet } = this.data;
    
    if (!customPet.name || !customPet.type) {
      wx.showToast({
        title: '请填写宠物名称和类型',
        icon: 'none'
      });
      return;
    }

    const newPet = {
      id: Date.now(),
      name: customPet.name,
      type: customPet.type,
      description: customPet.description,
      image: '/images/custom-pet.png',
      dietPreference: customPet.dietPreference,
      recommendedFoods: customPet.foods.split(',').map(food => food.trim()),
      personality: customPet.personality
    };

    this.setData({
      pets: [...this.data.pets, newPet],
      showCustomModal: false,
      customPet: {
        name: '',
        type: '',
        personality: '',
        dietPreference: '',
        foods: '',
        description: ''
      }
    });

    wx.showToast({
      title: '创建成功',
      icon: 'success'
    });
  },

  hideDetailModal() {
    this.setData({
      showDetailModal: false,
      currentPet: null
    });
  },

  selectCurrentPet() {
    wx.showLoading({ title: '保存中...' });
    
    api.updateAISettings({
      name: this.data.currentPet.name,
      personality: this.data.currentPet.personality,
      speakingStyle: this.data.currentPet.dietPreference,
      memories: [
        `我是${this.data.currentPet.name}，一只${this.data.currentPet.type}`,
        `我的性格${this.data.currentPet.personality}`,
        `我喜欢${this.data.currentPet.dietPreference}的食物`,
        `我会推荐: ${this.data.currentPet.recommendedFoods.join('、')}`,
        this.data.currentPet.description
      ]
    }).then(() => {
      wx.hideLoading();
      
      // 修改为 navigateTo，避免使用 reLaunch
      wx.switchTab({
        url: '/pages/preferences/preferences',
        success: () => {
          wx.showToast({
            title: '选择成功',
            icon: 'success',
            duration: 1000
          });
        },
        fail: (err) => {
          console.error('页面跳转失败:', err);
          wx.showToast({
            title: '跳转失败',
            icon: 'error'
          });
        }
      });
    }).catch((err) => {
      console.error('保存失败:', err);
      wx.hideLoading();
      wx.showToast({
        title: '保存失败',
        icon: 'error'
      });
    });
  }
}); 