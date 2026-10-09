
import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# Load Railway variables - supports both names securely
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# FREE Ghibli brain model - no billing
API_URL = "https://huggingface.co"

headers = {}
if HF_TOKEN:
    headers["Authorization"] = f"Bearer {HF_TOKEN.strip()}"

def ask_ghibli_brain(user_message):
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
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            first_result = data[0]
            if isinstance(first_result, dict):
                return first_result.get("generated_text", "").strip()
            
        if isinstance(data, dict):
            if "error" in data:
                return f"The forest spirit is waking up... try again in a moment. ({str(data['error'])[:50]})"
            if "estimated_time" in data:
                return "The forest spirits are waking up... give them just a moment to answer."
                
        return "The forest is completely quiet right now... try asking again."
    except Exception as e:
        print(f"HF Error: {e}")
        return "A gust of wind disrupted the connection, try again!"

# CRITICAL: Unified text handler that processes commands and standard conversation
async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # Handle incoming Text and Commands
    if update.message.text:
        text = update.message.text
        lower_text = text.lower()

        # 1. COMMAND CAPTURE: Photo-to-Video feature logic
        if "/photo_to_video" in lower_text or "photo to video" in lower_text:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VIDEO)
            # Add your core processing or generation execution pipeline below this line
            await update.message.reply_text("🎬 *The whimsical machinery whirs into life...* Ready to transform your memories. Please upload or link your image asset below!")
            return

        # 2. COMMAND CAPTURE: Explicit /start catch
        if text.startswith("/start"):
            await update.message.reply_text("🍃 *A tiny forest spirit rustles in the bushes...*\nHello! I am MuvBot. Share your thoughts or send commands, and I will answer.")
            return

        # 3. CONVERSATION CAPTURE: Send everything else directly to the Ghibli Brain
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
        print("✨ MuvBot online and monitoring all command text integrations!")
        app = Application.builder().token(TOKEN).build()
        
        # FIXED: Removed "~filters.COMMAND" so absolutely everything is captured and handled
        app.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, handle_everything))  
        
        app.run_polling()

