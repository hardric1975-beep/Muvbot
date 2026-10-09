
import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Load Railway variables - supports both names
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# FREE Ghibli brain model - no billing
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

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
            return data[0].get("generated_text", "").strip()
        if isinstance(data, dict) and "error" in data:
            # Model loading
            return f"🌱 *The forest spirit is waking up... try again in 10s* ({data['error'][:80]})"
        return "🌱 *The forest is quiet right now...*"
    except Exception as e:
        print(f"HF Error: {e}")
        return "✨ *A gust of wind disrupted the connection, try again!*"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return
    # reply in telegram
    async with context.typing_action():
        reply = ask_ghibli_brain(text)
        await update.message.reply_text(reply)

if __name__ == "__main__":
    if not TOKEN or not HF_TOKEN:
        print("ERROR: Set BOT_TOKEN and HF_TOKEN in Railway Variables!")
    else:
        print("✨ MuvBot online with FREE Ghibli Brain!")
        app = Application.builder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.run_polling()

