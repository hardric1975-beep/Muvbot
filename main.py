
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

BOT_TOKEN = os.getenv("BOT_TOKEN")
FAL_KEY = os.getenv("FAL_KEY")

# Force assign variables into the target OS runtime contexts
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY.strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends initialization guidance directly to target users."""
    if update.message:
        instructions = (
            "🔥 **MuvBot Photo-to-Video Engine Active!**\n\n"
            "Upload an image file and write your movement prompt using the `/animate` command.\n\n"
            "👉 **Example Caption:**\n"
            "`/animate slow cinematic camera pan, cinematic lighting, 4k resolution`"
        )
        await update.message.reply_text(instructions, parse_mode="Markdown")

async def process_photo_to_video(image_bytes: bytes, prompt: str) -> str:
    """
    Converts image bytes directly into a secure Data URI base64 string, 
    bypassing Fal CDN uploads to completely avoid 403 authorization issues.
    """
    loop = asyncio.get_running_loop()
    
    def convert_to_data_uri():
        base64_encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{base64_encoded}"

    data_uri = await loop.run_in_executor(None, convert_to_data_uri)
    logger.info("Successfully converted input image buffer into local Data URI format.")

    # Fire direct photo-to-video animation endpoint using the memory string
    result = await loop.run_in_executor(
        None,
        lambda: fal_client.subscribe(
            "fal-ai/kling-video/v3/standard/image-to-video",
            arguments={
                "prompt": prompt,
                "start_image_url": data_uri,  # Safe, unblocked base64 path
                "duration": 5,                # Generates a standard 5-second video asset
                "generate_audio": False       # Disabled ambient engine audio trackers
            }
        )
    )
    logger.info(f"Fal pipeline complete. Output payload dictionary: {result}")
    return result["video"]["url"]

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parses incoming photos to look for precise explicit operational prefixes."""
    if not update.message or not update.message.photo:
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
        # Download local binary payload straight out of the Telegram CDN network
        tg_file = await update.message.photo[-1].get_file()
        image_bytes = await tg_file.download_as_bytearray()

        # Execute pure Fal AI video pass processing arrays
        video_url = await process_photo_to_video(bytes(image_bytes), prompt_modifier)

        # Deliver final compilation product to user client application container
        await update.message.reply_video(
            video=video_url, 
            caption=f"✨ **Photo Animated Successfully!**\nPrompt: _{prompt_modifier}_", 
            parse_mode="Markdown"
        )
        await status_message.delete()

    except Exception as e:
        logger.error(f"Global pipeline error event: {e}", exc_info=True)
        await status_message.edit_text(f"❌ Video compilation failed:\n`{e}`", parse_mode="Markdown")

def main():
    """Validates parameters and starts the application long-polling loop."""
    print("--- MUVBOT BOOT DIAGNOSTICS ---")
    print(f"BOT_TOKEN loaded: {'✅ Yes' if BOT_TOKEN else '❌ No'}")
    print(f"FAL_KEY loaded: {'✅ Yes' if FAL_KEY else '❌ No'}")
    
    if FAL_KEY and (FAL_KEY.startswith(" ") or FAL_KEY.endswith(" ")):
        print("⚠️ WARNING: Your FAL_KEY has hidden spaces! Cleaning it up automatically...")

    if not BOT_TOKEN:
        logger.error("Bot cannot execute. Critical environment string BOT_TOKEN is missing.")
        return
        
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("\nInitialization valid. Polling live...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
