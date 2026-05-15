from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes
import io
import httpx
import re

from config import TELEGRAM_TOKEN, OPENAI_API_KEY
from database import save_message, clear_chat_history, register_contact, get_contacts, get_contact_by_name
from claude_agent import chat_with_kolya

ADMIN_ID = 564938961  # Андрій П'яних

WAITING_NAME = 1


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
    user_id = user.id

    if user_id == ADMIN_ID:
        await update.message.reply_text(
            f"Привіт, Андрію! 👋\n\n"
            f"Я Коля — твій персональний AI-асистент.\n\n"
            f"Просто пиши або надсилай голосові повідомлення.\n\n"
            f"Корисні команди:\n"
            f"/contacts — список контактів\n"
            f"/clear — очистити чат"
        )
    else:
        await update.message.reply_text(
            f"Привіт! 👋 Я Коля — асистент Андрія П'яних (DriveMe).\n\n"
            f"Як тебе звати? Напиши своє ім'я щоб я тебе запам'ятав."
        )
        return WAITING_NAME


async def save_contact_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = update.message.text.strip()

    await register_contact(user.id, name)

    await update.message.reply_text(
        f"✅ Дякую, {name}! Тепер Андрій може надіслати тобі повідомлення через мене."
    )
    return ConversationHandler.END


async def contacts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    contacts = await get_contacts()
    if not contacts:
        await update.message.reply_text("📭 Поки немає контактів. Попроси людей написати /start боту.")
        return

    text = "📋 Контакти:\n\n"
    for c in contacts:
        text += f"• {c['name']} (ID: {c['user_id']})\n"
    text += f"\nЩоб написати — просто скажи мені:\n«Напиши Роману: текст повідомлення»"
    await update.message.reply_text(text)


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await clear_chat_history(user_id)
    await update.message.reply_text("🗑 Чат очищено.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Перевіряємо чи це команда "напиши [ім'я]: [текст]"
    if user_id == ADMIN_ID:
        match = re.match(r'^напиши\s+(.+?):\s*(.+)$', text, re.IGNORECASE | re.DOTALL)
        if match:
            contact_name = match.group(1).strip()
            message_text = match.group(2).strip()

            contact = await get_contact_by_name(contact_name)
            if not contact:
                await update.message.reply_text(f"❌ Контакт «{contact_name}» не знайдено.\nПеревір /contacts")
                return

            try:
                await context.bot.send_message(
                    chat_id=contact["user_id"],
                    text=f"📩 Повідомлення від Андрія П'яних:\n\n{message_text}"
                )
                await update.message.reply_text(f"✅ Відправлено {contact['name']}!")
            except Exception as e:
                await update.message.reply_text(f"❌ Помилка відправки: {str(e)[:200]}")
            return

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

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_contact_name)]},
        fallbacks=[],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("contacts", contacts_cmd))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    return app
