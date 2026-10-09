
async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    lower_text = text.lower()

    # 1. COMMAND: /start
    if text.startswith("/start"):
        await update.message.reply_text("🍃 Hello! I am MuvBot. Chat with me normally, or type `/generate <prompt>` to sketch something!")
        return

    # 2. COMMAND: /animate
    if text.startswith("/animate") or "animate" in lower_text:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VIDEO)
        await update.message.reply_text(
            "🎬 *The animation gears are turning...*\n\n"
            "To animate a picture, please make sure you upload the photo directly into this chat first, "
            "then type `/animate` as the caption!"
        )
        return

    # 3. COMMAND: /generate <prompt>
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

    # Standard Chat (Only runs if no commands match)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    reply = ask_ghibli_brain(text)
    await update.message.reply_text(reply)


