App({globalData:{apiBase:'http://192.168.1.7:8000',userInfo:null},onLaunch(){wx.getSystemInfo({success:function(res){this.globalData.systemInfo=res}})}})
