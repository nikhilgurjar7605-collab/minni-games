import os
import json
import random
import asyncio
import logging
from openai import AsyncOpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ─── CONFIG ─────────────────────────────
BOT_TOKEN = "8380616064:AAGCdwaWNRDxa0tThc8JMprWJfWhtQ5bl-4"
OPENAI_KEY = "sk-5678efgh5678efgh5678efgh5678efgh5678efgh"
SCORES_FILE = "scores.json"

client = AsyncOpenAI(api_key=OPENAI_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ACTIVE_QUESTIONS = {}

# ─── QUESTIONS ──────────────────────────
QUESTIONS = [
    {"q": "Capital of France?", "options": ["Berlin","Paris","Rome","Madrid"], "answer": "Paris"},
    {"q": "2 + 2 = ?", "options": ["3","4","5","6"], "answer": "4"},
]

# ─── AI FUNCTION ────────────────────────
async def ask_gpt(prompt):
    try:
        res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ─── COMMANDS ───────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot started!\nUse /play")

async def play(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    q = random.choice(QUESTIONS)
    ACTIVE_QUESTIONS[chat_id] = q["answer"]

    keyboard = [[InlineKeyboardButton(o, callback_data=o)] for o in q["options"]]

    await update.message.reply_text(
        q["q"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    if chat_id not in ACTIVE_QUESTIONS:
        return

    correct = ACTIVE_QUESTIONS[chat_id]

    if query.data == correct:
        await query.edit_message_text("✅ Correct!")
    else:
        await query.edit_message_text(f"❌ Wrong! Answer: {correct}")

    del ACTIVE_QUESTIONS[chat_id]

# ─── MAIN ───────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CallbackQueryHandler(answer))

    print("🚀 Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
