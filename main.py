import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from config import TELEGRAM_TOKEN, WEBHOOK_URL, PORT
from database import init_db, get_tasks, create_task, update_task_status, delete_task, get_stats
from claude_agent import chat_with_kolya
from bot import build_application

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

telegram_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app
    await init_db()
    logger.info("DB initialized")

    telegram_app = build_application()
    await telegram_app.initialize()
    await telegram_app.start()

    if WEBHOOK_URL:
        webhook_endpoint = f"{WEBHOOK_URL}/webhook"
        await telegram_app.bot.set_webhook(webhook_endpoint)
        logger.info(f"Webhook set: {webhook_endpoint}")
    else:
        logger.warning("WEBHOOK_URL not set — bot won't receive updates until deployed")

    yield

    await telegram_app.stop()
    await telegram_app.shutdown()


app = FastAPI(title="Koля Task Manager", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/app", response_class=HTMLResponse)
async def mini_app(user_id: int = 0):
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/webhook")
async def telegram_webhook(request: Request):
    global telegram_app
    if not telegram_app:
        raise HTTPException(status_code=503, detail="Bot not ready")
    data = await request.json()
    from telegram import Update
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


class ChatRequest(BaseModel):
    user_id: int
    message: str


class TaskCreate(BaseModel):
    user_id: int
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: str = None


class TaskStatusUpdate(BaseModel):
    user_id: int
    status: str


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    result = await chat_with_kolya(req.user_id, req.message)
    return result


@app.get("/api/tasks")
async def api_get_tasks(user_id: int, status: str = None):
    tasks = await get_tasks(user_id, status if status != "all" else None)
    return {"tasks": tasks}


@app.post("/api/tasks")
async def api_create_task(req: TaskCreate):
    task_id = await create_task(
        user_id=req.user_id,
        title=req.title,
        description=req.description,
        priority=req.priority,
        due_date=req.due_date
    )
    return {"id": task_id, "title": req.title}


@app.patch("/api/tasks/{task_id}")
async def api_update_task(task_id: int, req: TaskStatusUpdate):
    await update_task_status(task_id, req.user_id, req.status)
    return {"ok": True}


@app.delete("/api/tasks/{task_id}")
async def api_delete_task(task_id: int, user_id: int):
    await delete_task(task_id, user_id)
    return {"ok": True}


@app.get("/api/stats")
async def api_stats(user_id: int):
    stats = await get_stats(user_id)
    return stats


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
