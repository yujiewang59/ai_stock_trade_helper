from celery import Celery
from ai_stock_trade_helper.flow import StockAnalysisFlow
from dotenv import load_dotenv
import os

from ai_stock_trade_helper.models import TaskRequest

load_dotenv()
broker = os.getenv("REDIS_URL")
backend = os.getenv("REDIS_URL")

# 1. 初始化Celery
app = Celery(
    "ai_stock_tasks",
    broker=broker,      # 消息队列
    backend=backend     # 结果存储
)

# 2. 全局配置
app.conf.update(
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_default_retry_delay=10,
    task_max_retries=3
)

# ====================== 业务任务 ======================
# 任务: 接收分析请求，执行CrewAI流程，返回结果
@app.task(name="analysis_task")
def analysis_task(request: dict):
    try:
        data = TaskRequest(
            industry=request["industry"],
            industry_label=request["industry_label"],
            user_assets=request["user_assets"],
            user_stock_holds=request["user_stock_holds"],
            risk_level=request["risk_level"]
        )

        """异步分析任务"""
        flow = StockAnalysisFlow()
        flow.state.industry = data.industry
        flow.state.industry_label = data.industry_label
        flow.state.user_assets = data.user_assets
        flow.state.user_stock_holds = data.user_stock_holds
        flow.state.risk_level = data.risk_level

        result = flow.kickoff()  # 运行流程，获取结果
        return result
    except Exception as e:
        return str(e)
