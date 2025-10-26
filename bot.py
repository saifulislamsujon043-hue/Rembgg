import os
import datetime
from io import BytesIO
from rembg import remove
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
)

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

GROUP_ID = -1003190051264
CHANNELS = [
    "@Noob_tube_ff_tg_Channel",
    "@grow_up_with_10x",
    "@grow_up_with_10x_Group"
]
DAILY_LIMIT = 40

# In-memory user data (you can use database in production)
user_usage = {}
users_set = set()

# === FUNCTIONS ===

async def check_channels(update: Update, context: CallbackContext) -> bool:
    user_id = update.effective_user.id
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                raise Exception("Not joined")
        except:
            buttons = [[InlineKeyboardButton("🔗 Join Channel 1", url="https://t.me/Noob_tube_ff_tg_Channel")],
                       [InlineKeyboardButton("🔗 Join Channel 2", url="https://t.me/grow_up_with_10x")],
                       [InlineKeyboardButton("💬 Join Group", url="https://t.me/grow_up_with_10x_Group")]]
            await update.message.reply_text(
                "❗ Please join all channels to use this bot.",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return False
    return True


async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    users_set.add(user.id)

    keyboard = [
        [InlineKeyboardButton("➕ Add me to your group", url="http://t.me/IMAGE_BG_REMOVER_by_10x_BOT?startgroup=start")],
        [InlineKeyboardButton("👑 Owner", url="https://t.me/NoobTube_FF")]
    ]
    await update.message.reply_text(
        f"👋 Hi {user.first_name}!\n\nSend me any photo, and I'll remove its background instantly!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_image(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name

    if not await check_channels(update, context):
        return

    # Reset daily usage
    today = datetime.date.today()
    usage = user_usage.get(user_id, {"count": 0, "date": today})
    if usage["date"] != today:
        usage = {"count": 0, "date": today}

    if usage["count"] >= DAILY_LIMIT:
        await update.message.reply_text("⚠️ You’ve reached your daily limit of 40 images. Try again tomorrow.")
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    img_data = await file.download_as_bytearray()

    await update.message.reply_text("🪄 Removing background... please wait...")

    result = remove(img_data)

    output_image = BytesIO(result)
    output_image.name = "output.png"

    await update.message.reply_photo(photo=InputFile(output_image), caption="✅ Background removed!")

    # Send logs to your group
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"📸 Image processed by @{username}"
    )
    output_image.seek(0)
    await context.bot.send_photo(chat_id=GROUP_ID, photo=InputFile(output_image))

    usage["count"] += 1
    user_usage[user_id] = usage


async def statistics(update: Update, context: CallbackContext):
    total_users = len(users_set)
    await update.message.reply_text(f"📊 Total users: {total_users}")


# === MAIN ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("statistics", statistics))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    print("✅ Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
