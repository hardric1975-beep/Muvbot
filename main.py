import os, logging, asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import replicate
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
if REPLICATE_TOKEN:
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_TOKEN
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Muvbot ONLINE 24/7\nSend PHOTO to make VIDEO!")
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("📥 Generating... 30-60 sec boss 🙏")
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        output = await asyncio.to_thread(lambda: replicate.run("stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51ffcd3958fdec167e29b1a3398b055", input={"input_image": file.file_path, "motion_bucket_id": 127, "frames_per_second": 6}))
        video_url = output if isinstance(output, str) else output[0]
        await update.message.reply_video(video=video_url, caption="Done boss! 24/7 ✅")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:200]}")
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
if __name__ == "__main__":
    main()
