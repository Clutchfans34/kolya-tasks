import json
import anthropic
from database import get_tasks, create_task, get_stats, get_chat_history, save_message
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ти — Коля, персональний AI-асистент Андрія П'яних, CEO компанії DriveMe (національний автопарк, 348 авто, 7 філій по Україні).

Твоя роль: Chief of Staff + персональний асистент.

Твій характер:
- Чіткий, структурований, проактивний
- Говориш українською, коротко і по суті
- Знаєш контекст бізнесу DriveMe
- Допомагаєш управляти часом і задачами CEO

Твої можливості в таск менеджері:
1. **Створення задач** — коли користувач описує задачу, ти розумієш і підтверджуєш
2. **Планування дня/тижня** — аналізуєш задачі і пропонуєш порядок
3. **Аналіз продуктивності** — даєш insights по виконаним задачам
4. **Пріоритизація** — допомагаєш обрати що робити першим

Пріоритети задач:
- high (🔴) — термінове і важливе
- medium (🟡) — важливе, не термінове
- low (🟢) — можна пізніше

Коли користувач описує задачу голосом або текстом:
- Розпізнай заголовок (коротко)
- Визнач пріоритет
- Запитай дедлайн якщо не вказано і задача важлива
- Поверни JSON якщо треба створити задачу:
  {"action": "create_task", "title": "...", "priority": "high/medium/low", "due_date": "YYYY-MM-DD або null"}

Коли питають про задачі або план дня — відповідай текстом, структуровано.

Якщо питання не про задачі — відповідай як Chief of Staff Андрія, з фокусом на DriveMe."""

TOOLS = [
    {
        "name": "create_task",
        "description": "Створити нову задачу для користувача",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Назва задачі (коротко)"},
                "description": {"type": "string", "description": "Деталі задачі (опційно)"},
                "priority": {"type": "string", "enum": ["high", "medium", "low"], "description": "Пріоритет"},
                "due_date": {"type": "string", "description": "Дедлайн у форматі YYYY-MM-DD або null"}
            },
            "required": ["title", "priority"]
        }
    },
    {
        "name": "get_tasks_list",
        "description": "Отримати список задач користувача",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["todo", "in_progress", "done", "all"], "description": "Статус задач"}
            }
        }
    },
    {
        "name": "get_productivity_stats",
        "description": "Отримати статистику продуктивності",
        "input_schema": {"type": "object", "properties": {}}
    }
]


async def chat_with_kolya(user_id: int, user_message: str) -> dict:
    """
    Returns: {"text": "...", "task_created": {...} or None}
    """
    history = await get_chat_history(user_id, limit=10)
    await save_message(user_id, "user", user_message)

    messages = history + [{"role": "user", "content": user_message}]

    tasks = await get_tasks(user_id)
    tasks_context = ""
    if tasks:
        active = [t for t in tasks if t["status"] != "done"]
        tasks_context = f"\n\n[Поточні задачі користувача: {len(active)} активних з {len(tasks)} всього]"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT + tasks_context,
        tools=TOOLS,
        messages=messages
    )

    result_text = ""
    task_created = None

    for block in response.content:
        if block.type == "text":
            result_text = block.text
        elif block.type == "tool_use":
            if block.name == "create_task":
                inp = block.input
                task_id = await create_task(
                    user_id=user_id,
                    title=inp["title"],
                    description=inp.get("description", ""),
                    priority=inp.get("priority", "medium"),
                    due_date=inp.get("due_date")
                )
                task_created = {
                    "id": task_id,
                    "title": inp["title"],
                    "priority": inp.get("priority", "medium"),
                    "due_date": inp.get("due_date")
                }
                if not result_text:
                    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(inp.get("priority", "medium"), "🟡")
                    result_text = f"✅ Задачу створено!\n\n{priority_emoji} **{inp['title']}**"
                    if inp.get("due_date"):
                        result_text += f"\n📅 Дедлайн: {inp['due_date']}"

            elif block.name == "get_tasks_list":
                status_filter = block.input.get("status", "all")
                if status_filter == "all":
                    fetched = await get_tasks(user_id)
                else:
                    fetched = await get_tasks(user_id, status=status_filter)

                follow_up = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=messages + [
                        {"role": "assistant", "content": response.content},
                        {"role": "user", "content": f"Ось задачі: {json.dumps(fetched, ensure_ascii=False)}"}
                    ]
                )
                for b in follow_up.content:
                    if b.type == "text":
                        result_text = b.text

            elif block.name == "get_productivity_stats":
                stats = await get_stats(user_id)
                total = sum(stats.values())
                done = stats.get("done", 0)
                result_text = f"📊 **Статистика продуктивності**\n\n"
                result_text += f"✅ Виконано: {done}\n"
                result_text += f"⏳ В роботі: {stats.get('in_progress', 0)}\n"
                result_text += f"📋 Заплановано: {stats.get('todo', 0)}\n"
                result_text += f"📦 Всього: {total}\n"
                if total > 0:
                    pct = round(done / total * 100)
                    result_text += f"\n🎯 Прогрес: {pct}%"

    if not result_text:
        result_text = "Зрозумів! Чим можу допомогти далі?"

    await save_message(user_id, "assistant", result_text)

    return {"text": result_text, "task_created": task_created}
