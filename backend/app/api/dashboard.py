import random
from fastapi import APIRouter
from datetime import datetime
from ..database import get_db
from ..config import COMPETITOR_BRANDS

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard():
    conn = get_db()

    # GMV 模拟计算
    total_gmv = 1286000.00 + hash(datetime.now().strftime("%H")) % 50000

    # GMV 近7日趋势
    gmv_trend = []
    for i in range(7, 0, -1):
        gmv_trend.append({"date": f"07-{i+5:02d}", "value": 150000 + (i * 15000) + (hash(str(i)) % 30000)})

    # 各平台流量占比
    platforms = ["抖音", "小红书", "天猫", "京东"]
    traffic = []
    total_traffic = 0
    for p in platforms:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM platform_data WHERE platform=?",
            (p,)
        ).fetchone()
        traffic.append({"platform": p, "count": row["cnt"] if row else random.randint(100, 500)})
        total_traffic += traffic[-1]["count"]
    for t in traffic:
        t["ratio"] = round(t["count"] / max(total_traffic, 1) * 100, 1)

    # 竞品价格分布
    competitor_data = []
    for brand in COMPETITOR_BRANDS:
        rows = conn.execute(
            "SELECT product_name, price FROM competitor_monitor WHERE brand=?",
            (brand,)
        ).fetchall()
        for r in rows:
            competitor_data.append({"brand": brand, "product": r["product_name"], "price": r["price"]})

    # 舆情情感趋势
    sentiment_data = []
    for k in ["零添加", "有机酱油", "减盐"]:
        row = conn.execute(
            "SELECT keyword, SUM(mention_count) as total, AVG(positive_ratio) as pos, AVG(negative_ratio) as neg FROM sentiment_trend WHERE keyword=? GROUP BY keyword",
            (k,)
        ).fetchone()
        if row:
            sentiment_data.append({
                "keyword": row["keyword"],
                "mentions": row["total"],
                "positive": round(row["pos"] * 100, 1),
                "negative": round(row["neg"] * 100, 1),
                "neutral": round((1 - (row["pos"] + row["neg"])) * 100, 1),
            })

    # 预警信息
    alerts = conn.execute(
        "SELECT COUNT(*) as cnt FROM competitor_monitor WHERE promo_info IS NOT NULL"
    ).fetchone()

    conn.close()

    return {
        "total_gmv": total_gmv,
        "gmv_trend": gmv_trend,
        "platform_traffic": traffic,
        "competitor_prices": competitor_data,
        "sentiment_trend": sentiment_data,
        "alert_count": alerts["cnt"] if alerts else 0,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
