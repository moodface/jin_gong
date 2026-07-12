"""
============================================================
Redis 缓存层 + 任务队列
技术展示：
1. 缓存热门数据 (Dashboard/Trending)
2. 任务队列 (异步爬取)
3. 限流计数器
4. 会话存储

安装: pip install redis
生产环境: docker run -d -p 6379:6379 redis:7-alpine
开发环境可选: pip install fakeredis (无需安装Redis服务)
============================================================
"""

import os
import json
import time
import hashlib
from typing import Optional, Any


class RedisConfig:
    """Redis 配置 - 生产/开发环境"""
    HOST = os.getenv("REDIS_HOST", "localhost")
    PORT = int(os.getenv("REDIS_PORT", "6379"))
    DB = int(os.getenv("REDIS_DB", "0"))
    PASSWORD = os.getenv("REDIS_PASSWORD", None)
    PREFIX = "jingong:"


class CacheService:
    """缓存服务 - Python版Redis Client + 内存回退"""
    def __init__(self):
        self._redis = None
        self._use_memory = True
        self._memory_cache = {}
        self._memory_ttl = {}

    def _init_redis(self):
        if self._redis is not None:
            return
        try:
            import redis
            self._redis = redis.Redis(
                host=RedisConfig.HOST,
                port=RedisConfig.PORT,
                db=RedisConfig.DB,
                password=RedisConfig.PASSWORD,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            self._redis.ping()
            self._use_memory = False
            print("[Redis] 连接成功")
        except Exception as e:
            print(f"[Redis] 连接失败({e})，使用内存缓存回退")
            self._use_memory = True

    def _key(self, key: str) -> str:
        return f"{RedisConfig.PREFIX}{key}"

    def get(self, key: str) -> Optional[str]:
        key = self._key(key)
        if self._use_memory:
            now = time.time()
            if key in self._memory_ttl and self._memory_ttl[key] < now:
                del self._memory_cache[key]
                del self._memory_ttl[key]
                return None
            return self._memory_cache.get(key)
        self._init_redis()
        if self._redis:
            try:
                return self._redis.get(key)
            except:
                return None
        return None

    def set(self, key: str, value: str, ttl: int = 300) -> bool:
        key = self._key(key)
        if self._use_memory:
            self._memory_cache[key] = value
            self._memory_ttl[key] = time.time() + ttl
            return True
        self._init_redis()
        if self._redis:
            try:
                return self._redis.setex(key, ttl, value)
            except:
                return False
        return False

    def delete(self, key: str) -> bool:
        key = self._key(key)
        if self._use_memory:
            self._memory_cache.pop(key, None)
            self._memory_ttl.pop(key, None)
            return True
        self._init_redis()
        if self._redis:
            try:
                return self._redis.delete(key) > 0
            except:
                return False
        return False

    def incr(self, key: str, amount: int = 1, ttl: int = 60) -> int:
        """限流计数器 - 分钟级别"""
        key = self._key(key)
        if self._use_memory:
            now = time.time()
            if key in self._memory_ttl and self._memory_ttl[key] < now:
                self._memory_cache[key] = 0
                self._memory_ttl[key] = now + ttl
            if key not in self._memory_cache:
                self._memory_cache[key] = 0
                self._memory_ttl[key] = now + ttl
            self._memory_cache[key] += amount
            return self._memory_cache[key]
        self._init_redis()
        if self._redis:
            try:
                val = self._redis.incrby(key, amount)
                self._redis.expire(key, ttl)
                return val
            except:
                return 0
        return 0


# ============================================================
# 单例
# ============================================================
cache = CacheService()


# ============================================================
# 装饰器 - 缓存 API 响应
# ============================================================
def cached(ttl: int = 300, key_prefix: str = "api"):
    """缓存装饰器 - 自动缓存函数返回值"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(str(kwargs).encode()).hexdigest()[:8]}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data)

            result = await func(*args, **kwargs) if callable(getattr(func, '__await__', None)) else func(*args, **kwargs)
            cache.set(cache_key, json.dumps(result, ensure_ascii=False, default=str), ttl)
            return result
        return wrapper
    return decorator


# ============================================================
# 任务队列 (简单版 - 生产环境用 Celery/RQ)
# ============================================================
class TaskQueue:
    """基于 Redis List 的轻量级任务队列"""
    QUEUE_KEY = "task_queue"

    @classmethod
    def push(cls, task_data: dict) -> bool:
        task_json = json.dumps(task_data)
        return cache.set(f"{cls.QUEUE_KEY}:{time.time()}", task_json, ttl=3600)

    @classmethod
    def pop(cls) -> Optional[dict]:
        # 生产环境应使用 BLPOP
        for key in list(cache._memory_cache.keys()) if cache._use_memory else []:
            if cls.QUEUE_KEY in key:
                data = cache.get(key.replace(RedisConfig.PREFIX, ""))
                if data:
                    cache.delete(key.replace(RedisConfig.PREFIX, ""))
                    return json.loads(data)
        return None
