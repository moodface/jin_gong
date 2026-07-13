App({globalData:{apiBase:'http://139.155.99.106:8000',userInfo:null},onLaunch(){wx.getSystemInfo({success:function(res){this.globalData.systemInfo=res}})}})
