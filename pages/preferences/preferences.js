import api from '../../services/api';

Page({
  data: {
    preferences: {
      gender: '',
      ageRange: '',
      city: '',
      occupation: '',
      lifestyle: [],
      dietaryHabits: [],
      alcoholPreference: '',
      flavorPreferences: [],
      restaurantTypes: [],
      preferredDrinks: [],
      foodExperience: '',
      specialPreferences: ''
    },
    ageRanges: ['18-24岁', '25-34岁', '35-44岁', '45-54岁', '55岁以上'],
    occupations: ['学生', '上班族', '自由职业', '企业主', '其他']
  },

  handleInputChange(e) {
    const { field } = e.currentTarget.dataset;
    const value = e.detail.value;
    this.setData({
      [`preferences.${field}`]: value
    });
  },

  handlePickerChange(e) {
    const { field } = e.currentTarget.dataset;
    const { value } = e.detail;
    
    const dataSource = {
      ageRange: this.data.ageRanges,
      occupation: this.data.occupations
    }[field];

    this.setData({
      [`preferences.${field}`]: dataSource[value]
    });
  },

  handleSubmit() {
    const { preferences } = this.data;
    // 调用API中的方法提交餐饮喜好信息
    api.submitPreferences(preferences)
      .then(res => {
        if (res.success) {
          wx.showToast({
            title: '提交成功',
            icon: 'success'
          });
          // 跳转到首页
          wx.reLaunch({
            url: '/pages/index/index'
          });
        } else {
          wx.showToast({
            title: '提交失败，请重试',
            icon: 'none'
          });
        }
      })
      .catch(error => {
        console.error('提交失败:', error);
        wx.showToast({
          title: '提交失败，请重试',
          icon: 'none'
        });
      });
  }
}); 