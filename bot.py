from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
import json
import io

from config import TELEGRAM_TOKEN, WEBHOOK_URL, OPENAI_API_KEY
from database import get_tasks, update_task_status, delete_task, get_stats, clear_chat_history
from claude_agent import chat_with_kolya

try:
    import openai
    openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    openai_client = None

PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
STATUS_EMOJI = {"todo": "📋", "in_progress": "⏳", "done": "✅"}


def get_main_keyboard(webapp_url: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Відкрити Task Manager", web_app=WebAppInfo(url=webapp_url))],
        [
            InlineKeyboardButton("📋 Мої задачі", callback_data="tasks_todo"),
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        ],
        [InlineKeyboardButton("🗑 Очистити чат з Колею", callback_data="clear_chat")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    webapp_url = f"{WEBHOOK_URL}/app?user_id={user.id}"

    text = (
        f"Привіт, {user.first_name}! 👋\n\n"
        f"Я **Коля** — твій персональний AI-асистент.\n\n"
        f"Що я вмію:\n"
        f"• Приймаю задачі текстом — просто напиши що треба зробити\n"
        f"• Плануємо день разом\n"
        f"• Нагадую про дедлайни\n"
        f"• Аналізую твою продуктивність\n\n"
        f"Напиши мені будь-яку задачу або відкрий Task Manager 👇"
    )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard(webapp_url)
    )


async def transcribe_voice(voice_file) -> str:
    if not openai_client:
        raise RuntimeError("OpenAI не налаштований")
    file_bytes = await voice_file.download_as_bytearray()
    audio = io.BytesIO(bytes(file_bytes))
    audio.name = "voice.ogg"
    transcript = await openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=audio,
        language="uk"
    )
    return transcript.text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    result = await chat_with_kolya(user_id, text)

    reply_text = result["text"]

    webapp_url = f"{WEBHOOK_URL}/app?user_id={user_id}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Відкрити Task Manager", web_app=WebAppInfo(url=webapp_url))]
    ])

    await update.message.reply_text(
        reply_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        voice_file = await update.message.voice.get_file()
        text = await transcribe_voice(voice_file)
    except Exception as e:
        await update.message.reply_text("⚠️ Не вдалося розпізнати голос. Спробуй ще раз.")
        return

    await update.message.reply_text(f"🎤 _{text}_", parse_mode=ParseMode.MARKDOWN)

    result = await chat_with_kolya(user_id, text)

    webapp_url = f"{WEBHOOK_URL}/app?user_id={user_id}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Відкрити Task Manager", web_app=WebAppInfo(url=webapp_url))]
    ])

    await update.message.reply_text(
        result["text"],
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()

    webapp_url = f"{WEBHOOK_URL}/app?user_id={user_id}"

    if data == "tasks_todo":
        tasks = await get_tasks(user_id, status="todo")
        if not tasks:
            text = "📭 Немає активних задач!\n\nНапиши мені що треба зробити — створю задачу."
        else:
            text = f"📋 **Активні задачі ({len(tasks)}):**\n\n"
            for t in tasks[:10]:
                emoji = PRIORITY_EMOJI.get(t["priority"], "🟡")
                due = f" — 📅 {t['due_date']}" if t.get("due_date") else ""
                text += f"{emoji} {t['title']}{due}\n"
            if len(tasks) > 10:
                text += f"\n...і ще {len(tasks) - 10} задач"

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard(webapp_url)
        )

    elif data == "stats":
        stats = await get_stats(user_id)
        total = sum(stats.values())
        done = stats.get("done", 0)
        pct = round(done / total * 100) if total > 0 else 0

        bar_filled = int(pct / 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)

        text = (
            f"📊 **Твоя продуктивність**\n\n"
            f"✅ Виконано: {done}\n"
            f"⏳ В роботі: {stats.get('in_progress', 0)}\n"
            f"📋 Заплановано: {stats.get('todo', 0)}\n"
            f"📦 Всього: {total}\n\n"
            f"[{bar}] {pct}%"
        )

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard(webapp_url)
        )

    elif data == "clear_chat":
        await clear_chat_history(user_id)
        await query.edit_message_text(
            "🗑 Контекст розмови очищено. Починаємо з чистого аркуша!",
            reply_markup=get_main_keyboard(webapp_url)
        )


def build_application():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    return app
