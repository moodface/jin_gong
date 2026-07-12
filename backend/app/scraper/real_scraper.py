# ================================================================
# 真实数据爬虫 - 微博热搜 + 百度热搜
# AI生成: httpx异步请求基础框架、数据清洗流程
# 人工修改: 微博403反爬处理、浏览器指纹伪装、优雅降级策略、
#           模拟数据回退机制、data_source字段标记
# ================================================================

import httpx
import re
import asyncio
from datetime import datetime
from ..database import get_db
from ..config import HOT_KEYWORDS


# AI生成: 微博API请求基础结构
# 人工修改: 增加12个请求头模拟真实浏览器、403状态码处理、
#           str()捕获异常替代json()崩溃
async def fetch_weibo_hot():
    """微博热搜 - 真实公开API，无需密钥"""
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Referer": "https://weibo.com/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Ch-Ua": '"Chromium";v="130", "Google Chrome";v="130"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Requested-With": "XMLHttpRequest",
    }
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                print(f"[Scraper] 微博返回 {resp.status_code}，使用备用方案")
                return []
            data = resp.json()
            items = []
            for item in data.get("data", {}).get("realtime", [])[:20]:
                word = item.get("word", "").strip()
                if word:
                    items.append({
                        "title": word,
                        "hot": item.get("raw_hot", item.get("num", 0)),
                        "category": item.get("category", "热搜"),
                        "rank": item.get("rank", 0),
                    })
            return items
        except Exception as e:
            print(f"[Scraper] 微博爬取异常: {e}")
            return []


async def fetch_baidu_hot():
    """百度热搜 - 通过官方接口获取"""
    url = "https://top.baidu.com/board?tab=realtime"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers)
        html = resp.text
        # 解析 embedded JSON
        pattern = r'<!--s-data:(.*?)-->'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            import json
            raw = match.group(1)
            # 处理特殊字符转义
            raw = raw.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
            try:
                sdata = json.loads(raw)
            except json.JSONDecodeError:
                return []
            cards = sdata.get("data", {}).get("cards", [])
            items = []
            for card in cards:
                for content in card.get("content", []):
                    word = content.get("word", content.get("query", ""))
                    if word:
                        items.append({
                            "title": word,
                            "hot": content.get("hotScore", content.get("heat_score", 0)),
                            "category": card.get("cardName", "热搜"),
                            "rank": content.get("index", len(items) + 1),
                        })
            return items[:20]

    # fallback: parse HTML
    items = []
    pattern = r'<div[^>]*class="[^"]*content_1YWBm[^"]*"[^>]*>(.*?)</div>'
    matches = re.findall(pattern, html)
    for i, m in enumerate(matches[:20]):
        word = re.sub(r'<.*?>', '', m).strip()
        if word:
            items.append({
                "title": word,
                "hot": 0,
                "category": "热搜",
                "rank": i + 1,
            })
    return items


async def scrape_all_sources():
    """爬取所有数据源，返回原始数据"""
    all_results = {"微博": [], "百度": []}

    try:
        all_results["微博"] = await fetch_weibo_hot()
    except Exception as e:
        print(f"[Scraper] 微博爬取失败: {e}")

    try:
        all_results["百度"] = await fetch_baidu_hot()
    except Exception as e:
        print(f"[Scraper] 百度爬取失败: {e}")

    return all_results


# AI生成: 数据清洗函数骨架 (去重、去噪逻辑)
# 人工修改: 增加空标题过滤、hash去重优化、清洗统计返回
def clean_data(raw_items, platform):
    """数据清洗：去重、去噪、补全"""
    seen_titles = set()
    cleaned = []
    stats = {"total": len(raw_items), "duplicates": 0, "empty_titles": 0, "valid": 0}

    for item in raw_items:
        title = item.get("title", "").strip()
        if not title:
            stats["empty_titles"] += 1
            continue
        if title in seen_titles:
            stats["duplicates"] += 1
            continue
        seen_titles.add(title)
        cleaned.append({
            "title": title,
            "platform": platform,
            "hot_value": item.get("hot", 0),
            "category": item.get("category", "其他"),
            "rank": item.get("rank", 0),
            "crawl_time": datetime.now().isoformat(),
            "raw_data": str(item),
        })
        stats["valid"] += 1

    return cleaned, stats


def filter_relevant(items):
    """关键词过滤：识别调味品/食品行业相关内容"""
    relevant_keywords = HOT_KEYWORDS + ["酱油", "调味", "食品", "餐饮", "厨房", "美食", "食谱", "品牌", "消费",
                                          "海天", "千禾", "李锦记", "生抽", "老抽", "蚝油", "醋", "食用油", "味精"]
    relevant = []
    for item in items:
        title = item["title"]
        matched_keywords = [kw for kw in relevant_keywords if kw in title]
        item["relevance"] = len(matched_keywords) > 0
        item["matched_keywords"] = matched_keywords
        relevant.append(item)
    return relevant


def save_to_db(items, platform):
    """保存清洗后的数据到数据库"""
    conn = get_db()
    now = datetime.now().isoformat()
    count = 0
    for item in items:
        try:
            conn.execute(
                "INSERT INTO platform_data (platform,data_type,content,author,likes,publish_time,crawl_time,sentiment,content_type,raw_json,data_source) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    platform, "hot_search",
                    item["title"],
                    f"{platform}热搜",
                    item.get("hot_value", 0),
                    now, now,
                    "neutral", "热搜",
                    item.get("raw_data", "{}"),
                    "真实API"  # 标记为真实数据
                )
            )
            count += 1
        except Exception as e:
            pass
    conn.commit()
    conn.close()
    return count


async def run_real_scrape():
    """执行真实爬取任务，失败时自动回退到模拟数据"""
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO scrape_tasks (platform,status,start_time) VALUES (?,?,?)",
        ("微博+百度", "running", now)
    )
    conn.commit()
    conn.close()

    results = {"platforms": {}, "cleaning_stats": {}, "total_saved": 0}

    try:
        raw_data = await scrape_all_sources()

        for platform, items in raw_data.items():
            if not items:
                print(f"[Scraper] {platform} 未获取到数据，跳过")
                continue
            cleaned, stats = clean_data(items, platform)
            filtered = filter_relevant(cleaned)
            saved = save_to_db(filtered, platform)
            results["platforms"][platform] = {
                "raw_count": len(items),
                "cleaned_count": len(cleaned),
                "relevant_count": len([i for i in filtered if i["relevance"]]),
                "saved": saved,
            }
            results["cleaning_stats"][platform] = stats
            results["total_saved"] += saved

        # 如果任何真实数据都没获取到，回退到模拟数据
        if results["total_saved"] == 0:
            print("[Scraper] 所有来源均失败，使用模拟数据")
            from ..services.mock_data import generate_mock_platform_data
            generate_mock_platform_data()
            results["total_saved"] = 50
            results["note"] = "网络受限，使用模拟数据"

        conn = get_db()
        conn.execute(
            "UPDATE scrape_tasks SET status='completed', end_time=?, records_fetched=? WHERE platform='微博+百度' AND status='running'",
            (datetime.now().isoformat(), results["total_saved"])
        )
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"[Scraper] 爬取异常: {e}")
        conn = get_db()
        conn.execute(
            "UPDATE scrape_tasks SET status='completed', end_time=?, records_fetched=?, error_msg=? WHERE platform='微博+百度' AND status='running'",
            (datetime.now().isoformat(), 50, f"网络异常({str(e)[:80]})，已使用模拟数据")
        )
        conn.commit()
        conn.close()
        # 回退到模拟数据
        from ..services.mock_data import generate_mock_platform_data
        generate_mock_platform_data()
        results["total_saved"] = 50
        results["note"] = f"异常: {str(e)[:80]}, 已回退到模拟数据"

    return results
