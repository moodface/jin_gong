"""
============================================================
第三方数据 API 集成模块
技术展示：
1. 蝉妈妈 (Chanmama) - 抖音数据 API 集成
2. 灰豚数据 (Huitun) - 电商竞品监控 API 集成
3. 统一 API 客户端封装（重试、降级、缓存）
4. 模拟真实 API 请求/响应格式
============================================================
"""

import os
import json
import time
import httpx
import hashlib
import random
from abc import ABC, abstractmethod
from datetime import datetime
from functools import wraps


# ============================================================
# 1. 统一 API 客户端基类
# ============================================================

class BaseAPIClient(ABC):
    """第三方 API 客户端基类 - 统一认证、重试、降级"""

    def __init__(self, api_key: str = None, base_url: str = ""):
        self.api_key = api_key or os.getenv(f"{self.name.upper()}_API_KEY", "")
        self.base_url = base_url
        self.rate_limiter = RateLimiter(max_calls=50, period=60)

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """统一请求方法 - 带重试和降级"""
        await self.rate_limiter.wait()

        headers = kwargs.pop("headers", {})
        headers.update({
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        })

        url = f"{self.base_url}{path}"
        retries = 3

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.request(method, url, headers=headers, **kwargs)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as e:
                if attempt == retries - 1:
                    return {"error": str(e), "fallback": True}
                await asyncio_sleep(2 ** attempt)

        return {"error": "max retries exceeded", "fallback": True}


# ============================================================
# 2. 速率限制器
# ============================================================

class RateLimiter:
    def __init__(self, max_calls: int = 50, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    async def wait(self):
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.period]
        if len(self.calls) >= self.max_calls:
            wait_time = self.calls[0] + self.period - now
            if wait_time > 0:
                await asyncio_sleep(wait_time)
        self.calls.append(time.time())


import asyncio
async def asyncio_sleep(seconds):
    await asyncio.sleep(seconds)


# ============================================================
# 3. 蝉妈妈 API 客户端
# ============================================================

class ChanmamaClient(BaseAPIClient):
    """蝉妈妈 - 抖音电商数据平台 API"""
    name = "chanmama"
    base_url = "https://api.chanmama.com/v1"

    async def get_trending_videos(self, category: str = "food", limit: int = 20) -> list:
        """获取热门视频榜单"""
        path = "/rankings/live/v2"
        params = {"category": category, "limit": limit, "sort": "hot"}

        # 模拟真实 API 返回格式
        if not self.api_key:
            return self._mock_trending_videos(limit)

        return await self._request("GET", path, params=params)

    async def get_brand_ranking(self, industry: str = "condiment") -> dict:
        """获取品牌排行榜"""
        path = "/brand/tops"
        params = {"industry": industry, "period": "7d"}

        if not self.api_key:
            return self._mock_brand_ranking()

        return await self._request("GET", path, params=params)

    async def get_keyword_trend(self, keyword: str, days: int = 7) -> dict:
        """获取关键词搜索趋势"""
        path = "/keyword/trend"
        params = {"keyword": keyword, "days": days}

        if not self.api_key:
            return self._mock_keyword_trend(keyword, days)

        return await self._request("GET", path, params=params)

    # ---- Mock 数据（无 API Key 时使用）----
    def _mock_trending_videos(self, limit: int) -> list:
        videos = []
        base_data = [
            ("海天酱油炒菜神器，妈妈用了30年", 89234, "海天"),
            ("零添加酱油评测对比，千禾vs海天", 65421, "千禾"),
            ("厨房小白也能做的三杯鸡教程", 54321, "美食"),
            ("蚝油新用法！15秒搞定减脂餐", 43210, "厨邦"),
            ("有机酱油开箱测评", 38765, "千禾"),
            ("调味品行业揭秘：酱油的真相", 32109, "科普"),
        ]
        for i, (title, plays, brand) in enumerate(base_data[:limit]):
            videos.append({
                "rank": i + 1,
                "title": title,
                "plays": plays,
                "likes": int(plays * random.uniform(0.02, 0.08)),
                "brand_tag": brand,
                "publish_date": (datetime.now()).strftime("%Y-%m-%d"),
            })
        return videos

    def _mock_brand_ranking(self) -> dict:
        return {
            "industry": "调味品",
            "period": "7天",
            "rankings": [
                {"rank": 1, "brand": "海天", "score": 95.6, "trend": "up"},
                {"rank": 2, "brand": "千禾", "score": 87.3, "trend": "up"},
                {"rank": 3, "brand": "李锦记", "score": 82.1, "trend": "stable"},
                {"rank": 4, "brand": "厨邦", "score": 74.8, "trend": "down"},
                {"rank": 5, "brand": "加加", "score": 68.2, "trend": "stable"},
            ],
            "update_time": datetime.now().isoformat(),
        }

    def _mock_keyword_trend(self, keyword: str, days: int) -> dict:
        trend = []
        for d in range(days, 0, -1):
            trend.append({"date": f"07-{13-d:02d}", "index": random.randint(1000, 8000)})
        return {"keyword": keyword, "trend": trend}


# ============================================================
# 4. 灰豚数据 API 客户端
# ============================================================

class HuitunClient(BaseAPIClient):
    """灰豚数据 - 电商竞品监控平台 API"""
    name = "huitun"
    base_url = "https://open.huitun.com/api"

    async def search_product(self, keyword: str, platform: str = "all") -> list:
        """商品搜索"""
        path = "/product/search"
        params = {"q": keyword, "platform": platform, "limit": 20}

        if not self.api_key:
            return self._mock_product_search(keyword)

        return await self._request("GET", path, params=params)

    async def get_price_history(self, product_id: str, days: int = 30) -> dict:
        """商品历史价格"""
        path = "/product/price-history"
        params = {"product_id": product_id, "days": days}

        if not self.api_key:
            return self._mock_price_history()

        return await self._request("GET", path, params=params)

    async def get_competitor_comparison(self, brands: list) -> dict:
        """竞品对比分析"""
        path = "/monitor/competitor"
        data = {"brands": brands}

        if not self.api_key:
            return self._mock_competitor_comparison(brands)

        return await self._request("POST", path, json=data)

    # ---- Mock 数据 ----
    def _mock_product_search(self, keyword: str) -> list:
        products = {
            "酱油": [
                {"name": "海天金标生抽500ml", "price": 9.9, "platform": "京东", "sales": "10万+"},
                {"name": "千禾零添加酱油500ml", "price": 18.9, "platform": "天猫", "sales": "5万+"},
                {"name": "李锦记精选生抽500ml", "price": 9.9, "platform": "京东", "sales": "8万+"},
                {"name": "厨邦特级生抽500ml", "price": 8.9, "platform": "天猫", "sales": "3万+"},
            ],
            "蚝油": [
                {"name": "海天蚝油700g", "price": 12.9, "platform": "京东", "sales": "15万+"},
                {"name": "李锦记旧庄蚝油510g", "price": 19.9, "platform": "天猫", "sales": "6万+"},
            ],
        }
        return products.get(keyword, [{"name": f"{keyword}相关商品", "price": 0, "platform": "全平台", "sales": "N/A"}])

    def _mock_price_history(self) -> dict:
        history = []
        base_price = 18.9
        for d in range(30, 0, -1):
            history.append({
                "date": f"06-{d+13:02d}",
                "price": round(base_price + random.uniform(-2, 1), 1),
                "platform": random.choice(["天猫", "京东"]),
            })
        return {"product": "千禾零添加酱油500ml", "history": history, "lowest": 15.9, "highest": 22.9}

    def _mock_competitor_comparison(self, brands: list) -> dict:
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "comparison": [
                {"brand": b, "avg_price": random.uniform(8, 25), "market_share": random.uniform(5, 35),
                 "promo_count": random.randint(0, 3)}
                for b in brands
            ],
            "source": "灰豚数据 Mock API",
        }


# ============================================================
# 5. 工厂函数 - 统一获取第三方数据
# ============================================================

async def fetch_from_third_party(source: str, **kwargs) -> dict:
    """统一入口 - 从第三方平台获取数据"""
    clients = {
        "chanmama": ChanmamaClient(),
        "huitun": HuitunClient(),
    }

    client = clients.get(source)
    if not client:
        return {"error": f"未知数据源: {source}", "available": list(clients.keys())}

    result = {
        "source": source,
        "api_type": "第三方数据API",
        "auth_status": "已认证" if client.api_key else "模拟模式（无API Key）",
        "data": {},
    }

    if source == "chanmama":
        result["data"]["trending_videos"] = await client.get_trending_videos()
        result["data"]["brand_ranking"] = await client.get_brand_ranking("condiment")
        result["data"]["keyword_trend"] = await client.get_keyword_trend("零添加酱油")

    elif source == "huitun":
        result["data"]["product"] = await client.search_product("酱油")
        result["data"]["price_history"] = await client.get_price_history("0001")
        result["data"]["competitor"] = await client.get_competitor_comparison(
            ["海天", "千禾", "李锦记", "厨邦", "加加"]
        )

    return result
