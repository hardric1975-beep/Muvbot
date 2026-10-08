import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import fal_client

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
FAL_KEY = os.getenv("FAL_KEY")

# fal-client automatically reads FAL_KEY from the environment
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("MuvBot READY 🔥 Send photo with caption like 'ghibli studio style'")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        caption = update.message.caption or "ghibli studio style, anime"
        await update.message.reply_text(f"🎨 Making {caption}... 15 sec")

        # 1. Download the image from Telegram into memory
        tg_file = await update.message.photo[-1].get_file()
        image_bytes = await tg_file.download_as_bytearray()

        # 2. Upload it securely to Fal's ephemeral storage to get a temporary valid URL
        image_url = fal_client.upload(image_bytes, "image/jpeg")
        logging.info(f"Uploaded to Fal storage: {image_url}")

        # 3. Submit to the Flux Dev Image-to-Image endpoint
        result = fal_client.subscribe(
            "fal-ai/flux/dev/image-to-image",
            arguments={
                "prompt": caption,
                "image": image_url,  # <-- FIXED: key must be 'image', not 'image_url'
                "strength": 0.75,
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "num_images": 1,
                "output_format": "jpeg"
            }
        )

        logging.info(f"Fal result: {result}")
        out_url = result["images"][0]["url"]

        await update.message.reply_photo(photo=out_url, caption=f"Done ✨ {caption}")

    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    if not BOT_TOKEN or not FAL_KEY:
        logging.error("Missing BOT_TOKEN or FAL_KEY environment variables.")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
