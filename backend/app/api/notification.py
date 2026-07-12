from fastapi import APIRouter
from pydantic import BaseModel
from ..services.alert_service import AlertDetector, NotificationStore, SubscriptionManager

router = APIRouter(prefix="/api/notify", tags=["notify"])


class SubscriptionRequest(BaseModel):
    keywords: list = []
    brands: list = []
    notify_enabled: bool = True


@router.get("/alerts")
def get_notifications():
    """获取当前未读通知"""
    alerts = NotificationStore.get_unread_notifications()
    return {"alerts": alerts, "count": len(alerts)}


@router.get("/check")
def run_alert_check():
    """手动触发异常检测"""
    detector = AlertDetector()
    alerts = detector.run_all_checks()
    return {"alerts": alerts, "count": len(alerts)}


@router.get("/subscription")
def get_subscription():
    """获取当前订阅配置"""
    return SubscriptionManager.get_subscriptions()


@router.post("/subscription")
def save_subscription(req: SubscriptionRequest):
    """保存订阅配置"""
    return SubscriptionManager.save_subscription(
        keywords=req.keywords,
        brands=req.brands,
        notify_enabled=req.notify_enabled,
    )


@router.post("/wechat-template")
def send_wechat_template():
    """
    微信模板消息推送（预留接口）
    生产环境配置：
    1. 微信公众平台 → 模板消息 → 申请模板
    2. 获取 access_token（使用 appid + secret）
    3. POST https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token=TOKEN
    
    模板示例:
    {
      "touser": "OPENID",
      "template_id": "TEMPLATE_ID",
      "data": {
        "thing1": {"value": "竞品降价预警"},
        "thing2": {"value": "海天金标生抽降价20%"},
        "time3": {"value": "2026-07-13 10:00"},
        "thing4": {"value": "请及时调整价格策略"}
      }
    }
    """
    return {
        "status": "demo",
        "message": "微信模板消息功能已预留。生产环境需配置appid/secret/template_id",
        "integration_guide": {
            "step1": "微信公众平台 → 功能 → 订阅消息 → 选择模板",
            "step2": "小程序端调用 wx.requestSubscribeMessage 获取用户授权",
            "step3": "后端 /api/notify/wechat-template 发送模板消息",
            "note": "开发环境使用小程序内部通知栏替代（已实现）",
        }
    }
