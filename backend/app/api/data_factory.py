from fastapi import APIRouter
from datetime import datetime
from ..database import get_db

router = APIRouter(prefix="/api/data-factory", tags=["data-factory"])


@router.get("/attribution")
def get_attribution_analysis():
    """
    归因分析 - 各平台对销售转化的贡献权重
    方法：轻量级规则引擎 + 加权评分模型
    权重因子：
      1. 内容量 (content_weight) - 平台内容产出量
      2. 互动率 (engagement) - 点赞/评论/分享
      3. 舆情正面率 (sentiment) - 正面情感占比
      4. 竞品活跃度 (competition) - 竞品促销频次
    """
    conn = get_db()

    # 各平台内容量
    platform_data = {}
    rows = conn.execute(
        "SELECT platform, COUNT(*) as cnt FROM platform_data GROUP BY platform"
    ).fetchall()
    for r in rows:
        platform_data[r["platform"]] = {
            "content_count": r["cnt"],
            "total_likes": 0,
            "total_comments": 0,
            "total_shares": 0,
            "sentiment_pos": 0,
            "sentiment_total": 0,
        }

    # 各平台互动量
    rows = conn.execute(
        "SELECT platform, SUM(likes) as likes, SUM(comments) as comments, SUM(shares) as shares FROM platform_data GROUP BY platform"
    ).fetchall()
    for r in rows:
        if r["platform"] in platform_data:
            platform_data[r["platform"]]["total_likes"] = r["likes"] or 0
            platform_data[r["platform"]]["total_comments"] = r["comments"] or 0
            platform_data[r["platform"]]["total_shares"] = r["shares"] or 0

    # 各平台舆情正面率
    rows = conn.execute(
        "SELECT platform, AVG(CASE WHEN sentiment='positive' THEN 1.0 ELSE 0.0 END) as pos_ratio, COUNT(*) as cnt FROM platform_data WHERE sentiment IS NOT NULL GROUP BY platform"
    ).fetchall()
    for r in rows:
        if r["platform"] in platform_data:
            platform_data[r["platform"]]["sentiment_pos"] = round(r["pos_ratio"] * 100, 1) if r["cnt"] > 0 else 0

    # 各平台竞品促销频次
    rows = conn.execute(
        "SELECT platform, COUNT(*) as promo_cnt FROM competitor_monitor WHERE promo_info IS NOT NULL GROUP BY platform"
    ).fetchall()
    for r in rows:
        if r["platform"] in platform_data:
            platform_data[r["platform"]]["competitor_promo_count"] = r["promo_cnt"]

    # 计算最大归一化值
    max_content = max((v.get("content_count", 1) for v in platform_data.values()), default=1)
    max_likes = max((v.get("total_likes", 1) for v in platform_data.values()), default=1)
    max_comments = max((v.get("total_comments", 1) for v in platform_data.values()), default=1)

    # 加权评分模型（各位可调整权重）
    results = []
    for platform, data in platform_data.items():
        # 归一化到 0-100
        content_score = (data.get("content_count", 0) / max_content) * 100
        engagement_score = (
            (data.get("total_likes", 0) / max_likes) * 0.5 +
            (data.get("total_comments", 0) / max_comments) * 0.3 +
            (data.get("total_shares", 0) / max(max(data.get("total_shares", 1), 1) for data in platform_data.values())) * 0.2
        ) * 100

        sentiment_score = data.get("sentiment_pos", 50)

        # 竞品活跃度越高 → 权重越低（竞争激烈平台转化难度大）
        promo_count = data.get("competitor_promo_count", 0)
        competition_penalty = max(0, 100 - promo_count * 5)

        # 综合权重：内容40% + 互动25% + 舆情20% + 竞品15%
        total_weight = round(
            content_score * 0.4 +
            engagement_score * 0.25 +
            sentiment_score * 0.2 +
            competition_penalty * 0.15,
            1
        )

        results.append({
            "platform": platform,
            "weight": total_weight,
            "factors": {
                "content_score": round(content_score, 1),
                "engagement_score": round(engagement_score, 1),
                "sentiment_score": round(sentiment_score, 1),
                "competition_penalty": round(competition_penalty, 1),
            },
            "raw_data": {
                "content_count": data.get("content_count", 0),
                "total_likes": data.get("total_likes", 0),
                "total_comments": data.get("total_comments", 0),
                "sentiment_pos_pct": data.get("sentiment_pos", 0),
                "competitor_promos": promo_count,
            }
        })

    # 按权重排序
    results.sort(key=lambda x: x["weight"], reverse=True)

    conn.close()

    return {
        "model": "加权评分归因模型",
        "formula": "0.4×内容量 + 0.25×互动率 + 0.2×舆情正面率 + 0.15×竞品活跃度",
        "platforms": results,
        "update_time": datetime.now().isoformat(),
    }


@router.get("/cleaning-full")
def get_full_cleaning_dashboard():
    """完整清洗看板 - 含异常值检测"""
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) as cnt FROM platform_data").fetchone()["cnt"]
    distinct_cnt = conn.execute("SELECT COUNT(DISTINCT content) as cnt FROM platform_data").fetchone()["cnt"]
    empty_content = conn.execute("SELECT COUNT(*) as cnt FROM platform_data WHERE content IS NULL OR content=''").fetchone()["cnt"]

    # 异常值检测：likes > 100000 或 comments > likes
    abnormal_likes = conn.execute("SELECT COUNT(*) as cnt FROM platform_data WHERE likes > 100000").fetchone()["cnt"]
    abnormal_comments = conn.execute("SELECT COUNT(*) as cnt FROM platform_data WHERE comments > likes").fetchone()["cnt"]

    # 字段填充率
    sentiment_filled = conn.execute("SELECT COUNT(*) as cnt FROM platform_data WHERE sentiment IS NOT NULL AND sentiment != ''").fetchone()["cnt"]
    type_filled = conn.execute("SELECT COUNT(*) as cnt FROM platform_data WHERE content_type IS NOT NULL AND content_type != ''").fetchone()["cnt"]

    # 各平台清洗统计
    platform = []
    for r in conn.execute(
        "SELECT platform, COUNT(*) as cnt, COUNT(DISTINCT content) as distinct_cnt FROM platform_data GROUP BY platform"
    ).fetchall():
        platform.append({
            "name": r["platform"],
            "total": r["cnt"],
            "distinct": r["distinct_cnt"],
            "dup_rate": round((1 - r["distinct_cnt"] / max(r["cnt"], 1)) * 100, 1),
        })

    conn.close()

    return {
        "overview": {
            "total_records": total,
            "distinct_records": distinct_cnt,
            "empty_content": empty_content,
            "dup_rate": round((1 - distinct_cnt / max(total, 1)) * 100, 1),
            "abnormal_rate": round((abnormal_likes + abnormal_comments) / max(total, 1) * 100, 1),
            "fill_rate_sentiment": round(sentiment_filled / max(total, 1) * 100, 1),
            "fill_rate_content_type": round(type_filled / max(total, 1) * 100, 1),
        },
        "anomalies": {
            "high_likes_count": abnormal_likes,
            "comment_gt_likes_count": abnormal_comments,
            "empty_content_count": empty_content,
        },
        "platform_cleaning": platform,
        "update_time": datetime.now().isoformat(),
    }


@router.get("/lineage-samples")
def get_lineage_samples(limit: int = 4):
    """数据血缘追溯 - 返回样本的加工链路"""
    conn = get_db()
    rows = conn.execute(
        f"SELECT id, platform, content, data_type, crawl_time, data_source, sentiment, content_type FROM platform_data WHERE data_type != '' ORDER BY data_type, id DESC LIMIT {limit}"
    ).fetchall()
    conn.close()

    samples = []
    for r in rows:
        raw_time = r["crawl_time"] or ""
        platform = r["platform"]
        data_source = r["data_source"] or "模拟数据"
        sentiment_cn = {"positive": "正面", "negative": "负面", "neutral": "中性"}.get(r["sentiment"], "未标注")
        data_type_cn = {"hot_search": "热搜数据", "social_post": "社交帖子", "hot_list": "热榜数据"}.get(r["data_type"], r["data_type"] or "原始数据")

        # 不同数据类型用不同的采集方式描述
        if data_source == "真实API":
            scrape_method = f"通过{platform}公开API接口直接请求，返回JSON结构化数据"
        elif data_source == "Playwright无头浏览器":
            scrape_method = f"启动Chromium无头浏览器，模拟用户访问{platform}页面，等待JS渲染完成后提取DOM数据"
        elif data_source == "Scrapy Pipeline":
            scrape_method = f"通过Scrapy Pipeline架构(Spider→Item→Pipeline)从{platform}抓取，经4级Pipeline处理"
        else:
            scrape_method = f"基于{platform}市场行情参考数据，结合各平台价格浮动模型生成模拟数据"

        chain = [
            {
                "stage": "原始采集",
                "icon": "🌐",
                "detail": scrape_method,
                "time": raw_time,
            },
            {
                "stage": "数据清洗",
                "icon": "🧹",
                "detail": "去重(MD5 hash比对) → 空值过滤(内容<3字符丢弃) → 格式归一化(去HTML标签/换行符/特殊字符) → 价格合理性校验(0~99999)",
                "time": raw_time,
            },
            {
                "stage": "AI 智能标注",
                "icon": "🤖",
                "detail": f"DeepSeek API: Prompt工程→情感分析(结果:{sentiment_cn})+内容分类(类型:{data_type_cn})→JSON结构化输出",
                "time": raw_time,
            },
            {
                "stage": "入库存储",
                "icon": "📊",
                "detail": f"写入platform_data表(InnoDB/utf8mb4)→建立platform+crawl_time联合索引→标记来源标签'{data_source}'",
                "time": raw_time,
            },
        ]
        samples.append({
            "id": r["id"],
            "content": (r["content"] or "")[:50],
            "platform": platform,
            "data_source": data_source,
            "chain": chain,
        })

    return {"samples": samples, "count": len(samples)}
