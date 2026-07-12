import asyncio
import random
from datetime import datetime
from ..database import get_db
from ..config import HOT_KEYWORDS

# 模拟抖音热榜数据 - 真实场景可用 Playwright 爬取
DOUYIN_HOT_LIST = [
    {"rank": 1, "title": "零添加酱油真的健康吗", "hot": 9820000, "category": "美食"},
    {"rank": 2, "title": "酱油脱脂技术新突破", "hot": 7650000, "category": "科技"},
    {"rank": 3, "title": "厨房小白也能做的三杯鸡", "hot": 6540000, "category": "美食"},
    {"rank": 4, "title": "海天酱油vs千禾酱油盲测", "hot": 5430000, "category": "美食"},
    {"rank": 5, "title": "有机调味品选购指南", "hot": 4320000, "category": "生活"},
    {"rank": 6, "title": "老抽和生抽到底什么区别", "hot": 3980000, "category": "美食"},
    {"rank": 7, "title": "蚝油新吃法挑战", "hot": 3650000, "category": "美食"},
    {"rank": 8, "title": "每天做饭的调味品推荐", "hot": 3210000, "category": "生活"},
    {"rank": 9, "title": "减盐酱油测评", "hot": 2980000, "category": "美食"},
    {"rank": 10, "title": "调味品行业发展趋势", "hot": 2760000, "category": "财经"},
]


async def scrape_douyin_hot_list():
    conn = get_db()
    now = datetime.now().isoformat()

    # AI生成 - 实际场景使用 Playwright 或官方API
    # from playwright.async_api import async_playwright
    # async with async_playwright() as p:
    #     browser = await p.chromium.launch()
    #     page = await browser.new_page()
    #     await page.goto("https://www.douyin.com/hot")
    #     ...

    for item in DOUYIN_HOT_LIST:
        conn.execute(
            "INSERT INTO platform_data (platform,data_type,content,author,likes,publish_time,crawl_time,sentiment,content_type,raw_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                "抖音", "hot_list", item["title"],
                "抖音热榜", item["hot"], now,
                now, "neutral", "热搜",
                str(item)
            )
        )

    # 更新任务状态
    conn.execute(
        "UPDATE scrape_tasks SET status='completed', end_time=?, records_fetched=? WHERE platform='抖音' AND status='running'",
        (now, len(DOUYIN_HOT_LIST))
    )
    conn.commit()
    conn.close()
    return len(DOUYIN_HOT_LIST)


async def run_scrape_task(platform: str = "抖音"):
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO scrape_tasks (platform,status,start_time) VALUES (?,?,?)",
        (platform, "running", now)
    )
    conn.commit()
    conn.close()

    try:
        count = await scrape_douyin_hot_list()
        return {"platform": platform, "status": "completed", "records": count}
    except Exception as e:
        conn = get_db()
        conn.execute(
            "UPDATE scrape_tasks SET status='failed', error_msg=? WHERE platform=? AND status='running'",
            (str(e), platform)
        )
        conn.commit()
        conn.close()
        return {"platform": platform, "status": "failed", "error": str(e)}
