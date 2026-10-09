import os
import discord
from discord.ext import commands
import requests

# 1. Load your Railway environment variables
TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")  # Hidden behind asterisks in your screenshot

# 2. Setup Discord bot intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_config=None, command_prefix="!", intents=intents)

# 3. Hugging Face API Configuration
# You can change this model URL to any text generation model you prefer
API_URL = "https://huggingface.co"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def ask_ghibli_brain(user_message):
    """Sends the message to Hugging Face with a Ghibli personality prompt."""
    
    # Define the Ghibli personality instructions
    system_prompt = (
        "You are a gentle, whimsical, and comforting AI brain inspired by Studio Ghibli films. "
        "Your tone is warm, nostalgic, and deeply connected to nature, magic, and simple joys. "
        "Keep your answers relatively short, cozy, and helpful, as if you are a friendly forest spirit."
    )
    
    # Format the payload for an instruction/chat model
    prompt = f"<s>[SYSTEM] {system_prompt} [/SYSTEM] [USER] {user_message} [/USER] [BOT]"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 150,
            "temperature": 0.7,
            "top_p": 0.95
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response_json = response.json()
        
        # Parse the text result from the API response
        if isinstance(response_json, list) and "generated_text" in response_json[0]:
            full_text = response_json[0]["generated_text"]
            # Extract just the bot's response after the last prompt tag
            bot_response = full_text.split("[BOT]")[-1].strip()
            return bot_response
        else:
            return "🌱 *The forest is quiet right now...* (API Error)"
            
    except Exception as e:
        print(f"Error calling Hugging Face: {e}")
        return "✨ *A gust of wind disrupted the connection...*"

# 4. Bot Events & Commands
@bot.event
async def on_ready():
    print(f'✨ Muvbot is online as {bot.user} with Ghibli Brain active!')

@bot.event
async def on_message(message):
    # Prevent the bot from responding to itself
    if message.author == bot.user:
        return

    # Trigger the brain if the bot is mentioned or if it's a direct command
    if bot.user.mentioned_in(message):
        # Clean the mention out of the text
        clean_prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not clean_prompt:
            await message.reply("🍃 *Tilts head curiously and waits for you to speak.*")
            return
            
        async with message.channel.typing():
            reply = ask_ghibli_brain(clean_prompt)
            await message.reply(reply)

    await bot.process_commands(message)

# 5. Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)

