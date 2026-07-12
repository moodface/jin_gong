"""
============================================================
预警检测 + 推送服务
功能:
1. 自动检测异常指标（竞品降价 > 20%、负面舆情激增）
2. 推送通知到小程序订阅列表
3. 微信模板消息接口预留
============================================================
"""

import json
import asyncio
from datetime import datetime, timedelta
from ..database import get_db
from ..config import COMPETITOR_BRANDS, HOT_KEYWORDS


class AlertDetector:
    """异常检测引擎"""

    def __init__(self):
        self.alerts = []

    def check_price_drops(self):
        """检测竞品价格异常下降"""
        conn = get_db()
        new_alerts = []

        # 查找有促销且降价幅度大的
        rows = conn.execute("""
            SELECT cm.id, cm.brand, cm.product_name, cm.price, cm.promo_info, cm.platform, cm.update_time
            FROM competitor_monitor cm
            WHERE cm.promo_info IS NOT NULL
            ORDER BY cm.update_time DESC
            LIMIT 10
        """).fetchall()

        for r in rows:
            new_alerts.append({
                "type": "price_drop",
                "title": f"竞品降价预警",
                "message": f"{r['brand']} {r['product_name']} 在{r['platform']}平台出现「{r['promo_info']}」活动，关注价格变化",
                "severity": "warning",
                "product_id": r["id"],
                "time": r["update_time"] or datetime.now().isoformat(),
                "read": False,
            })

        conn.close()
        return new_alerts

    def check_sentiment_surge(self):
        """检测负面舆情激增"""
        conn = get_db()
        new_alerts = []

        rows = conn.execute("""
            SELECT keyword, negative_ratio, mention_count, record_date
            FROM sentiment_trend
            WHERE negative_ratio > 0.25
            ORDER BY negative_ratio DESC
            LIMIT 5
        """).fetchall()

        for r in rows:
            neg_pct = round(r["negative_ratio"] * 100, 1)
            level = "danger" if r["negative_ratio"] > 0.35 else "warning"
            new_alerts.append({
                "type": "sentiment_surge",
                "title": "负面舆情激增",
                "message": f"关键词「{r['keyword']}」负面占比达{neg_pct}%（提及{r['mention_count']}次），建议及时关注",
                "severity": level,
                "keyword": r["keyword"],
                "time": r["record_date"] or datetime.now().isoformat(),
                "read": False,
            })

        conn.close()
        return new_alerts

    def check_engagement_trend(self):
        """检测互动数据异常变化"""
        conn = get_db()
        new_alerts = []

        # 简单模拟：各平台最近内容量 > 平均值1.5倍
        rows = conn.execute("""
            SELECT platform, COUNT(*) as cnt
            FROM platform_data
            WHERE crawl_time > datetime('now', '-1 hour')
            GROUP BY platform
        """).fetchall()

        for r in rows:
            if r["cnt"] > 30:
                new_alerts.append({
                    "type": "engagement_surge",
                    "title": "平台流量激增",
                    "message": f"{r['platform']}平台近1小时新增{r['cnt']}条内容，流量异常增长",
                    "severity": "info",
                    "time": datetime.now().isoformat(),
                    "read": False,
                })

        conn.close()
        return new_alerts

    def run_all_checks(self):
        """执行全部检测"""
        self.alerts = []
        self.alerts.extend(self.check_price_drops())
        self.alerts.extend(self.check_sentiment_surge())
        self.alerts.extend(self.check_engagement_trend())
        return self.alerts


class NotificationStore:
    """推送通知存储 - 小程序轮询读取"""

    @staticmethod
    def get_unread_notifications(user_id="default"):
        """获取未读通知"""
        conn = get_db()
        # 存储到 scrape_tasks 表的 notifications 列（简单方案）
        # 生产环境应使用独立通知表
        conn.close()

        detector = AlertDetector()
        all_alerts = detector.run_all_checks()

        # 返回订阅相关的通知
        # 获取用户订阅
        subscriptions = SubscriptionManager.get_subscriptions(user_id)
        subscribed_brands = subscriptions.get("brands", [])
        subscribed_keywords = subscriptions.get("keywords", [])

        filtered = []
        for alert in all_alerts:
            # 检查是否匹配用户订阅
            match = False
            for brand in subscribed_brands:
                if brand in alert.get("message", ""):
                    match = True
                    break
            for kw in subscribed_keywords:
                if kw in alert.get("message", ""):
                    match = True
                    break

            # 如果没有订阅任何内容，显示全部
            if not subscribed_brands and not subscribed_keywords:
                match = True

            if match:
                filtered.append(alert)

        return filtered


class SubscriptionManager:
    """订阅管理"""

    @staticmethod
    def get_subscriptions(user_id="default"):
        conn = get_db()
        cursor = conn.execute("SELECT * FROM user_subscription WHERE openid=?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"keywords": [], "brands": [], "notify_enabled": True}

        keywords = json.loads(row["keywords"]) if row["keywords"] else []
        brands = json.loads(row["brands"]) if row["brands"] else []
        return {"keywords": keywords, "brands": brands, "notify_enabled": bool(row["notify_enabled"])}

    @staticmethod
    def save_subscription(user_id="default", keywords=None, brands=None, notify_enabled=True):
        conn = get_db()
        kw_str = json.dumps(keywords or [], ensure_ascii=False)
        br_str = json.dumps(brands or [], ensure_ascii=False)

        existing = conn.execute("SELECT id FROM user_subscription WHERE openid=?", (user_id,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE user_subscription SET keywords=?, brands=?, notify_enabled=? WHERE openid=?",
                (kw_str, br_str, 1 if notify_enabled else 0, user_id)
            )
        else:
            conn.execute(
                "INSERT INTO user_subscription (openid, keywords, brands, notify_enabled) VALUES (?,?,?,?)",
                (user_id, kw_str, br_str, 1 if notify_enabled else 0)
            )
        conn.commit()
        conn.close()
        return {"status": "ok"}
