# backend.py
import json

from fastapi import FastAPI

from ai_stock_trade_helper.models import TaskRequest
from celery_backend import analysis_task


app = FastAPI()
tasks_db = {}  # 存储任务状态


# 请求异步任务API
@app.post("/analysis/start")
async def run_crew(request: TaskRequest):
    args = {
        "industry": request.industry,
        "industry_label": request.industry_label,
        "user_assets": request.user_assets,
        "user_stock_holds": request.user_stock_holds,
        "risk_level": request.risk_level
    }
    task = analysis_task.delay(args)  # 调用 Celery 异步任务
    return {"task_id": task.id, "status": "started"}


# 获取任务状态API
@app.get("/status/{task_id}")
def get_status(task_id: str):
    from celery_backend import app
    res = app.AsyncResult(task_id)

    # 任务状态：PENDING（等待）/ SUCCESS（成功）/ FAILURE（失败）
    if res.state == "SUCCESS":
        # result: str = res.result.removeprefix("a coroutine was expected, got")
        # result = json.loads(result.strip())  # 验证是否为合法JSON格式
        # 成功：安全返回结果
        return {
            "task_id": task_id,
            "state": res.state,
            "status": "completed",
            "result": res.result
        }
    elif res.state == "FAILURE":
        # 失败：返回异常信息（关键！排查错误）
        return {
            "task_id": task_id,
            "state": res.state,
            "status": "failed",
            "error": str(res.result),  # 这里会显示 EncodeError 详情
            "msg": "任务执行失败"
        }
    else:
        # 等待中
        return {
            "task_id": task_id,
            "state": res.state,
            "status": "pending"
        }