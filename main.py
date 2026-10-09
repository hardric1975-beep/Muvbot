
import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# Load Railway variables - supports both names
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# FREE Ghibli brain model - no billing
API_URL = "https://huggingface.co"

# Format headers securely
headers = {}
if HF_TOKEN:
    # Cleans out accidental spaces if copy-pasted wrong in Railway
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
        
        # FIXED: Correctly grab the dictionary out of the list first!
        if isinstance(data, list) and len(data) > 0:
            first_result = data[0]
            if isinstance(first_result, dict):
                return first_result.get("generated_text", "").strip()
            
        # Handle API loading statuses or errors safely without breaking
        if isinstance(data, dict):
            if "error" in data:
                error_msg = str(data["error"])
                return f"The forest spirit is waking up... try sending your message again in a few seconds! ({error_msg[:50]})"
            if "estimated_time" in data:
                return "The forest spirits are waking up... give them just a moment to answer."
                
        return "The forest is completely quiet right now... try asking again."
    except Exception as e:
        print(f"HF Error: {e}")
        return "A gust of wind disrupted the connection, try again!"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Safety checks to prevent empty message crashes
    if not update.message or not update.message.text:
        return
        
    text = update.message.text
    
    try:
        # Send a "typing..." action so the user knows the AI is processing
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        
        reply = ask_ghibli_brain(text)
        await update.message.reply_text(reply)
    except Exception as e:
        print(f"Telegram Handler Error: {e}")

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: Set BOT_TOKEN or TELEGRAM_TOKEN in Railway Variables!")
    else:
        print("✨ MuvBot online with FREE Ghibli Brain!")
        app = Application.builder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  
        app.run_polling()

