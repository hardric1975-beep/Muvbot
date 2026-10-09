import os
import logging
import asyncio
import base64
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import fal_client

# Setup clean visual logging architecture
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fetch environment variables safely
BOT_TOKEN = os.getenv("BOT_TOKEN")
FAL_KEY = os.getenv("FAL_KEY")

# CRASH PROTECTION: Pre-clean and securely map key configurations
if FAL_KEY:
    FAL_KEY = FAL_KEY.strip().replace('"', '').replace("'", "")
    os.environ["FAL_KEY"] = FAL_KEY

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends immediate usage instructions to users."""
    if update.message:
        instructions = (
            "🔥 **MuvBot Photo-to-Video Engine Active!**\n\n"
            "Upload an image file and write your movement prompt using the `/animate` command.\n\n"
            "👉 **Example Caption:**\n"
            "`/animate slow cinematic camera pan, cinematic lighting, 4k resolution`"
        )
        await update.message.reply_text(instructions, parse_mode="Markdown")

async def process_photo_to_video(image_bytes: bytes, prompt: str) -> str:
    """Converts image bytes safely to a base64 Data URI string, bypassing CDN errors."""
    loop = asyncio.get_running_loop()
    
    def convert_to_data_uri():
        base64_encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{base64_encoded}"

    data_uri = await loop.run_in_executor(None, convert_to_data_uri)
    logger.info("Successfully converted input image buffer into base64 Data URI.")

    # Submit payload directly to Kling V3 standard video generation engine
    result = await loop.run_in_executor(
        None,
        lambda: fal_client.subscribe(
            "fal-ai/kling-video/v3/standard/image-to-video",
            arguments={
                "prompt": prompt,
                "start_image_url": data_uri,
                "duration": 5,
                "generate_audio": False
            }
        )
    )
    logger.info(f"Fal operation resolved successfully: {result}")
    return result["video"]["url"]

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts and parses incoming picture command strings."""
    if not update.message or not update.message.photo:
        return

    # Check key status inside request block to avoid unexpected execution drops
    if not os.getenv("FAL_KEY"):
        await update.message.reply_text("❌ System configuration error: The server's Fal AI Key is missing or unauthenticated.")
        return

    caption_text = update.message.caption or ""
    
    if not caption_text.startswith("/animate"):
        await update.message.reply_text(
            "⚠️ **Command missing!**\nPlease include `/animate [your description]` directly inside the photo caption box.",
            parse_mode="Markdown"
        )
        return

    prompt_modifier = caption_text.replace("/animate", "").strip()
    if not prompt_modifier:
        await update.message.reply_text("❌ Please include an animation prompt! Example: `/animate camera zooming in`")
        return

    status_message = await update.message.reply_text("🎬 **Processing video physics frames...**\n*Estimated duration: ~20-30s*")

    try:
        # Download image directly from Telegram backend lines
        tg_file = await update.message.photo[-1].get_file()
        image_bytes = await tg_file.download_as_bytearray()

        # Fire core worker compilation task
        video_url = await process_photo_to_video(bytes(image_bytes), prompt_modifier)

        # Transmit output MP4 file back down to client user
        await update.message.reply_video(
            video=video_url, 
            caption=f"✨ **Photo Animated Successfully!**\nPrompt: _{prompt_modifier}_", 
            parse_mode="Markdown"
        )
        await status_message.delete()

    except Exception as e:
        logger.error(f"Execution error caught: {e}", exc_info=True)
        await status_message.edit_text(f"❌ Video compilation failed:\n`{e}`")

def main():
    """Initializes safe boot logging sequences."""
    print("--- MUVBOT BOOT DIAGNOSTICS ---")
    print(f"BOT_TOKEN loaded: {'✅ Yes' if BOT_TOKEN else '❌ No'}")
    print(f"FAL_KEY loaded: {'✅ Yes' if FAL_KEY else '❌ No'}")
    
    if not BOT_TOKEN:
        logger.error("Bot cannot execute: BOT_TOKEN is missing entirely.")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("\nStarting bot polling loop...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()


