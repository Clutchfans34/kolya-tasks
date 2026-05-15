from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import io
import httpx

from config import TELEGRAM_TOKEN, OPENAI_API_KEY
from database import save_message, clear_chat_history
from claude_agent import chat_with_kolya


async def transcribe_voice(voice_file) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY не встановлений")
    file_bytes = await voice_file.download_as_bytearray()
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            files={"file": ("voice.ogg", bytes(file_bytes), "audio/ogg")},
            data={"model": "whisper-1", "language": "uk"},
        )
        response.raise_for_status()
        return response.json()["text"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привіт, {user.first_name}! 👋\n\n"
        f"Я Коля — твій персональний AI-асистент.\n\n"
        f"Просто пиши або надсилай голосові — відповім на будь-яке питання про DriveMe, команду, цифри, рішення ради або допоможу з будь-чим іншим."
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await clear_chat_history(user_id)
    await update.message.reply_text("🗑 Чат очищено. Починаємо з чистого аркуша!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    reply = await chat_with_kolya(user_id, text)

    try:
        await update.message.reply_text(reply)
    except Exception:
        await update.message.reply_text(reply[:4000])


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        voice_file = await update.message.voice.get_file()
        text = await transcribe_voice(voice_file)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Помилка розпізнавання: {str(e)[:200]}")
        return

    await update.message.reply_text(f"🎤 {text}")

    reply = await chat_with_kolya(user_id, text)

    try:
        await update.message.reply_text(reply)
    except Exception:
        await update.message.reply_text(reply[:4000])


def build_application():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    return app
