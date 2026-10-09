import os
import io
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

TEXT_API_URL = "https://huggingface.co"
IMAGE_API_URL = "https://huggingface.co"

headers = {"Authorization": f"Bearer {HF_TOKEN.strip()}"} if HF_TOKEN else {}

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
        response = requests.post(TEXT_API_URL, headers=headers, json=payload, timeout=30)
        data = response.json()
        
        # FIXED: This line stops the nonsense by properly digging out the text from the response list
        if isinstance(data, list) and len(data) > 0:
            return data[0].get("generated_text", "").strip()
                
        if isinstance(data, dict) and "error" in data:
            return f"The forest spirit is waking up... try again in a moment. ({str(data['error'])[:50]})"
        return "The forest is completely quiet right now... try asking again."
    except Exception as e:
        print(f"HF Text Error: {e}")
        return "A gust of wind disrupted the connection, try again!"

def generate_image_from_prompt(prompt_text):
    styled_prompt = f"{prompt_text}, studio ghibli style, beautiful anime aesthetic, whimsical, masterfully detailed, vibrant colors"
    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json=styled_prompt, timeout=45)
        if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("image/"):
            return response.content
        return "The spirits couldn't draw that right now. Try a different description!"
    except Exception as e:
        print(f"HF Image Error: {e}")
        return "A gust of wind ruined the drawing template. Try again!"

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text

    if text.startswith("/start"):
        await update.message.reply_text("🍃 Hello! I am MuvBot. Chat with me normally, or type `/generate <prompt>` to sketch something!")
        return

    if text.startswith("/generate"):
        prompt_text = text[9:].strip()
        if not prompt_text:
            await update.message.reply_text("✨ Please provide a description! Example: `/generate a floating castle`")
            return
            
        await update.message.reply_text("🎨 *Drawing your vision now...*")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
        
        result = generate_image_from_prompt(prompt_text)
        if isinstance(result, str):
            await update.message.reply_text(result)
        else:
            image_file = io.BytesIO(result)
            image_file.name = "art.png"
            await update.message.reply_photo(photo=image_file, caption=f"✨ '{prompt_text}'")
        return

    # Standard Chat
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    reply = ask_ghibli_brain(text)
    await update.message.reply_text(reply)

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: Missing BOT_TOKEN")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, handle_everything))  
        app.run_polling()


