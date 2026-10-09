import os
import io
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# Load Railway environment variables
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# API Endpoints
TEXT_API_URL = "https://huggingface.co"
IMAGE_API_URL = "https://huggingface.co"

# Set up headers if API token is provided
headers = {"Authorization": f"Bearer {HF_TOKEN.strip()}"} if HF_TOKEN else {}


def ask_ghibli_brain(user_message):
    """Generates conversational text responses using Zephyr-7b."""
    system_prompt = (
        "You are a gentle, whimsical AI inspired by Studio Ghibli. "
        "Warm, nostalgic, cozy, connected to nature and magic. Keep answers short and comforting."
    )
    prompt = f"<|system|>{system_prompt}</s><|user|>{user_message}</s><|assistant|>"
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 150, "temperature": 0.7, "return_full_text": False}
    }
    try:
        response = requests.post(TEXT_API_URL, headers=headers, json=payload, timeout=30)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            first_result = data[0]
            if isinstance(first_result, dict):
                return first_result.get("generated_text", "").strip()
        if isinstance(data, dict):
            if "error" in data:
                return f"The forest spirit is waking up... try again in a moment. ({str(data['error'])[:50]})"
        return "The forest is completely quiet right now... try asking again."
    except Exception as e:
        print(f"HF Text Error: {e}")
        return "A gust of wind disrupted the connection, try again!"


def generate_image_from_prompt(prompt_text):
    """Sends a text prompt to SDXL and returns raw image bytes."""
    payload = {"inputs": prompt_text}
    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json=payload, timeout=45)
        
        # Check if the response contains valid image binary data
        if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("image/"):
            return response.content
            
        # Handle model loading or failure details safely
        try:
            error_data = response.json()
            if isinstance(error_data, dict) and "error" in error_data:
                return f"The canvas is dusty... give the spirits a few seconds to mix the paint. ({str(error_data['error'])[:50]})"
        except Exception:
            pass
            
        return "The spirits couldn't draw that right now. Try a different description!"
    except Exception as e:
        print(f"HF Image Error: {e}")
        return "A gust of wind ruined the drawing template. Try again!"


async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    lower_text = text.lower()

    # 1. COMMAND: /start
    if text.startswith("/start"):
        await update.message.reply_text(
            "🍃 *A tiny forest spirit rustles in the bushes...*\n"
            "Hello! I am MuvBot.\n\n"
            "💬 Chat with me normally for Ghibli wisdom.\n"
            "🎨 Type `/generate <your prompt>` to sketch an artistic creation!"
        )
        return

    # 2. COMMAND: /generate <prompt>
    if text.startswith("/generate"):
        # Remove the word "/generate" to isolate just the description text
        prompt_text = text[9:].strip()
        
        if not prompt_text:
            await update.message.reply_text("✨ Please provide a description! Example: `/generate a floating wizard castle`")
            return
            
        await update.message.reply_text("🎨 *The canvas is being prepared... drawing your vision now.*")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
        
        result = generate_image_from_prompt(prompt_text)
        
        # If the result is a string, it's an error message. Otherwise, it's raw image bytes.
        if isinstance(result, str):
            await update.message.reply_text(result)
        else:
            # Wrap binary data bytes into an in-memory file object for Telegram to upload
            image_file = io.BytesIO(result)
            image_file.name = "generated_art.png"
            await update.message.reply_photo(photo=image_file, caption=f"✨ Created your vision: '{prompt_text}'")
        return

    # 3. CONVERSATION: Standard chatting goes directly to the text brain
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        reply = ask_ghibli_brain(text)
        await update.message.reply_text(reply)
    except Exception as e:
        print(f"Brain execution error: {e}")


if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: Set BOT_TOKEN or TELEGRAM_TOKEN in Railway Variables!")
    else:
        print("✨ MuvBot online with Text Chatting and /generate Image capabilities!")
        app = Application.builder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, handle_everything))  
        app.run_polling()


