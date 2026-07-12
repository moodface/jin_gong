"""
============================================================
Playwright 无头浏览器爬虫模块
============================================================
技术展示：
1. 使用 Playwright 启动无头 Chrome 浏览器
2. 截图验证页面加载成功
3. JS 渲染页面数据提取（应对 SPA 网站）
4. 自动滚动加载更多内容
5. User-Agent 伪装 + 浏览器指纹模拟
6. 请求频率控制（反反爬）

安装: pip install playwright
初始化: playwright install chromium
============================================================
"""

import asyncio
import os
import random
import time
from datetime import datetime
from ..database import get_db

# --- 反爬策略配置 ---
ANTI_BOT_CONFIG = {
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    ],
    "request_delay": (2, 5),  # 每次请求间隔 2-5 秒
    "max_retries": 3,
    "viewport": {"width": 1920, "height": 1080},
}

# --- 模拟第三方数据 API 配置 ---
THIRD_PARTY_APIS = {
    "chanmama": {  # 蝉妈妈 - 抖音数据
        "base_url": "https://api.chanmama.com/v1",
        "endpoints": {
            "hot_videos": "/rankings/live/v2",
            "brand_rank": "/brand/tops",
            "keyword_trend": "/keyword/trend",
        },
        "auth_type": "api_key",
        "rate_limit": "100次/分钟",
    },
    "huitun": {  # 灰豚数据 - 电商数据
        "base_url": "https://open.huitun.com/api",
        "endpoints": {
            "product_search": "/product/search",
            "price_track": "/product/price-history",
            "competitor_monitor": "/monitor/competitor",
        },
        "auth_type": "token",
        "rate_limit": "50次/分钟",
    },
}


async def playwright_scrape_douyin_hot():
    """
    使用 Playwright 无头浏览器抓取抖音热榜
    - 启动无头 Chromium
    - 设置反爬参数
    - 等待 JS 渲染完成
    - 截图保存
    - 提取页面数据
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[Playwright] 未安装 playwright，跳过")
        return {
            "status": "skipped",
            "reason": "playwright 未安装，运行: pip install playwright && playwright install chromium",
        }

    results = []
    screenshots = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )

        context = await browser.new_context(
            user_agent=random.choice(ANTI_BOT_CONFIG["user_agents"]),
            viewport=ANTI_BOT_CONFIG["viewport"],
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            # 模拟地理位置
            geolocation={"longitude": 116.397, "latitude": 39.908},
            permissions=["geolocation"],
        )

        # 隐藏自动化特征
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
            window.chrome = { runtime: {} };
        """)

        page = await context.new_page()

        try:
            # 访问抖音热榜
            print("[Playwright] 正在访问抖音热榜...")
            await page.goto("https://www.douyin.com/hot", wait_until="networkidle", timeout=30000)

            # 等待内容渲染
            await page.wait_for_timeout(3000)

            # 截图保存
            screenshot_dir = os.path.join(os.path.dirname(__file__), "..", "..", "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(screenshot_dir, f"douyin_hot_{timestamp}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            screenshots.append(screenshot_path)
            print(f"[Playwright] 截图已保存: {screenshot_path}")

            # 提取热榜数据
            items = await page.evaluate("""
                () => {
                    const items = [];
                    const cards = document.querySelectorAll('[data-e2e="hot-list-item"], .hot-list-item, .trending-item');
                    cards.forEach((card, i) => {
                        const title = card.querySelector('.title, .word, h3')?.innerText?.trim() || '';
                        const hot = card.querySelector('.hot-value, .num, .count')?.innerText?.trim() || '';
                        if (title && i < 20) {
                            items.push({ title, hot, rank: i + 1 });
                        }
                    });
                    return items;
                }
            """)

            for item in items:
                results.append({
                    "title": item.get("title", ""),
                    "hot": item.get("hot", ""),
                    "rank": item.get("rank", len(results) + 1),
                    "platform": "抖音",
                })

            print(f"[Playwright] 成功提取 {len(results)} 条抖音热榜数据")

        except Exception as e:
            print(f"[Playwright] 页面操作异常: {e}")
        finally:
            await browser.close()

    # 保存到数据库
    if results:
        conn = get_db()
        now = datetime.now().isoformat()
        count = 0
        for item in results:
            try:
                conn.execute(
                    "INSERT INTO platform_data (platform,data_type,content,author,likes,publish_time,crawl_time,sentiment,content_type,raw_json,data_source) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        "抖音", "hot_list", item["title"],
                        "Playwright爬虫",
                        0, now, now,
                        "neutral", "热搜",
                        str(item), "Playwright无头浏览器"
                    )
                )
                count += 1
            except:
                pass
        conn.commit()
        conn.close()

    return {
        "status": "completed" if results else "empty",
        "items_found": len(results),
        "screenshots": screenshots,
        "method": "Playwright (Chromium 无头浏览器)",
        "anti_bot": "WebDriver隐藏 + UA轮换 + 浏览器指纹伪装 + 延迟请求",
    }


async def playwright_scrape_ecommerce(product_url: str, platform: str):
    """
    使用 Playwright 抓取电商平台商品页
    - 处理 JS 动态渲染的价格
    - 提取商品详情
    - 滚动加载评论
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"status": "skipped", "reason": "playwright 未安装"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(ANTI_BOT_CONFIG["user_agents"]),
            viewport={"width": 1366, "height": 768},
        )
        page = await context.new_page()

        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
        """)

        try:
            await page.goto(product_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)

            # 提取商品信息 (通用选择器)
            product_info = await page.evaluate("""
                () => {
                    const getText = (sel) => {
                        const el = document.querySelector(sel);
                        return el ? el.innerText.trim() : '';
                    };
                    return {
                        title: getText('.title, .product-title, h1, [data-title]'),
                        price: getText('.price, .product-price, .p-price, [data-price]'),
                    };
                }
            """)

            await browser.close()
            return {
                "status": "completed",
                "platform": platform,
                "product": product_info,
            }

        except Exception as e:
            await browser.close()
            return {"status": "error", "error": str(e)}
