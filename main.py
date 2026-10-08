import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import fal_client

# Setup logging
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
FAL_KEY = os.getenv("FAL_KEY")

# Set FAL key
os.environ["FAL_KEY"] = FAL_KEY

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey! 👋 Send me a photo + caption like 'make this ghibli' or 'pixar style' and I'll transform it!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        caption = update.message.caption or "ghibli studio style"
        await update.message.reply_text(f"🎨 Creating: {caption}... wait 15 sec")

        # Get photo file
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        # Upload to fal
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(photo_bytes)
            tmp_path = tmp.name

        # Use fal to transform
        image_url = fal_client.upload_file(tmp_path)

        result = fal_client.subscribe(
            "fal-ai/flux/dev",
            arguments={
                "prompt": f"{caption}, high quality, detailed",
                "image_url": image_url,
                "strength": 0.85
            }
        )

        # Get result image
        if result and "images" in result and len(result["images"]) > 0:
            out_url = result["images"][0]["url"]
            await update.message.reply_photo(photo=out_url, caption=f"Done! ✨ {caption}")
        else:
            await update.message.reply_text(f"Result: {result}")

        os.remove(tmp_path)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {e}\nCheck logs!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
