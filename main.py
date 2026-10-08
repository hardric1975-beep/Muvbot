
import os
import logging
import asyncio
import fal_client
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
FAL_KEY = os.getenv("FAL_KEY")

# Set fal key
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Muvbot is LIVE!\n\n"
        "Send me a PHOTO with caption like:\n"
        "'make her smile and wave'\n\n"
        "Or send YouTube link / song name for music!\n\n"
        "/start - Start\n/help - Help"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "How to use:\n"
        "1. Send a photo + write what you want: 'smile, wave, blink'\n"
        "2. Wait 30-60 seconds, I will send video back!\n\n"
        "Need FAL_KEY in Railway Variables!"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FAL_KEY:
        await update.message.reply_text("❌ FAL_KEY missing! Add it in Railway > Variables")
        return

    caption = update.message.caption or "make person smile and wave naturally, subtle motion"
    await update.message.reply_text(f"🎬 Making video: {caption}\nPlease wait 30-60 sec...")

    try:
        # Get photo file
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download to /tmp
        file_path = f"/tmp/{photo.file_id}.jpg"
        await file.download_to_drive(file_path)

        # Upload to fal storage
        image_url = await fal_client.upload_file_async(file_path)

        # Generate video with Kling
        result = await fal_client.subscribe_async(
            "fal-ai/kling-video/v2.1/standard/image-to-video",
            arguments={
                "image_url": image_url,
                "prompt": caption,
                "duration": "5",
                "aspect_ratio": "9:16"
            },
        )

        video_url = result.get("video", {}).get("url")
        if not video_url:
            # try other format
            video_url = result.get("video_url") or str(result)

        await update.message.reply_video(video=video_url, caption=f"✅ Done! Prompt: {caption}")

    except Exception as e:
        logger.error(f"Video error: {e}")
        await update.message.reply_text(f"❌ Video failed: {str(e)}\nCheck FAL_KEY and try again.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(
        f"Got it: {text}\n\n"
        f"For video: Send a PHOTO with caption like 'make her smile and wave'\n"
        f"For music: Send YouTube link"
    )

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN missing!")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
