# AI 协作日志
# ================================================================
# 记录使用 Claude Code / OpenCode 辅助开发的关键交互
# 项目: 金宫味业数字营销数据中台
# 开发周期: 2026年7月6日 - 7月13日
# ================================================================

## 项目启动 (7/6)

### 架构设计
- **用户提问**: "帮我设计一个方案完成这个项目" (上传了实操题文档)
- **AI输出**: 完整的三层架构方案 (数据采集层→处理层→展示层)
- **人工修改**: 补充了调味品行业特定的品牌和关键词配置

## 后端开发 (7/7 - 7/9)

### FastAPI 项目搭建
- **AI生成**: main.py骨架、所有API路由模板、数据库初始化
- **人工修改**: lifespan生命周期逻辑、CORS配置、MySQL切换方案

### 爬虫模块
- **AI生成**: 微博/百度热搜爬虫基础结构 (httpx异步请求)
- **人工修改**: 反爬策略 (12个请求头模拟、403降级、浏览器指纹)、数据清洗Pipeline
- **关键对话**: "你需要处理反爬策略" → AI增加了User-Agent伪装和备用方案

### Scrapy Pipeline 架构
- **AI生成**: Item数据类、Spider基类、Pipeline基类
- **人工修改**: DeduplicationPipeline的hash算法、CleaningPipeline的价格校验逻辑
- **调试过程**: "Pipeline的dedup逻辑有bug" → AI修复了hash碰撞问题

### Playwright 无头浏览器
- **AI生成**: async_playwright启动框架
- **人工修改**: add_init_script隐藏WebDriver特征、截图保存路径

### AI 服务集成
- **AI生成**: DeepSeek API调用模板
- **人工修改**: Prompt工程 (调味品行业术语、Markdown→HTML转换)、无API Key降级方案
- **关键对话**: "生成的日报文字会露出<>这些代码" → AI修复了parse_markdown_sections的HTML标签bug

## 前端开发 (7/10 - 7/12)

### 微信小程序搭建
- **AI生成**: app.json配置、页面路由、基础WXML模板
- **人工修改**: 金宫红配色方案(#C8102E)、TabBar图标文案

### Dashboard 战情室
- **迭代1**: Canvas 2D 自制图表 (AI生成) → 微信小程序兼容性问题
- **迭代2**: CSS 纯柱状图 + 进度条 (AI+人工混合) → 稳定可靠
- **迭代3**: ECharts-for-weixin 折线/饼图/柱状图 (AI配置渐变、人工确认配色)
- **关键对话**: "为什么我的战情室的页面显示的东西很少" → AI诊断Canvas兼容性 → 重写为CSS方案

### Vant Weapp 集成
- **AI生成**: npm安装命令、app.json全局组件注册
- **人工修改**: van-tag/van-progress/van-loading 的样式适配

### MobX 状态管理
- **AI生成**: observable store结构
- **人工修改**: 计算属性(总GMV、增长率)、action方法命名规范

## 部署基础设施 (7/12-7/13)

### Docker 容器化
- **AI生成**: Dockerfile基础模板、docker-compose.yml服务编排
- **人工修改**: 腾讯云镜像加速(CCR)、非root用户安全加固、健康检查脚本

### Nginx 反向代理
- **AI生成**: 基础反向代理配置
- **人工修改**: 速率限制(30r/m)、安全头(X-Frame/XSS)、SSL模板

## 关键Bug修复记录

| 日期 | 问题 | 根因 | 修复 |
|------|------|------|------|
| 7/10 | WXML编译错误 | .toFixed()和嵌套三元在WXML不可用 | JS预计算所有显示值 |
| 7/11 | 爬取任务全部失败 | 微博返回403反爬 | 增强请求头+优雅降级+回退模拟数据 |
| 7/12 | 报告显示HTML源码 | parse_markdown_sections误解析HTML | 分离Markdown解析与HTML生成 |
| 7/12 | 后端启动无输出 | python命令指向Windows Store假Python | 改用E:\anaconda\python.exe |
| 7/13 | Canvas图表空白 | Canvas 2D API在小程序兼容性差 | 替换为ECharts-for-weixin |

## AI协作体会 (3分钟答辩要点)

1. **架构设计阶段**: AI快速生成了三层架构骨架和API路由，人工重点调整业务逻辑和行业配置
2. **编码阶段**: AI生成约70%的基础代码(CRUD接口、前端模板、配置脚手架)，人工补充约30%的核心逻辑(反爬策略、Prompt工程、错误处理)
3. **调试阶段**: AI擅长定位语法错误和兼容性问题，但业务逻辑bug需要人工描述清楚场景
4. **代码审查**: 每个AI生成的文件都经过人工Review，数据安全、异常处理、性能优化是重点审查点
