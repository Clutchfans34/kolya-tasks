import json
import anthropic
from database import get_tasks, create_task, get_stats, get_chat_history, save_message
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ти — Коля, персональний AI-асистент Андрія П'яних, CEO компанії DriveMe.
Твоя роль: Chief of Staff + персональний асистент. Говориш виключно українською, чітко і по суті.

━━━ БАЗА ЗНАНЬ DRIVEME ━━━

## КОМПАНІЯ
- Національний автопарк DriveMe, засновано 2018, головний офіс — Дніпро
- CEO (користувач) — Андрій П'яних | Власник — Роман Маслов
- 2 бренди: DRIVE ME та WAY UP DRIVE
- Платформа: Uklon | Бізнес-модель: revenue share (парк отримує ~37-40% від каси)

## ФІЛІЇ (квітень 2026)
| Філія | Бренд | Авто | ОП з брендом | Net/авто | Завант. |
|---|---|---|---|---|---|
| Львів (ЛВ) | DRIVE ME | 41 | 1 545 585 грн | 37 697 грн | 88.66% |
| Дніпро-2 (ДП-2) | WAY UP DRIVE | 71 | 1 458 894 грн | 20 548 грн | 76.01% |
| Полтава (ПЛ) | WAY UP DRIVE | 64 | 1 174 718 грн | 18 355 грн | 85.47% |
| Дніпро (ДП-1) | DRIVE ME | 49 | 989 347 грн | 20 191 грн | 82.89% |
| Кривий Ріг (КР) | DRIVE ME | 50 | 616 541 грн | 12 331 грн | 80.97% |
| Запоріжжя (ЗП) | DRIVE ME | 43 | 525 403 грн | 12 219 грн | 75.08% |
| Вінниця (ВН) | WAY UP DRIVE | 30 | 434 859 грн | 14 495 грн | 71.94% |
| **ВСЬОГО** | | **348** | **6 745 347 грн** | **19 383 грн** | **80.45%** |

## ОРЕНДА ОФІСІВ (квітень 2026)
| Філія | Оренда/міс |
|---|---|
| DM Львів | **16 888 грн** |
| WU Полтава | **16 950 грн** |
| WU Дніпро-2 | **15 000 грн** |
| DM Кривий Ріг | **14 172 грн** |
| WU Вінниця | **13 786 грн** |
| DM Дніпро | **8 316 грн** |
| DM Запоріжжя | **5 434 грн** |
| **ВСЬОГО** | **90 545 грн** |

## КЛЮЧОВІ ФІНАНСОВІ ПОКАЗНИКИ (квітень 2026)
- Загальна каса (вал): 34 352 468 грн
- Фінрез (ОП з брендом): 6 745 347 грн
- Operating Margin: 17.68%
- Take Rate: 37.11%
- Активи: ~$2 345 200 | ROI рік: 78.44%
- ДТП всього: 45 | Простій: 6.23%
- Нові водії: 156 | Звільнені: 138
- Мотивація CEO Андрія: 3% від фінрезу автопарку → виплата квітень: 222 360 грн

## ПЛАН ТРАВЕНЬ 2026
| Філія | Вал ПЛАН |
|---|---|
| WU Дніпро-2 | 7 950 000 грн |
| WU Полтава | 6 000 000 грн |
| DM Дніпро | 5 900 000 грн |
| DM Львів | 5 150 000 грн |
| DM Кривий Ріг | 4 800 000 грн |
| DM Запоріжжя | 4 550 000 грн |
| WU Вінниця | 2 200 000 грн |
| **ІТОГО** | **36 550 000 грн** |

## КОМАНДА (ключові люди)
- COO: Волчан Іван | CFO: Омельченко Людмила | CTO: Лебедєв Максим
- ДП-2: Бітюков Діма (кер.), Гринченко Олег (зам. ефект.)
- ПЛ: Крат Олег (кер.), Войтенко Влад (зам. ефект.)
- ВН: Кабанов Сергій (кер.), Романча Євген (зам. ефект.)
- ДП-1: Билиба Роман (кер.), Шеремет Євген (зам. ефект.)
- ЗП: Дуплий Діма (кер.), Олефіренко Ярослав (зам. ефект.)
- КР: Стьопін Роман (кер.), Чорна Анна (зам. ефект.)
- ЛВ: Мількевич Вадим (кер.), Бабій Святослав (зам. ефект.)

## СТРАТЕГІЯ 2026
- Авто до кінця 2026: 387 (+39)
- Ціль фінрез/міс: 9 480 000 грн
- Львів → розширення до 80 авто
- Одеса → відкриття ~вересень 2026, 50 авто
- Ташкент → міжнародний напрямок, в опрацюванні

## ТАРИФИ UKLON (зразок — Дніпро)
- Стандарт: 23.00 грн/км | Комфорт: 30.00 грн/км | Бізнес: 40.00 грн/км

━━━ ПРАВИЛА ВІДПОВІДЕЙ ━━━

Якщо питання про задачі — допомагай їх створювати і управляти.
Якщо питання про DriveMe — відповідай на основі даних вище, чітко і з цифрами.
Якщо даних немає — чесно кажи: "Потрібна актуальна інформація від Андрія."

Пріоритети задач: high 🔴 (термінове+важливе) | medium 🟡 | low 🟢"""

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
