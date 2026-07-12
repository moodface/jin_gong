# ================================================================
# 金宫味业数字营销数据中台 - FastAPI 入口
# AI生成: FastAPI 应用骨架、CORS中间件、路由注册
# 人工修改: lifespan生命周期配置、数据初始化策略、启动命令
# ================================================================

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.services.mock_data import init_mock_data
from app.api.dashboard import router as dashboard_router
from app.api.report import router as report_router
from app.api.monitor import router as monitor_router
from app.api.cleaning import router as cleaning_router
from app.api.data_factory import router as data_factory_router
from app.api.notification import router as notification_router


async def scheduled_scrape_and_detect():
    """每小时自动执行：数据爬取 + 异常检测"""
    while True:
        await asyncio.sleep(3600)
        print("[Scheduler] ========== 定时任务开始 ==========")
        try:
            from app.scraper.real_scraper import run_real_scrape
            result = await run_real_scrape()
            print(f"[Scheduler] 爬取完成: {result.get('total_saved', 0)} 条")
        except Exception as e:
            print(f"[Scheduler] 爬取失败: {e}")

        await asyncio.sleep(5)

        try:
            from app.services.alert_service import AlertDetector
            detector = AlertDetector()
            alerts = detector.run_all_checks()
            print(f"[Scheduler] 检测完成: {len(alerts)} 条预警")
        except Exception as e:
            print(f"[Scheduler] 检测失败: {e}")

        print(f"[Scheduler] ========== 定时任务结束 ==========")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_mock_data()
    task = asyncio.create_task(scheduled_scrape_and_detect())
    yield
    task.cancel()

# AI生成: FastAPI 应用实例化
# 人工修改: 应用标题、描述文案调整为金宫味业业务场景
app = FastAPI(
    title="金宫味业数字营销数据中台",
    description="全域数据采集、智能营销、可视化决策闭环",
    version="1.0.0",
    lifespan=lifespan,
)

# AI生成: CORS 中间件配置
# 人工修改: allow_origins 改为 ["*"] 以支持开发调试，生产环境需限定域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI生成: 路由自动注册
app.include_router(dashboard_router)
app.include_router(report_router)
app.include_router(monitor_router)
app.include_router(cleaning_router)
app.include_router(data_factory_router)
app.include_router(notification_router)


@app.get("/")
def root():
    return {"message": "金宫味业数字营销数据中台 API", "version": "1.0.0"}


# AI+人工: __main__ 启动块 (AI生成uvicorn调用，人工配置host/port)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
