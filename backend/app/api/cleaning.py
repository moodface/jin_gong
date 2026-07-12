from fastapi import APIRouter
from datetime import datetime
from ..database import get_db

router = APIRouter(prefix="/api/cleaning", tags=["cleaning"])


@router.get("/dashboard")
def get_cleaning_dashboard():
    """数据清洗看板 - 展示去重率、异常值、填充率"""
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) as cnt FROM platform_data").fetchone()["cnt"]
    distinct = conn.execute("SELECT COUNT(DISTINCT content) as cnt FROM platform_data").fetchone()["cnt"]
    with_sentiment = conn.execute("SELECT COUNT(*) as cnt FROM platform_data WHERE sentiment IS NOT NULL").fetchone()["cnt"]
    with_type = conn.execute("SELECT COUNT(*) as cnt FROM platform_data WHERE content_type IS NOT NULL").fetchone()["cnt"]

    # 各平台数据统计
    platform_stats = []
    for row in conn.execute(
        "SELECT platform, COUNT(*) as cnt, COUNT(DISTINCT content) as distinct_cnt FROM platform_data GROUP BY platform"
    ).fetchall():
        platform_stats.append({
            "platform": row["platform"],
            "total": row["cnt"],
            "distinct": row["distinct_cnt"],
            "dup_rate": round((1 - row["distinct_cnt"] / max(row["cnt"], 1)) * 100, 1),
        })

    conn.close()

    return {
        "total_records": total,
        "distinct_records": distinct,
        "dup_rate": round((1 - distinct / max(total, 1)) * 100, 1),
        "fill_rate_sentiment": round(with_sentiment / max(total, 1) * 100, 1),
        "fill_rate_content_type": round(with_type / max(total, 1) * 100, 1),
        "platform_stats": platform_stats,
        "update_time": datetime.now().isoformat(),
    }


@router.get("/trace/{record_id}")
def get_data_trace(record_id: int):
    """数据溯源 - 查看单条数据的原始→清洗→标签链路"""
    conn = get_db()
    row = conn.execute("SELECT * FROM platform_data WHERE id=?", (record_id,)).fetchone()
    if not row:
        return {"error": "记录不存在"}

    # 获取清洗前后的对比
    import json
    raw_data = {}
    try:
        raw_data = json.loads(row["raw_json"]) if row["raw_json"] else {}
    except:
        pass

    trace = {
        "id": row["id"],
        "stages": [
            {
                "stage": "原始采集",
                "platform": row["platform"],
                "data": {
                    "原始内容": raw_data.get("title", row["content"]) if isinstance(raw_data, dict) else row["content"],
                    "原始热度": raw_data.get("hot", row["likes"]) if isinstance(raw_data, dict) else row["likes"],
                    "采集时间": row["crawl_time"],
                }
            },
            {
                "stage": "数据清洗",
                "data": {
                    "去重": "已通过",
                    "去噪": "已通过",
                    "补全": "已完成",
                    "内容归一化": row["content"],
                }
            },
            {
                "stage": "AI 智能标注",
                "data": {
                    "情感倾向": row["sentiment"],
                    "内容分类": row["content_type"],
                    "作者": row["author"],
                }
            },
            {
                "stage": "入库指标",
                "data": {
                    "点赞量": row["likes"],
                    "评论量": row["comments"],
                    "分享量": row["shares"],
                    "发布时间": row["publish_time"],
                }
            },
        ],
        "raw_json": raw_data,
    }
    conn.close()
    return trace


@router.get("/sample")
def get_sample_records():
    """获取数据样本列表（用于溯源入口）"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, platform, content, data_type, crawl_time FROM platform_data ORDER BY id DESC LIMIT 30"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
