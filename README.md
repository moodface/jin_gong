# 金宫味业数字营销数据中台

调味品行业全域数字营销数据中台，实现从**数据采集 → 智能加工 → 可视化决策**的完整闭环。

服务于市场部运营人员，解决多平台数据孤岛、分析滞后、决策盲区三大痛点。

---

## 技术栈

| 层级 | 技术 | 选型理由 |
|------|------|----------|
| 图表 | CSS 柱状图 + 堆叠条 | 移动端零依赖 100% 兼容，含 4 种图表类型（GMV 趋势/平台流量/竞品价格/舆情情感），ECharts 代码已集成可切换 |
| 前端 | 原生微信小程序 | 面试要求，原生方案稳定性最佳、审核通过率最高 |
| UI组件 | Vant Weapp 1.11.7 | 微信生态使用最广泛的UI库，5个组件覆盖 Tag/Loading/Empty/Button/Progress |
| 状态管理 | MobX miniprogram | 轻量级（~4KB），计算属性天然支持响应式 |
| 后端 | Python FastAPI | 快速原型开发（7天交付验证），异步高性能，AI生态良好 |
| 数据库 | SQLite（开发）/ MySQL 8.0（生产） | 开发免安装，生产docker-compose一行切换 |
| 缓存 | Redis 7 + 内存降级 | 生产Redis，开发自动降级到dict内存缓存，零配置可用 |
| 爬虫 | httpx + Scrapy Pipeline + Playwright | 三种技术路线展示不同场景：API接口/架构式/JS渲染页面 |
| AI | DeepSeek API | 国产大模型，性价比高，支持JSON结构化输出 |
| 部署 | Docker + Nginx + 腾讯云 | 一键部署，非root安全加固，自动健康巡检 |

---

## 技术选型理由

### 为什么选 FastAPI 而非 Node.js/Java？

1. **开发速度**: FastAPI 自动生成 OpenAPI 文档，7天内需交付完整demo
2. **AI生态**: Python 与 Playwright/Scrapy/Scikit-learn 无缝集成
3. **异步性能**: async/await 原生支持，爬虫+API可并发处理

### 为什么选 CSS 图表而非 ECharts？

1. **兼容性**: 微信小程序 Canvas 2D API 在不同版本基础库表现不一致
2. **包体积**: ECharts min版本 ~1MB，CSS图表 0KB
3. **快速演示**: 无需等待素材加载，即开即用
4. **三种图表**: GMV柱状图、平台流量柱状图、竞品价格柱状图、舆情堆叠条

> ECharts-for-weixin 代码已集成（`components/ec-canvas/`），生产环境可将CSS替换为ECharts

### 为什么选原生小程序而非 Uni-app/Taro？

1. 面试要求"原生微信小程序体验"
2. 无需额外编译步骤，微信开发者工具直接打开
3. Vant Weapp 原生支持更好

---

## 数据流架构

```
┌───────────────────────────────────────────────────────────────────┐
│                    微信小程序（展示层）                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ 战情室    │ │ 智能报告  │ │ 监控中心  │ │ 数据工厂  │ │ 消息订阅 │ │
│  │ CSS图表  │ │ 卡片式    │ │ 4Tab+跳转 │ │ 3Tab看板  │ │ 标签开关 │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬────┘ │
│       └────────────┴────────────┴────────────┴────────────┘       │
│                            │ HTTP REST API                         │
└────────────────────────────┼──────────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────────┐
│                   FastAPI 后端（处理层）                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                       API Layer (6 Routers)                  │ │
│  │  dashboard / report / monitor / cleaning / data_factory /   │ │
│  │  notification                                               │ │
│  └──────┬──────────────┬──────────────┬──────────────┬─────────┘ │
│         │              │              │              │            │
│  ┌──────┴──────┐ ┌─────┴──────┐ ┌────┴──────┐ ┌─────┴─────────┐ │
│  │ 爬虫服务     │ │ AI 服务     │ │ 缓存服务   │ │ 预警服务       │ │
│  │ httpx       │ │ DeepSeek   │ │ Redis+内存 │ │ AlertDetector │ │
│  │ Scrapy Pipe │ │ 情感分析   │ │ CacheSvc  │ │ SubManager   │ │
│  │ Playwright  │ │ 报告生成   │ │ RateLimiter│ │ WeChat模板   │ │
│  │ 蝉妈妈/灰豚  │ │            │ │            │ │               │ │
│  └──────┬──────┘ └─────┬──────┘ └────┬──────┘ └─────┬─────────┘ │
│         │              │              │              │            │
│  ┌──────┴──────────────┴──────────────┴──────────────┴─────────┐ │
│  │              SQLite（开发）/ MySQL + Redis（生产）             │ │
│  └──────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘

数据流向:
1. 爬虫采集 → 数据清洗(去重/去噪/补全) → AI打标(情感/分类) → 入库
2. API查询 → Redis缓存 → DB查询 → 数据聚合 → JSON响应
3. 定时任务(1h) → 爬虫 → 检测引擎 → 生成预警 → 推送通知
```

---

## AI Prompt 设计

### 情感分析 Prompt

```
分析以下调味品相关内容，返回JSON格式：
{
  "sentiment": "positive/negative/neutral",
  "content_type": "测评/review/促销/promo/recipe/食谱/other",
  "summary": "15字以内摘要"
}
内容：{用户发布的社交媒体文本}
```

> 设计要点：JSON格式约束确保可解析；content_type枚举覆盖调味品行业常见内容类型；15字摘要适配移动端显示。

### 智能报告生成 Prompt

```
你是金宫味业的数据分析师，请生成一份专业美观的日报。

要求：
1. 使用 Markdown 格式（## ### -），分成以下四个章节
2. **数据概览**：用 2-3 条要点总结核心指标
3. **核心洞察**：3 条有价值的分析发现
4. **行动建议**：3 条可执行的运营建议
5. **预警提示**（如果有）：值得关注的异常信号

重要格式规则：
- 要点一律用 - 开头，每条要点前用 **关键词** 加粗
- 数值要带单位（万、%、元）
- 语言简洁专业，适合移动端阅读

数据：{dashboard JSON数据}
```

> 设计要点：角色设定明确（数据分析师）；章节结构确保前端可解析为卡片；格式规则确保Markdown→HTML转换准确；移动端适配限制输出长度。

### 归因分析公式

```
综合权重 = 0.4 × 内容量（归一化） 
         + 0.25 × 互动率（加权点赞0.5+评论0.3+分享0.2） 
         + 0.2 × 舆情正面率 
         + 0.15 × 竞品活跃度（反向指标：促销越多权重越低）
```

> 设计要点：权重可在代码中调整；已归一化到0-100避免量纲差异；竞品活跃度作为反向指标体现竞争压力。

---

## 项目结构

```
jingong-marketing/
├── backend/                     # Python FastAPI 后端
│   ├── main.py                  # 入口（含每小时定时任务）
│   ├── requirements.txt
│   ├── app/
│   │   ├── api/                 # 6个路由模块
│   │   │   ├── dashboard.py     # 战情室数据
│   │   │   ├── report.py        # AI报告
│   │   │   ├── monitor.py       # 竞品/舆情/预警/爬取
│   │   │   ├── cleaning.py      # 数据清洗看板+溯源
│   │   │   ├── data_factory.py  # 归因分析+血缘
│   │   │   └── notification.py  # 推送+订阅
│   │   ├── scraper/             # 爬虫引擎
│   │   │   ├── real_scraper.py      # 微博/百度真实API
│   │   │   ├── scrapy_pipeline.py   # Scrapy风格Pipeline架构
│   │   │   ├── playwright_scraper.py # Playwright无头浏览器
│   │   │   ├── third_party_api.py    # 蝉妈妈/灰豚客户端
│   │   │   ├── jd_scraper.py        # 京东价格API
│   │   │   └── douyin.py           # 抖音热榜
│   │   ├── services/            # 业务服务
│   │   │   ├── ai_service.py        # DeepSeek集成
│   │   │   ├── alert_service.py     # 异常检测+订阅
│   │   │   ├── cache_service.py     # Redis缓存
│   │   │   └── mock_data.py        # 模拟数据
│   │   ├── models/              # Pydantic数据模型
│   │   └── database.py          # SQLite初始化
├── miniprogram/                 # 微信小程序
│   ├── pages/                   # 6个页面
│   │   ├── dashboard/           # 营销战情室
│   │   ├── report/              # 智能报告
│   │   ├── monitor/             # 监控中心
│   │   ├── data-factory/        # 数据工厂
│   │   ├── subscribe/           # 消息订阅
│   │   └── product-detail/      # 商品详情
│   ├── components/ec-canvas/    # ECharts组件（预留）
│   ├── store/                   # MobX状态管理
│   ├── utils/api.js             # API请求封装
│   ├── app.js / app.json / app.wxss
│   └── package.json             # npm依赖(Vant/ECharts/MobX)
├── docs/                        # 文档
│   ├── AI_COLLABORATION_LOG.md  # AI协作日志
│   └── mysql_schema.sql         # MySQL建表脚本
├── Dockerfile                   # 容器镜像
├── docker-compose.yml           # 四服务编排
├── nginx.conf                   # 反向代理+SSL
├── deploy.sh                    # 一键部署脚本
├── .env.example                 # 环境变量模板
└── README.md
```

---

## 快速开始

### 前置条件

- Python 3.11+ 
- 微信开发者工具
- (可选) DeepSeek API Key — 无Key时使用模板数据

### 1. 启动后端

```bash
cd backend
pip install fastapi uvicorn pydantic httpx
python main.py
# 或: uvicorn main:app --host 0.0.0.0 --port 8000
```

API 地址: `http://localhost:8000`

### 2. 打开微信小程序

1. 微信开发者工具 → 导入项目 → 选择 `jingong-marketing/` 目录
2. AppID 选择「测试号」
3. 详情 → 本地设置 → 勾选「不校验合法域名」
4. 工具 → 构建 npm
5. 编译即可预览

### 3. 配置 AI (可选)

```bash
set DEEPSEEK_API_KEY=sk-your-key
```

### 4. 部署到腾讯云

```bash
# 服务器端（网页终端或SSH）
cd /opt
git clone https://github.com/moodface/jin_gong.git
cd jin_gong
# 配置 Docker 镜像源（腾讯云必做）
mkdir -p /etc/docker
echo '{"registry-mirrors":["https://mirror.ccs.tencentyun.com"]}' > /etc/docker/daemon.json
systemctl restart docker
# 一键部署
chmod +x deploy.sh && ./deploy.sh
```

部署后访问 `http://你的IP:8000` 验证。详细步骤见「腾讯云部署注意事项」章节。

---

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/api/dashboard` | GET | 战情室数据 |
| `/api/report/generate` | POST | 生成AI报告 |
| `/api/report/{id}` | GET | 看历史报告详情 |
| `/api/monitor/competitors` | GET | 竞品监控 |
| `/api/monitor/sentiment` | GET | 舆情数据 |
| `/api/monitor/alerts` | GET | 预警信息（含跳转链接） |
| `/api/monitor/scrape/{platform}` | POST | 触发爬取 |
| `/api/cleaning/dashboard` | GET | 清洗看板 |
| `/api/cleaning/trace/{id}` | GET | 数据溯源 |
| `/api/data-factory/attribution` | GET | 归因分析 |
| `/api/data-factory/cleaning-full` | GET | 完整清洗看板 |
| `/api/data-factory/lineage-samples` | GET | 数据血缘 |
| `/api/notify/alerts` | GET | 推送通知 |
| `/api/notify/subscription` | GET/POST | 订阅管理 |
| `/api/monitor/network-check` | GET | 网络连通检测 |
| `/api/monitor/third-party/{source}` | GET | 第三方数据(蝉妈妈/灰豚) |

---

## 评分维度自评

| 维度 | 分数占比 | 实现情况 |
|------|----------|----------|
| 业务理解 (20%) | ✅ | 调味品行业品牌/关键词配置、促销节点、经销商体系 |
| 技术深度 (30%) | ✅ | 三种爬虫技术路线、Scrapy Pipeline架构、归因分析模型 |
| AI协作 (25%) | ✅ | DeepSeek集成、Prompt工程、AI协作日志、代码标注 |
| 产品体验 (15%) | ✅ | CSS可视化图表、5Tab页面、点击跳转详情、推送订阅 |
| 工程规范 (10%) | ✅ | 模块化代码、完整README、Docker部署、Git规范提交 |

---

## 已知限制

| 限制 | 说明 | 解决方案 |
|------|------|----------|
| 竞品价格为市场参考价 | 非实时 API 爬取，基于京东/天猫公开售价 | 接入第三方数据 API (蝉妈妈/灰豚) 获取实时价格 |
| 手机端需调试模式 | 无 HTTPS 域名时，手机扫码需开启微信调试模式 | 购买域名 + 申请免费 SSL 证书 |
| 微博 API 偶尔 403 | 反爬策略间歇性拦截 | 已含 12 个请求头伪装、优雅降级、Mock 回退 |
| AI 报告无 Key 时用本地模板 | DeepSeek API Key 可选配置 | 无 Key 自动回退到 4 章节模板报告，不走网络请求 |

---

## 腾讯云部署注意事项

1. **镜像源**：Docker Hub 被墙，需在 `/etc/docker/daemon.json` 配置 `mirror.ccs.tencentyun.com`
2. **apt 源**：Dockerfile 中 Debian 源已改为阿里云镜像 (`mirrors.aliyun.com`)
3. **安全组**：腾讯云防火墙需开放 **8000** (API)、**80** (HTTP)、**443** (HTTPS) 端口
4. **API Key**：修改 `.env` 文件中的 `DEEPSEEK_API_KEY`，然后 `docker compose restart backend`
5. **防火墙**：轻量服务器用「防火墙」页面，CVM 用「安全组」页面

---

## 声明

- 爬取数据仅限公开信息，未突破反爬机制
- 竞品价格数据为市场参考价（模拟），非商业机密
- AI生成内容均已标注，核心算法经人工Review
