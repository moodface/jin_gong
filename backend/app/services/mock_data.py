import random
from datetime import datetime, timedelta
from ..database import get_db
from ..config import COMPETITOR_BRANDS, HOT_KEYWORDS

PLATFORMS = ["抖音", "小红书", "天猫", "京东"]
CONTENT_TYPES = ["测评", "recipe", "促销", "开箱", "种草"]
SENTIMENTS = ["positive", "negative", "neutral"]

# 基于真实市场行情的产品及参考价格（2026年调味品市场）
PRODUCTS = {
    "海天": [
        {"name": "金标生抽500ml", "price": 9.9},
        {"name": "蚝油700g", "price": 12.9},
        {"name": "老抽王500ml", "price": 8.5},
        {"name": "味极鲜1L", "price": 15.9},
    ],
    "千禾": [
        {"name": "零添加酱油500ml", "price": 18.9},
        {"name": "有机酱油500ml", "price": 29.9},
        {"name": "180天黑豆酱油1L", "price": 22.8},
        {"name": "糯米香醋500ml", "price": 12.9},
    ],
    "李锦记": [
        {"name": "蒸鱼豉油410ml", "price": 10.9},
        {"name": "旧庄蚝油510g", "price": 19.9},
        {"name": "精选生抽500ml", "price": 9.9},
        {"name": "豆瓣酱500g", "price": 8.9},
    ],
    "厨邦": [
        {"name": "特级生抽500ml", "price": 8.9},
        {"name": "蚝油700g", "price": 11.9},
        {"name": "草菇老抽500ml", "price": 7.9},
    ],
    "加加": [
        {"name": "面条鲜500ml", "price": 7.9},
        {"name": "特级生抽500ml", "price": 6.9},
        {"name": "蚝油480g", "price": 9.9},
    ],
}

# 模拟各平台的实时促销（模拟）
PROMOS = {
    "海天": [
        {"platform": "天猫", "promo": "满2件88折"},
        {"platform": "京东", "promo": "买二送一"},
    ],
    "千禾": [
        {"platform": "京东", "promo": "限时满199减30"},
    ],
    "李锦记": [
        {"platform": "天猫", "promo": "第二件半价"},
    ],
    "加加": [
        {"platform": "天猫", "promo": "3件8折"},
    ],
}

# 模拟每个品牌在各平台的价格微调（不同平台价格略不同）
PRICE_VARIANCE = {"天猫": 1.0, "京东": 0.98, "抖音": 0.95, "小红书": 1.05}


def generate_mock_platform_data():
    conn = get_db()
    data = []
    now = datetime.now()
    for _ in range(50):
        platform = random.choice(PLATFORMS)
        sentiment = random.choice(SENTIMENTS)
        content_type = random.choice(CONTENT_TYPES)
        likes = random.randint(10, 50000)
        comments = random.randint(0, likes // 3)
        data.append((
            platform, "social_post",
            f"用户{random.randint(10000,99999)}关于{random.choice(HOT_KEYWORDS)}的内容",
            f"用户_{random.randint(1000,9999)}",
            likes, comments, random.randint(0, likes // 10),
            (now - timedelta(hours=random.randint(0, 72))).isoformat(),
            datetime.now().isoformat(),
            sentiment, content_type,
            "{}", "simulated"
        ))
    conn.executemany(
        "INSERT OR IGNORE INTO platform_data (platform,data_type,content,author,likes,comments,shares,publish_time,crawl_time,sentiment,content_type,raw_json,data_source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        data
    )
    conn.commit()
    conn.close()


def generate_mock_competitor_data():
    conn = get_db()
    data = []
    now = datetime.now().isoformat()
    for brand in COMPETITOR_BRANDS:
        products = PRODUCTS.get(brand, [{"name": "产品A", "price": 15.0}])
        for platform in random.sample(PLATFORMS, k=random.randint(2, 4)):
            for product in random.sample(products, k=min(2, len(products))):
                base_price = product["price"]
                variance = PRICE_VARIANCE.get(platform, 1.0)
                price = round(base_price * variance * random.uniform(0.95, 1.05), 1)

                # 检查是否有促销
                promo = None
                for p_promo in PROMOS.get(brand, []):
                    if p_promo["platform"] == platform and random.random() < 0.5:
                        promo = p_promo["promo"]
                        price = round(price * 0.85, 1)

                data.append((
                    brand, platform, product["name"],
                    price, promo,
                    round(random.uniform(4.3, 4.9), 1),
                    random.randint(2000, 80000),
                    now, "市场参考价"
                ))
    conn.execute("DELETE FROM competitor_monitor")
    conn.executemany(
        "INSERT INTO competitor_monitor (brand,platform,product_name,price,promo_info,rating,review_count,update_time,data_source) VALUES (?,?,?,?,?,?,?,?,?)",
        data
    )
    conn.commit()
    conn.close()


def generate_mock_sentiment_trend():
    conn = get_db()
    data = []
    today = datetime.now().date()
    for keyword in HOT_KEYWORDS:
        for platform in random.sample(PLATFORMS, k=random.randint(2, 4)):
            mentions = random.randint(50, 10000)
            pos = round(random.uniform(0.3, 0.7), 2)
            neg = round(random.uniform(0.05, 0.3), 2)
            data.append((
                keyword, platform, mentions, pos, neg, round(1 - pos - neg, 2),
                today.isoformat(), "AI模拟分析"
            ))
    conn.execute("DELETE FROM sentiment_trend")
    conn.executemany(
        "INSERT INTO sentiment_trend (keyword,platform,mention_count,positive_ratio,negative_ratio,neutral_ratio,record_date,data_source) VALUES (?,?,?,?,?,?,?,?)",
        data
    )
    conn.commit()
    conn.close()


def init_mock_data():
    conn = get_db()
    # 只在表为空时初始化
    existing = conn.execute("SELECT COUNT(*) as cnt FROM platform_data").fetchone()
    if existing["cnt"] == 0:
        generate_mock_platform_data()
        generate_mock_competitor_data()
        generate_mock_sentiment_trend()
    conn.close()
