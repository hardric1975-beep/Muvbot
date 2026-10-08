
import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import fal_client

# Load variables from .env file
load_dotenv()

# Setup logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
FAL_KEY = os.getenv("FAL_KEY")

if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends immediate instructions to the user when they initialize the bot."""
    instructions = (
        "🔥 **MuvBot Photo-to-Video Engine Ready!**\n\n"
        "Upload a photo and write what you want to happen using the `/animate` command in the caption.\n\n"
        "👉 **Example Caption:**\n"
        "`/animate hair blowing in the wind, cinematic slow camera zoom, 4k highly detailed`"
    )
    await update.message.reply_text(instructions, parse_mode="Markdown")

async def process_photo_to_video(image_bytes: bytes, animation_prompt: str) -> str:
    """
    Uploads the photo to Fal CDN and uses Kling V3 to animate 
    the exact photo into a video file asynchronously.
    """
    loop = asyncio.get_running_loop()
    
    # 1. Upload raw bytes to secure storage bucket to get a public URL for the model
    uploaded_url = await loop.run_in_executor(
        None, 
        lambda: fal_client.upload(image_bytes, "image/jpeg")
    )
    logger.info(f"Source photo hosted at Fal storage: {uploaded_url}")

    # 2. Fire direct photo-to-video animation endpoint (Kling V3 Standard)
    result = await loop.run_in_executor(
        None,
        lambda: fal_client.subscribe(
            "fal-ai/kling-video/v3/standard/image-to-video",
            arguments={
                "prompt": animation_prompt,
                "start_image_url": uploaded_url,  # Explicit structural parameter for the photo
                "duration": 5,                    # Generates a clean 5-second video clip
                "generate_audio": False
            }
        )
    )
    logger.info(f"Fal execution output payload: {result}")
    return result["video"]["url"]

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming photos containing the text prefix."""
    if not update.message or not update.message.photo:
        return

    caption_text = update.message.caption or ""
    
    # Strict validation filter check for /animate command
    if not caption_text.startswith("/animate"):
        await update.message.reply_text(
            "⚠️ **Command missing!**\nPlease include `/animate [your description]` directly inside the photo caption box.",
            parse_mode="Markdown"
        )
        return

    # Extract the user's specific text animation instructions
    prompt_modifier = caption_text.replace("/animate", "").strip()
    if not prompt_modifier:
        await update.message.reply_text("❌ Please include an animation description! Example: `/animate camera panning left`")
        return

    status_message = await update.message.reply_text(
        "🎬 **Animating your photo...**\n*Processing video physics frames (~20-30 seconds)*", 
        parse_mode="Markdown"
    )

    try:
        # Fetch the highest resolution image version uploaded by the user
        tg_file = await update.message.photo[-1].get_file()
        image_bytes = await tg_file.download_as_bytearray()

        # Run compilation task without blocking our primary execution thread
        video_url = await process_photo_to_video(bytes(image_bytes), prompt_modifier)

        # Send the final generated MP4 video back to the user
        await update.message.reply_video(
            video=video_url, 
            caption=f"✨ **Photo Animated Successfully!**\nPrompt: _{prompt_modifier}_", 
            parse_mode="Markdown"
        )
        await status_message.delete()

    except Exception as e:
        logger.error(f"Ecosystem compilation sequence failure event: {e}", exc_info=True)
        await status_message.edit_text(f"❌ Video compilation failed: {e}")

def main():
    if not BOT_TOKEN or not FAL_KEY:
        logger.error("Configuration critical strings missing. Populate BOT_TOKEN and FAL_KEY in your .env configuration.")
        return
        
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    logger.info("MuvBot Photo-to-Video Engine Online. Polling Active...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
