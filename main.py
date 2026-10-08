import os
import logging
import asyncio
import base64
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
    if update.message:
        instructions = (
            "🔥 **MuvBot Photo-to-Video Engine Online!**\n\n"
            "Upload a photo and write what you want to happen using the `/animate` command in the caption.\n\n"
            "👉 **Example Caption:**\n"
            "`/animate cinematic slow camera zoom, smoke floating in the background, 4k detail`"
        )
        await update.message.reply_text(instructions, parse_mode="Markdown")

async def process_photo_to_video(image_bytes: bytes, animation_prompt: str) -> str:
    """
    Converts image bytes directly into a secure Data URI base64 string, 
    bypassing Fal CDN uploads to completely avoid 403 authorization issues.
    """
    loop = asyncio.get_running_loop()
    
    # Convert image bytes into a data URL pattern directly in local CPU memory
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
                "prompt": animation_prompt,
                "start_image_url": data_uri,  # Uses the direct data URI format string safely
                "duration": 5,                # Generates a standard 5-second video asset
                "generate_audio": False
            }
        )
    )
    logger.info(f"Fal pipeline complete. Output payload dictionary: {result}")
    return result["video"]["url"]

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes incoming photos containing the precise text prefix parameter."""
    if not update.message or not update.message.photo:
        return

    caption_text = update.message.caption or ""
    
    # Strict validation check for the /animate command string sequence
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
        "🎬 **Processing your video animation layers...**\n*This will take around 20-30 seconds.*", 
        parse_mode="Markdown"
    )

    try:
        # Fetch the highest resolution image version uploaded by the user
        tg_file = await update.message.photo[-1].get_file()
        image_bytes = await tg_file.download_as_bytearray()

        # Run calculation pipeline safely in thread workers
        video_url = await process_photo_to_video(bytes(image_bytes), prompt_modifier)

        # Transmit the finalized MP4 file down to the active client device
        await update.message.reply_video(
            video=video_url, 
            caption=f"✨ **Photo Animated Successfully!**\nPrompt: _{prompt_modifier}_", 
            parse_mode="Markdown"
        )
        await status_message.delete()

    except Exception as e:
        logger.error(f"Ecosystem compilation sequence failure event: {e}", exc_info=True)
        await status_message.edit_text(f"❌ Video compilation failed:\n`{e}`", parse_mode="Markdown")

def main():
    if not BOT_TOKEN or not FAL_KEY:
        logger.error("Configuration strings missing. Check that BOT_TOKEN and FAL_KEY are populated inside .env.")
        return
        
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    logger.info("MuvBot engine validation verified. Long polling active...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

