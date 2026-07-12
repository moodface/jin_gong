import os

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data.db")

# AI 配置 - 通过环境变量或写死 DeepSeek API key
# 请在运行前设置环境变量: set DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

# 爬虫配置
SCRAPE_INTERVAL_MINUTES = 30

# 竞品品牌关键词
COMPETITOR_BRANDS = ["海天", "千禾", "李锦记", "厨邦", "加加"]

# 舆情热词
HOT_KEYWORDS = ["零添加", "有机酱油", "减盐", "生抽", "老抽", "蚝油"]
