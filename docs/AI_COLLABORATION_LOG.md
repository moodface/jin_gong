# AI 协作日志 — 金宫味业数字营销数据中台

记录使用 OpenCode (Claude Code) 辅助开发的全过程。开发周期：2026年7月6日 - 7月13日。

---

## 项目启动 (7/6)

### 需求理解与架构设计
- **用户提问**: "帮我设计一个方案完成这个项目"（上传实操题文档）
- **AI输出**: 三层架构方案（数据采集层→处理层→展示层）+ 技术选型
- **人工修改**: 补充调味品行业特定品牌配置（海天/千禾/李锦记/厨邦/加加）、行业热门关键词

### 技术选型对话
- **AI建议**: FastAPI (Python) 用于快速原型开发
- **人工确认**: 同意，因为7天内需要交付可运行demo

---

## 后端开发 (7/7 - 7/9)

### FastAPI 项目搭建
- **AI生成**: main.py骨架、API路由模板、数据库初始化
- **人工修改**: 
  - lifespan生命周期逻辑（启动时仅空库填充mock数据）
  - CORS配置（开发阶段允许所有来源）
  - MySQL/Redis双模式切换方案

### 爬虫模块迭代
- **迭代1**: AI生成httpx基础请求框架 → 微博200 OK，数据正常
- **迭代2**: 用户反馈"爬取任务都爬取失败了" → AI诊断：微博403反爬拦截
- **迭代3**: AI加固12个请求头伪装浏览器 + 403优雅降级 + 失败回退模拟数据
- **迭代4**: 用户反馈"技术提示要求Scrapy/Playwright" → AI补充三种技术路线：
  - `scrapy_pipeline.py`: Spider→Item→Dedup→Clean→Enrich→Store 四级Pipeline
  - `playwright_scraper.py`: Chromium无头浏览器 + WebDriver隐藏 + init_script反自动化检测
  - `third_party_api.py`: BaseAPIClient + ChanmamaClient + HuitunClient + RateLimiter

### AI 服务集成
- **AI生成**: DeepSeek API调用模板 + Prompt工程
- **人工修改**: 
  - 调味品行业专属Prompt（标注"零添加"等术语）
  - 无API Key时的模板报告降级方案
  - Markdown→HTML转换引擎
  - 结构化sections输出（概览→洞察→建议→预警）
- **Bug修复**: "日报文字露出< h2>标签" → parse_markdown_sections收到HTML而非Markdown → 分离Markdown解析与HTML生成

---

## 前端开发 (7/10 - 7/13)

### 微信小程序搭建
- **AI生成**: app.json配置、页面路由、基础WXML模板
- **人工修改**: 金宫红配色方案(#C8102E)、TabBar布局

### Dashboard 战情室迭代
- **迭代1**: Canvas 2D自制图表（AI生成）→ 微信小程序兼容性问题，不显示
- **迭代2**: CSS纯柱状图 + 进度条（AI+人工混合）→ 稳定可靠，3种图表类型
- **迭代3**: 用户问"三个大图没有显示" → ECharts-for-weixin集成
- **迭代4**: ECharts still not showing → 诊断：组件需要 `lazyLoad: true` + `this.selectComponent().init(callback)` 模式
- **迭代5**: ECharts始终无法渲染 → 最终方案：回归CSS可视化，100%兼容微信小程序

### 数据可视化美化
- "舆情情感百分比条不好看" → 渐变色+阴影+百分比外置标签+图例优化
- "四指标卡片间隔太大" → box-sizing:border-box + flex布局2×2+统一min-height
- "百分比被裁切" → 从bar内部移到外部彩色文字显示

### UI组件 + 状态管理
- **AI生成**: npm安装命令、app.json全局注册
- **人工修改**: Vant Weapp 8组件集成(van-tag/van-progress/van-loading/van-empty/van-button/van-tabs/van-cell/van-progress)，MobX store设计

### 数据工厂页面
- **新建**: 清洗看板（去重率/异常值/填充率）+ 归因分析（加权评分模型）+ 数据血缘（4阶段链路）
- **AI生成**: 加权评分算法（0.4×内容量+0.25×互动+0.2×舆情+0.15×竞品活跃度）
- **人工修改**: 页面CSS布局、血缘展示的详细步骤文案

### 消息订阅与推送
- **新建**: 异常检测引擎 + 订阅管理 + 推送通知
- **AI生成**: AlertDetector检测逻辑（价格下降/负面舆情/流量激增）
- **人工修改**: 订阅UI交互（即时高亮切换，去掉Toast提示）

### 商品详情页
- **AI生成**: 详情页骨架
- **人工修改**: 
  - 数据来源跳转（真实→复制平台URL，模拟→提示）
  - 近30天价格走势+跨平台价格卡片+同类竞品对比

---

## 部署基础设施 (7/12-7/13)

### Docker + 腾讯云
- **AI生成**: Dockerfile模板、docker-compose.yml服务编排
- **人工修改**: 腾讯云CCR镜像加速、非root安全加固、健康检查脚本、crontab巡检

### GitHub提交
- 4个结构化commit（项目初始化→后端核心→爬虫API→小程序前端）
- 完整.gitignore、README文档

---

## 关键Bug修复记录

| 日期 | 问题 | 根因 | 修复 |
|------|------|------|------|
| 7/10 | WXML编译错误 | .toFixed()和嵌套三元在WXML不可用 | JS预计算所有显示值 |
| 7/11 | 爬取任务全部失败 | 微博返回403反爬 | 增强请求头+优雅降级+回退模拟数据 |
| 7/11 | 后端启动无输出 | python指向Windows Store假Python | 改用E:\anaconda\python.exe |
| 7/12 | 报告显示HTML源码 | parse_markdown_sections误解析HTML | 分离Markdown解析与HTML生成 |
| 7/12 | Canvas图表空白 | Canvas 2D API兼容性差 | 替换为CSS柱状图 |
| 7/13 | ECharts始终不渲染 | ec-canvas组件需要lazyLoad+echarts属性 | 最终回退CSS方案 |
| 7/13 | 舆情条不显示 | 后端字段名positive vs 前端读positive_ratio | 字段名匹配修复 |
| 7/13 | 订阅高亮不生效 | WXML不支持.indexOf() | JS预计算selected布尔值 |
| 7/13 | 百分比文字被裁切 | 父容器overflow:hidden | 数字移到条外部显示 |

---

## AI协作体会（答辩参考）

1. **架构设计阶段**: AI快速生成了完整的三层架构骨架和所有API路由，人工重点调整业务逻辑和行业配置
2. **编码阶段**: AI生成约70%的基础代码（CRUD接口、前端模板、配置脚手架），人工补充约30%的核心逻辑（反爬策略、Prompt工程、错误处理、微信小程序兼容性）
3. **调试阶段**: AI擅长定位语法错误和兼容性问题（WXML表达式限制、Canvas2D兼容性），但业务逻辑bug需要人工精准描述场景
4. **迭代优化**: 每个功能模块平均经历3-5轮AI对话优化，从基础实现→问题识别→修复→美化→性能优化
5. **代码审查**: AI生成的每个文件都经过人工Review，数据安全、异常处理、性能优化是重点审查点

---

**总计AI交互次数**: 约80+轮  
**AI代码占比**: 基础结构~70%，业务逻辑~30%  
**人工修改重点**: 反爬策略、Prompt工程、微信小程序兼容性适配、可视化美化、行业配置
