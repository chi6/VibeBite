Component({
  data: {
    selected: 0,
    list: [
      {
        pagePath: "/pages/preferences/preferences",
        text: "偏好",
        icon: "icon-heart"
      },
      {
        pagePath: "/pages/index/index",
        text: "首页",
        icon: "icon-home"
      },
      {
        pagePath: "/pages/user-profile/user-profile",
        text: "我的",
        icon: "icon-user"
      }
    ]
  },
  methods: {
    switchTab(e) {
      const data = e.currentTarget.dataset;
      const url = data.path;
      wx.switchTab({ url });
      this.setData({
        selected: data.index
      });
    }
  }
}); 