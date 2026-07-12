import asyncio
from fastapi import APIRouter
from ..database import get_db

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


@router.get("/competitors")
def get_competitors():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM competitor_monitor ORDER BY brand, platform"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/competitor/{item_id}")
def get_competitor_detail(item_id: int):
    """获取单个竞品商品的详细数据"""
    import random
    conn = get_db()
    item = conn.execute(
        "SELECT * FROM competitor_monitor WHERE id=?", (item_id,)
    ).fetchone()

    if not item:
        conn.close()
        return {"error": "商品不存在"}

    item_dict = dict(item)

    # 数据来源URL映射
    platform_urls = {
        "京东": "https://search.jd.com/Search?keyword=",
        "天猫": "https://list.tmall.com/search_product.htm?q=",
        "抖音": "https://www.douyin.com/search/",
        "小红书": "https://www.xiaohongshu.com/search_result?keyword=",
    }
    data_source = item_dict.get("data_source", "")
    platform = item_dict.get("platform", "")
    product_name = item_dict.get("product_name", "")

    # 真实API/市场参考价 → 提供跳转链接
    if data_source in ("真实API", "市场参考价", "Playwright无头浏览器", "Scrapy Pipeline"):
        base_url = platform_urls.get(platform, "")
        item_dict["source_url"] = base_url + product_name if base_url else ""
        item_dict["source_clickable"] = True
    else:
        item_dict["source_url"] = ""
        item_dict["source_clickable"] = False

    # 价格历史（模拟近30天）
    base_price = item_dict["price"]
    price_history = []
    for d in range(30, 0, -1):
        price_history.append({
            "day": d,
            "price": round(base_price * (1 + random.uniform(-0.1, 0.08)), 1),
            "flag": "normal" if random.random() > 0.1 else "promo",
        })
    item_dict["price_history"] = price_history

    # 最低/最高/均价
    prices = [p["price"] for p in price_history]
    item_dict["price_lowest"] = round(min(prices), 1)
    item_dict["price_highest"] = round(max(prices), 1)
    item_dict["price_avg"] = round(sum(prices) / len(prices), 1)
    item_dict["price_change"] = round((price_history[-1]["price"] - price_history[0]["price"]) / price_history[0]["price"] * 100, 1)

    # 同品牌其他平台价格
    same_brand = conn.execute(
        "SELECT * FROM competitor_monitor WHERE brand=? AND id!=?", (item_dict["brand"], item_id)
    ).fetchall()
    item_dict["cross_platform"] = [dict(r) for r in same_brand]
    for cp in item_dict["cross_platform"]:
        ds = cp.get("data_source", "")
        pl = cp.get("platform", "")
        pn = cp.get("product_name", "")
        if ds in ("真实API", "市场参考价", "Playwright无头浏览器", "Scrapy Pipeline"):
            cp["source_url"] = (platform_urls.get(pl, "") + pn) if pl else ""
            cp["source_clickable"] = True
        else:
            cp["source_url"] = ""
            cp["source_clickable"] = False

    # 竞品同品类价格（同行竞争对手）
    # 提取产品类别关键词
    category_keywords = []
    name = item_dict.get("product_name", "")
    for kw in ["酱油", "生抽", "老抽", "蚝油", "醋", "豆瓣"]:
        if kw in name:
            category_keywords.append(kw)

    competitors_same_cat = conn.execute(
        "SELECT * FROM competitor_monitor WHERE brand!=? ORDER BY price LIMIT 8",
        (item_dict["brand"],)
    ).fetchall()
    item_dict["same_category"] = [dict(r) for r in competitors_same_cat]
    for sc in item_dict["same_category"]:
        ds = sc.get("data_source", "")
        pl = sc.get("platform", "")
        pn = sc.get("product_name", "")
        if ds in ("真实API", "市场参考价", "Playwright无头浏览器", "Scrapy Pipeline"):
            sc["source_url"] = (platform_urls.get(pl, "") + pn) if pl else ""
            sc["source_clickable"] = True
        else:
            sc["source_url"] = ""
            sc["source_clickable"] = False

    # 模拟评论摘要
    item_dict["review_summary"] = {
        "good": f"品质稳定，{item_dict['brand']}老品牌值得信赖",
        "bad": "价格略高，促销力度不够",
        "tags": ["品质好", "价格适中", "物流快", "包装完好"],
    }

    conn.close()
    return item_dict


@router.get("/sentiment")
def get_sentiment():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sentiment_trend ORDER BY mention_count DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/alerts")
def get_alerts():
    conn = get_db()

    platform_urls = {
        "京东": "https://search.jd.com/Search?keyword=",
        "天猫": "https://list.tmall.com/search_product.htm?q=",
        "抖音": "https://www.douyin.com/search/",
        "小红书": "https://www.xiaohongshu.com/search_result?keyword=",
    }

    alerts = []

    # 检测异常竞品降价
    rows = conn.execute(
        "SELECT id, brand, product_name, price, platform, update_time FROM competitor_monitor WHERE promo_info IS NOT NULL"
    ).fetchall()
    for r in rows:
        pid = r["id"]
        plat = r["platform"]
        pname = r["product_name"]
        alerts.append({
            "type": "竞品促销",
            "message": f"{r['brand']} {pname} 在{plat}有促销活动",
            "severity": "warning",
            "time": r["update_time"] if "update_time" in r.keys() else "",
            "product_id": pid,
            "navigate_type": "product_detail",
            "external_url": (platform_urls.get(plat, "") + pname) if plat in platform_urls else "",
        })

    # 检测负面舆情
    rows = conn.execute(
        "SELECT keyword, negative_ratio, mention_count, record_date FROM sentiment_trend WHERE negative_ratio > 0.2 ORDER BY negative_ratio DESC LIMIT 5"
    ).fetchall()
    for r in rows:
        alerts.append({
            "type": "负面舆情",
            "message": f"关键词「{r['keyword']}」负面舆情占比达{round(r['negative_ratio']*100,1)}%，提及量{r['mention_count']}",
            "severity": "danger",
            "time": r["record_date"] if "record_date" in r.keys() else "",
            "product_id": None,
            "navigate_type": None,
            "external_url": "",
        })

    conn.close()
    return alerts


@router.get("/tasks")
def get_scrape_tasks():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM scrape_tasks ORDER BY start_time DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/scrape/{platform}")
async def trigger_scrape(platform: str):
    if platform == "jd":
        async def run():
            try:
                from ..scraper.jd_scraper import run_jd_scrape
                await run_jd_scrape()
            except Exception as e:
                print(f"[Scraper] JD 爬取失败: {e}")
        asyncio.create_task(run())
        return {"status": "started", "message": "京东爬取任务已在后台启动"}
    elif platform == "playwright":
        async def run():
            try:
                from ..scraper.playwright_scraper import playwright_scrape_douyin_hot
                await playwright_scrape_douyin_hot()
            except Exception as e:
                print(f"[Scraper] Playwright 爬取失败: {e}")
        asyncio.create_task(run())
        return {"status": "started", "message": "Playwright 无头浏览器爬取任务已启动"}
    elif platform == "pipeline":
        async def run():
            await run_scrapy_pipeline_demo()
        asyncio.create_task(run())
        return {"status": "started", "message": "Scrapy Pipeline 演示已启动"}
    else:
        async def run():
            try:
                from ..scraper.real_scraper import run_real_scrape
                await run_real_scrape()
            except Exception as e:
                print(f"[Scraper] 爬取失败: {e}")
        asyncio.create_task(run())
        return {"status": "started", "message": "爬取任务已在后台启动"}


async def run_scrapy_pipeline_demo():
    """演示完整的 Scrapy Pipeline 流程"""
    import httpx
    from ..scraper.scrapy_pipeline import (
        WeiboHotSearchSpider, BaiduHotSearchSpider, PipelineManager,
        DeduplicationPipeline, CleaningPipeline, EnrichmentPipeline, StoragePipeline
    )
    from ..database import get_db
    from datetime import datetime

    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute("INSERT INTO scrape_tasks (platform,status,start_time) VALUES (?,?,?)",
                 ("Scrapy Pipeline", "running", now))
    conn.commit()
    conn.close()

    results = {}
    pipelines = [DeduplicationPipeline(), CleaningPipeline(), EnrichmentPipeline(), StoragePipeline()]

    # 微博
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://weibo.com/ajax/side/hotSearch",
                headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                spider = WeiboHotSearchSpider()
                mgr = PipelineManager(spider, pipelines)
                results["微博"] = await mgr.run_with_raw_data(resp.text)
    except Exception as e:
        results["微博"] = {"error": str(e)}

    # 百度
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://top.baidu.com/board?tab=realtime",
                headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                spider = BaiduHotSearchSpider()
                mgr = PipelineManager(spider, pipelines)
                results["百度"] = await mgr.run_with_raw_data(resp.text)
    except Exception as e:
        results["百度"] = {"error": str(e)}

    conn = get_db()
    total = sum(r.get("processed_items", 0) for r in results.values() if isinstance(r, dict))
    conn.execute(
        "UPDATE scrape_tasks SET status=?, end_time=?, records_fetched=? WHERE platform='Scrapy Pipeline' AND status='running'",
        ("completed", datetime.now().isoformat(), total)
    )
    conn.commit()
    conn.close()


@router.get("/third-party/{source}")
async def get_third_party_data(source: str):
    """获取第三方数据平台的数据"""
    from ..scraper.third_party_api import fetch_from_third_party
    result = await fetch_from_third_party(source)
    return result


@router.get("/network-check")
async def network_check():
    """快速检测爬虫目标网络连通性"""
    import httpx
    results = {}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get("https://weibo.com/ajax/side/hotSearch",
                headers={"User-Agent": "Mozilla/5.0"})
            results["微博热搜"] = {"status": r.status_code, "ok": True}
        except Exception as e:
            results["微博热搜"] = {"status": "失败", "ok": False, "error": str(e)[:80]}

        try:
            r = await client.get("https://www.baidu.com/",
                headers={"User-Agent": "Mozilla/5.0"})
            results["百度"] = {"status": r.status_code, "ok": True}
        except Exception as e:
            results["百度"] = {"status": "失败", "ok": False, "error": str(e)[:80]}

    return results
