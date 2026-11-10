
import asyncio
import logging
import os
import re
import html

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

# CONFIGURATION
API_TOKEN = os.getenv("9200521446:AAG9QuYBf8vrh1VhHsLM3MfXWcSI5x0c98Q")
ADMIN_ID = 8825308934

logging.basicConfig(level=logging.INFO)

if not API_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=MemoryStorage())


# FEEDBACK STATE
class FeedbackState(StatesGroup):
    waiting_for_feedback = State()


# 1. START COMMAND
@dp.message(CommandStart())
async def send_welcome(
    message: types.Message,
    state: FSMContext
):
    await state.set_state(
        FeedbackState.waiting_for_feedback
    )

    welcome_text = (
        "✨ ሰላም! እንኳን ደህና መጡ!\n\n"
        "💬 ያሎትን ማንኛውንም አስተያየት፣ "
        "ጥያቄ ወይም ሐሳብ ከዚህ በታች ይጻፉልን።\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "✨ Hello! Welcome!\n"
        "💬 Please write any feedback, questions "
        "or suggestions below.\n\n"
        "🙏 Thank you!"
    )

    await message.answer(welcome_text)


# 2. CANCEL COMMAND
@dp.message(Command("cancel"))
async def cancel_feedback(
    message: types.Message,
    state: FSMContext
):
    await state.clear()

    await message.answer(
        "❌ የFeedback መላክ ተቋርጧል።\n"
        "To start again, send /start"
    )


# 3. RECEIVE USER FEEDBACK
@dp.message(
    FeedbackState.waiting_for_feedback,
    F.chat.id != ADMIN_ID,
    F.text
)
async def receive_feedback(
    message: types.Message,
    state: FSMContext
):
    user = message.from_user

    if not user:
        return

    feedback_text = html.escape(message.text)

    name = html.escape(user.full_name)
    username = (
        f"@{html.escape(user.username)}"
        if user.username else "N/A"
    )

    admin_message = (
        "📩 <b>NEW FEEDBACK RECEIVED!</b>\n"
        "📩 አዲስ አስተያየት መጥቷል!\n\n"
        f"👤 <b>Name:</b> {name}\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n\n"
        "💬 <b>Message:</b>\n"
        f"{feedback_text}\n\n"
        "━━━━━━━━━━━━━━\n"
        "⚡️ Reply to this message to answer the user."
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message
        )

        await message.answer(
            "🙏 እናመሰግናለን!\n"
            "አስተያየትዎ ደርሶናል። "
            "በቅርብ እንመለስልዎታለን። ✨\n\n"
            "💙 Thank you! Your feedback has been received."
        )

        await state.clear()

    except TelegramAPIError:
        logging.exception("Failed to send feedback to admin")

        await message.answer(
            "⚠️ መልዕክቱን መላክ አልተቻለም። "
            "እባክዎ እንደገና ይሞክሩ።"
        )


# 4. NON-TEXT MESSAGE HANDLER
@dp.message(
    FeedbackState.waiting_for_feedback,
    F.chat.id != ADMIN_ID
)
async def non_text_feedback(message: types.Message):
    await message.answer(
        "⚠️ እባክዎ Feedback በጽሑፍ ብቻ ይላኩ።\n"
        "Please send your feedback as text."
    )


# 5. ADMIN REPLY HANDLER
@dp.message(
    F.chat.id == ADMIN_ID,
    F.reply_to_message
)
async def reply_to_user(message: types.Message):

    original = message.reply_to_message

    if not original or not original.text:
        await message.answer(
            "⚠️ Original feedback message not found."
        )
        return

    match = re.search(
        r"User ID:</b>\s*<code>(\d+)</code>",
        original.text
    )

    if not match:
        await message.answer(
            "⚠️ የተጠቃሚው ID አልተገኘም።"
        )
        return

    target_user_id = int(match.group(1))

    reply_text = message.text or message.caption

    if not reply_text:
        await message.answer(
            "⚠️ Please send a text reply."
        )
        return

    safe_reply = html.escape(reply_text)

    user_reply = (
        "📬 <b>Message from Wesib Admin</b>\n\n"
        f"{safe_reply}\n\n"
        "💙 <b>Wesib Team</b>"
    )

    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=user_reply
        )

        await message.answer(
            "✅ መልዕክቱ ለተጠቃሚው ተልኳል!"
        )

    except TelegramAPIError as e:
        logging.exception("Admin reply failed")

        await message.answer(
            f"⚠️ መልዕክቱ አልተላከም።\n{e}"
        )


# 6. ADMIN MESSAGE WITHOUT REPLY
@dp.message(F.chat.id == ADMIN_ID)
async def admin_no_reply(message: types.Message):
    await message.answer(
        "⚠️ ለተጠቃሚው መልስ ለመስጠት "
        "የFeedback መልዕክቱን Reply ያድርጉ።"
    )


# 7. START BOT
async def main():
    logging.info("Wesib Feedback Bot is starting...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
