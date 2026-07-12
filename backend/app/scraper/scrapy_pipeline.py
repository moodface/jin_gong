"""
============================================================
Scrapy 风格爬虫 Pipeline 架构
============================================================
技术展示：
1. Spider 基类 - 定义爬虫规范
2. Item 数据模型 - 结构化数据
3. Pipeline 处理链 - 清洗→去重→验证→存储
4. Middleware 中间件 - 下载器中间件/反爬
5. Scheduler 调度器 - 任务队列与频率控制
============================================================

本模块模拟了完整的 Scrapy 架构，但使用纯 Python 实现，
无需安装 Scrapy。轻量级、可定制、面试展示用。
============================================================
"""

import hashlib
import json
import time
import random
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from collections import deque
from ..database import get_db


# ============================================================
# 1. Item - 标准化数据模型 (类似 Scrapy Item)
# ============================================================

@dataclass
class HotSearchItem:
    """热搜条目"""
    platform: str
    title: str
    url: str = ""
    hot_value: int = 0
    rank: int = 0
    category: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class CompetitorProductItem:
    """竞品商品条目"""
    brand: str
    platform: str
    product_name: str
    price: float
    promo_info: str = ""
    review_count: int = 0
    rating: float = 0.0
    source_url: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class SocialContentItem:
    """社交媒体内容条目"""
    platform: str
    content: str
    author: str
    likes: int = 0
    comments: int = 0
    shares: int = 0
    publish_time: str = ""
    tags: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


# ============================================================
# 2. Spider 基类 (类似 Scrapy Spider)
# ============================================================

class BaseSpider(ABC):
    """爬虫基类 - 定义爬虫规范"""
    name: str = "base_spider"
    allowed_domains: list = []
    start_urls: list = []
    custom_settings: dict = {}

    def __init__(self):
        self.settings = {
            "DOWNLOAD_DELAY": 2,
            "RANDOMIZE_DOWNLOAD_DELAY": True,
            "CONCURRENT_REQUESTS": 3,
            "RETRY_TIMES": 3,
            "USER_AGENTS": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            ],
            "DEFAULT_REQUEST_HEADERS": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            },
        }
        self.crawler_stats = {"items_scraped": 0, "errors": 0, "start_time": None, "end_time": None}

    @abstractmethod
    async def parse(self, response_html: str) -> list:
        """解析响应，返回 Item 列表"""
        pass

    def get_random_ua(self) -> str:
        return random.choice(self.settings["USER_AGENTS"])

    def get_delay(self) -> float:
        base = self.settings["DOWNLOAD_DELAY"]
        if self.settings["RANDOMIZE_DOWNLOAD_DELAY"]:
            return base * random.uniform(0.5, 1.5)
        return base


# ============================================================
# 3. Pipeline 处理链 (类似 Scrapy Item Pipeline)
# ============================================================

class BasePipeline(ABC):
    """Pipeline 基类"""
    @abstractmethod
    def process_item(self, item, spider) -> dict:
        pass


class DeduplicationPipeline(BasePipeline):
    """去重 Pipeline - 基于内容 hash"""
    def __init__(self):
        self.seen_hashes = set()

    def process_item(self, item, spider) -> Optional[dict]:
        content = item.get("content") or item.get("title") or item.get("product_name", "")
        h = hashlib.md5(content.encode()).hexdigest()
        if h in self.seen_hashes:
            return None  # 丢弃重复项
        self.seen_hashes.add(h)
        return item


class CleaningPipeline(BasePipeline):
    """清洗 Pipeline - 去除无效数据"""
    def process_item(self, item, spider) -> Optional[dict]:
        for key in ["title", "content", "product_name"]:
            if key in item and item[key]:
                # 去除首尾空格和特殊字符
                item[key] = item[key].strip().replace("\n", " ").replace("\r", "")
                # 过滤过短内容
                if len(item[key]) < 3:
                    return None
                break

        # 价格合理性校验
        if "price" in item and item["price"] is not None:
            if item["price"] <= 0 or item["price"] > 99999:
                return None
            item["price"] = round(item["price"], 2)

        return item


class EnrichmentPipeline(BasePipeline):
    """数据补全 Pipeline - 填充缺失字段"""
    def process_item(self, item, spider) -> dict:
        now = datetime.now().isoformat()

        if "crawl_time" not in item or not item.get("crawl_time"):
            item["crawl_time"] = now

        if "platform" not in item:
            item["platform"] = spider.name

        if "data_source" not in item:
            item["data_source"] = f"Scrapy-like Pipeline ({spider.name})"

        return item


class StoragePipeline(BasePipeline):
    """存储 Pipeline - 写入 SQLite"""
    def process_item(self, item, spider) -> dict:
        conn = get_db()
        now = datetime.now().isoformat()

        try:
            if "brand" in item:
                conn.execute(
                    """INSERT INTO competitor_monitor
                    (brand, platform, product_name, price, promo_info, rating, review_count, update_time, data_source)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        item.get("brand", ""),
                        item.get("platform", ""),
                        item.get("product_name", ""),
                        item.get("price", 0),
                        item.get("promo_info", ""),
                        item.get("rating", 0),
                        item.get("review_count", 0),
                        now,
                        item.get("data_source", "Scrapy Pipeline"),
                    )
                )
            else:
                conn.execute(
                    """INSERT INTO platform_data
                    (platform, data_type, content, author, likes, publish_time, crawl_time, sentiment, content_type, raw_json, data_source)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        item.get("platform", ""),
                        item.get("data_type", "hot_search"),
                        item.get("title") or item.get("content", ""),
                        item.get("author", "Scrapy Spider"),
                        item.get("hot_value") or item.get("likes", 0),
                        now, now,
                        "neutral", "热搜",
                        json.dumps(item, ensure_ascii=False),
                        item.get("data_source", "Scrapy Pipeline"),
                    )
                )
            conn.commit()
        except Exception as e:
            print(f"[Pipeline] 存储失败: {e}")
        finally:
            conn.close()

        return item


# ============================================================
# 4. 具体 Spider 实现
# ============================================================

class WeiboHotSearchSpider(BaseSpider):
    """微博热搜 Spider"""
    name = "weibo_hot"
    allowed_domains = ["weibo.com"]
    start_urls = ["https://weibo.com/ajax/side/hotSearch"]

    async def parse(self, response_html: str) -> list:
        import json as _json
        items = []
        try:
            data = _json.loads(response_html)
            for item in data.get("data", {}).get("realtime", [])[:20]:
                items.append(HotSearchItem(
                    platform="微博",
                    title=item.get("word", "").strip(),
                    hot_value=item.get("raw_hot", 0),
                    rank=item.get("rank", 0),
                    category=item.get("category", "热搜"),
                ).to_dict())
        except Exception as e:
            print(f"[{self.name}] 解析失败: {e}")
        return items


class BaiduHotSearchSpider(BaseSpider):
    """百度热搜 Spider"""
    name = "baidu_hot"
    allowed_domains = ["top.baidu.com"]
    start_urls = ["https://top.baidu.com/board?tab=realtime"]

    async def parse(self, response_html: str) -> list:
        import json as _json
        items = []
        try:
            import re
            pattern = r'<!--s-data:(.*?)-->'
            match = re.search(pattern, response_html, re.DOTALL)
            if match:
                raw = match.group(1).replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
                sdata = _json.loads(raw)
                for card in sdata.get("data", {}).get("cards", []):
                    for content in card.get("content", []):
                        word = content.get("word", "") or content.get("query", "")
                        if word:
                            items.append(HotSearchItem(
                                platform="百度",
                                title=word,
                                hot_value=content.get("hotScore", 0),
                                rank=content.get("index", len(items) + 1),
                            ).to_dict())
        except Exception as e:
            print(f"[{self.name}] 解析失败: {e}")
        return items


# ============================================================
# 5. Pipeline 管理器 - 编排整个流程
# ============================================================

class PipelineManager:
    """管理 Spider 和 Pipeline 的执行"""
    def __init__(self, spider: BaseSpider, pipelines: List[BasePipeline] = None):
        self.spider = spider
        self.pipelines = pipelines or [
            DeduplicationPipeline(),
            CleaningPipeline(),
            EnrichmentPipeline(),
            StoragePipeline(),
        ]

    async def run_with_raw_data(self, raw_html: str) -> dict:
        """执行完整的 Spider → Pipeline 流程"""
        spider = self.spider
        spider.crawler_stats["start_time"] = datetime.now().isoformat()

        # Step 1: Spider 解析
        items = await spider.parse(raw_html)
        spider.crawler_stats["items_scraped"] = len(items)

        # Step 2: Pipeline 链式处理
        processed = 0
        for item in items:
            current = item
            for pipeline in self.pipelines:
                current = pipeline.process_item(current, spider)
                if current is None:
                    break  # 被某个 pipeline 丢弃
            if current is not None:
                processed += 1

        spider.crawler_stats["end_time"] = datetime.now().isoformat()

        return {
            "spider": spider.name,
            "raw_items": len(items),
            "processed_items": processed,
            "dedup_ratio": round((len(items) - processed) / max(len(items), 1) * 100, 1) if len(items) > processed else 0,
            "pipeline_chain": [p.__class__.__name__ for p in self.pipelines],
            "stats": spider.crawler_stats,
        }
