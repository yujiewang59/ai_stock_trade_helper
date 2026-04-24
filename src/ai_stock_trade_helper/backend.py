# backend.py
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

from ai_stock_trade_helper.flow import StockAnalysisFlow
from ai_stock_trade_helper.models import StockAnalysisState, UserStockHold

app = FastAPI()
tasks_db = {}  # 存储任务状态

class TaskRequest(BaseModel):
    industry: str
    industry_label: str
    user_assets: float
    user_stock_holds: list[UserStockHold]
    risk_level: str


# 定义 CrewAI 执行逻辑
async def run_crew_task(task_id: str, request: TaskRequest):
    try:
        flow = StockAnalysisFlow()
        flow.state.industry = request.industry
        flow.state.industry_label = request.industry_label
        flow.state.user_assets = request.user_assets
        flow.state.user_stock_holds = request.user_stock_holds
        flow.state.risk_level = request.risk_level

        result = await flow.akickoff()
        
        tasks_db[task_id]["status"] = "completed"
        tasks_db[task_id]["result"] = result
    except Exception as e:
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["error"] = str(e)

# 请求异步任务API
@app.post("/analysis/start")
async def run_crew(request: TaskRequest):
    task_id = f"stock_analysis_task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    tasks_db[task_id] = {"status": "pending", "result": None}
    # 创建后台任务，立即返回 task_id
    asyncio.create_task(run_crew_task(task_id, request))
    return {"task_id": task_id, "status": "started"}


# 获取任务状态API
@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id]