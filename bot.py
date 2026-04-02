import os
import json
import random
import asyncio
import openai 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ─── Config ───────────────────────────────────────────────────────────────────
Gemini said
Got it! If you're switching from Anthropic (Claude) to OpenAI (ChatGPT), the code structure changes slightly because the libraries use different argument names and response formats.

Here is the updated AI Helper section and the Config setup to work with the OpenAI Python SDK.

🛠️ The Switch: ChatGPT Integration
First, make sure you have the library installed:
pip install openai

Then, replace the relevant sections in your script with this:

Python
import openai  # Change from anthropic to openai

# ─── Config ───────────────────────────────────────────────────────────────────
BOT_TOKEN   = "8380616064:AAGCdwaWNRDxa0tThc8JMprWJfWhtQ5bl-4"
OPENAI_KEY  = "sk-5678efgh5678efgh5678efgh5678efgh5678efgh" # Use your GPT Key here
SCORES_FILE = "scores.json"

# Initialize OpenAI Client
ACTIVE_QUESTIONS = {}   # chat_id -> quiz state
SITUATIONSHIP    = {}   # chat_id -> situationship state

# ─── Question Bank ────────────────────────────────────────────────────────────
QUESTIONS = [
    {"q": "What is the capital of France?",       "options": ["Berlin","Madrid","Paris","Rome"],        "answer": "Paris"},
    {"q": "Which planet is closest to the Sun?",  "options": ["Venus","Earth","Mercury","Mars"],         "answer": "Mercury"},
    {"q": "How many sides does a hexagon have?",  "options": ["5","6","7","8"],                          "answer": "6"},
    {"q": "Who wrote 'Romeo and Juliet'?",        "options": ["Dickens","Shakespeare","Austen","Twain"], "answer": "Shakespeare"},
    {"q": "What is 12 × 12?",                     "options": ["132","144","124","148"],                  "answer": "144"},
    {"q": "Which ocean is the largest?",          "options": ["Atlantic","Indian","Arctic","Pacific"],   "answer": "Pacific"},
    {"q": "What gas do plants absorb?",           "options": ["Oxygen","Nitrogen","CO2","Hydrogen"],     "answer": "CO2"},
    {"q": "How many continents are there?",       "options": ["5","6","7","8"],                          "answer": "7"},
    {"q": "What is the fastest land animal?",     "options": ["Lion","Cheetah","Horse","Leopard"],       "answer": "Cheetah"},
    {"q": "Which element has symbol 'Au'?",       "options": ["Silver","Copper","Gold","Aluminium"],     "answer": "Gold"},
    {"q": "How many bones in adult human body?",  "options": ["196","206","216","226"],                  "answer": "206"},
    {"q": "What year did World War II end?",      "options": ["1943","1944","1945","1946"],               "answer": "1945"},
    {"q": "What is the square root of 144?",      "options": ["11","12","13","14"],                      "answer": "12"},
    {"q": "Which country invented pizza?",        "options": ["USA","France","Italy","Spain"],           "answer": "Italy"},
    {"q": "How many days in a leap year?",        "options": ["364","365","366","367"],                  "answer": "366"},
]

# ─── Score Helpers ────────────────────────────────────────────────────────────
def load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_scores(scores):
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f, indent=2)

def add_score(user_id, username, points=1):
    scores = load_scores()
    if user_id not in scores:
        scores[user_id] = {"name": username, "score": 0, "correct": 0, "wrong": 0}
    scores[user_id]["name"]     = username
    scores[user_id]["score"]   += points
    scores[user_id]["correct"] += 1
    save_scores(scores)

def add_wrong(user_id, username):
    scores = load_scores()
    if user_id not in scores:
        scores[user_id] = {"name": username, "score": 0, "correct": 0, "wrong": 0}
    scores[user_id]["name"]  = username
    scores[user_id]["wrong"] += 1
    save_scores(scores)

# ─── ChatGPT AI Helper ────────────────────────────────────────────────────────
def ask_gpt(system_prompt: str, user_msg: str, max_tokens: int = 300) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # Or "gpt-3.5-turbo" for lower cost
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ AI error: {e}"
# ═══════════════════════════════════════════════════════════════════════════════
#  COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎮 *Welcome to Group Game Bot!*\n\n"
        "🟢 *Quiz*\n"
        "  /play — Trivia question\n"
        "  /leaderboard — Top players\n"
        "  /mystats — Your stats\n\n"
        "😈 *Truth or Dare*\n"
        "  /truth — Get a truth question\n"
        "  /dare — Get a dare challenge\n"
        "  /tod — Spin Truth OR Dare randomly\n\n"
        "💘 *Situationship Game*\n"
        "  /situationship — Start a romantic scenario\n"
        "  /mytype — Discover your vibe type\n\n"
        "ℹ️ /help — Show this menu"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await start(update, ctx)

# ───────────────────────────── QUIZ ──────────────────────────────────────────

async def play(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in ACTIVE_QUESTIONS:
        await update.message.reply_text("⚠️ A question is already active! Answer it first.")
        return

    question = random.choice(QUESTIONS)
    options  = question["options"][:]
    random.shuffle(options)

    ACTIVE_QUESTIONS[chat_id] = {
        "answer":      question["answer"],
        "answered_by": set(),
        "question":    question["q"],
    }

    keyboard = [[InlineKeyboardButton(opt, callback_data=f"ans|{opt}")] for opt in options]
    msg = await update.message.reply_text(
        f"❓ *{question['q']}*\n\nChoose your answer below 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    ACTIVE_QUESTIONS[chat_id]["message_id"] = msg.message_id
    asyncio.create_task(expire_question(ctx, chat_id, msg.message_id, question["answer"]))

async def expire_question(ctx, chat_id, message_id, answer):
    await asyncio.sleep(30)
    if chat_id in ACTIVE_QUESTIONS and ACTIVE_QUESTIONS[chat_id].get("message_id") == message_id:
        del ACTIVE_QUESTIONS[chat_id]
        try:
            await ctx.bot.edit_message_text(
                chat_id=chat_id, message_id=message_id,
                text=f"⏰ *Time's up!*\nCorrect answer: *{answer}*\n\nUse /play to try again!",
                parse_mode="Markdown"
            )
        except Exception:
            pass

async def handle_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer()
    chat_id  = query.message.chat_id
    user     = query.from_user
    user_id  = str(user.id)
    username = user.first_name or user.username or "Player"

    if chat_id not in ACTIVE_QUESTIONS:
        await query.answer("❌ No active question!", show_alert=True)
        return

    state = ACTIVE_QUESTIONS[chat_id]
    if user_id in state["answered_by"]:
        await query.answer("You already answered!", show_alert=True)
        return

    state["answered_by"].add(user_id)
    chosen = query.data.split("|", 1)[1]

    if chosen == state["answer"]:
        add_score(user_id, username)
        total = load_scores()[user_id]["score"]
        await query.answer(f"✅ Correct! +1 point (Total: {total})", show_alert=True)
        del ACTIVE_QUESTIONS[chat_id]
        await query.edit_message_text(
            f"✅ *{username}* got it right!\n\n"
            f"❓ *{state['question']}*\n"
            f"✔️ Answer: *{state['answer']}*\n\n"
            f"🏅 {username} now has *{total} point(s)*\n\nUse /play for next question!",
            parse_mode="Markdown"
        )
    else:
        add_wrong(user_id, username)
        await query.answer(f"❌ Wrong! Answer: {state['answer']}", show_alert=True)

async def leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    scores = load_scores()
    if not scores:
        await update.message.reply_text("🏆 No scores yet! Use /play to start.")
        return
    sorted_p = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    medals   = ["🥇","🥈","🥉"]
    text     = "🏆 *LEADERBOARD* 🏆\n" + "─"*25 + "\n"
    for i, (uid, d) in enumerate(sorted_p[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        total = d["correct"] + d["wrong"]
        acc   = round(d["correct"]/total*100) if total else 0
        text += f"{medal} *{d['name']}*\n   ⭐ {d['score']} pts  |  ✅ {d['correct']}  ❌ {d['wrong']}  |  🎯 {acc}%\n"
    text += "\n_Use /play to climb the ranks!_"
    await update.message.reply_text(text, parse_mode="Markdown")

async def mystats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id  = str(update.effective_user.id)
    scores   = load_scores()
    if user_id not in scores:
        await update.message.reply_text("📊 You haven't played yet! Use /play to start.")
        return
    d        = scores[user_id]
    total    = d["correct"] + d["wrong"]
    acc      = round(d["correct"]/total*100) if total else 0
    sorted_p = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    rank     = next((i+1 for i,(uid,_) in enumerate(sorted_p) if uid==user_id), "?")
    await update.message.reply_text(
        f"📊 *Your Stats — {d['name']}*\n─────────────────────\n"
        f"🏅 Rank: *#{rank}*\n⭐ Points: *{d['score']}*\n"
        f"✅ Correct: *{d['correct']}*\n❌ Wrong: *{d['wrong']}*\n🎯 Accuracy: *{acc}%*",
        parse_mode="Markdown"
    )

# ───────────────────────── TRUTH OR DARE ─────────────────────────────────────

async def truth(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "Player"
    keyboard = [[
        InlineKeyboardButton("😊 Mild",    callback_data="truth|mild"),
        InlineKeyboardButton("😏 Medium",  callback_data="truth|medium"),
        InlineKeyboardButton("🌶️ Spicy",  callback_data="truth|spicy"),
        InlineKeyboardButton("🔥 Savage",  callback_data="truth|savage"),
    ]]
    await update.message.reply_text(
        f"😇 *Truth for {name}!*\nPick your spice level 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def dare(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "Player"
    keyboard = [[
        InlineKeyboardButton("😄 Easy",    callback_data="dare|easy"),
        InlineKeyboardButton("😅 Medium",  callback_data="dare|medium"),
        InlineKeyboardButton("😬 Hard",    callback_data="dare|hard"),
        InlineKeyboardButton("🫣 Extreme", callback_data="dare|extreme"),
    ]]
    await update.message.reply_text(
        f"😈 *Dare for {name}!*\nHow brave are you? 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def tod(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    choice = random.choice(["truth", "dare"])
    levels = {"truth": ["mild","medium","spicy","savage"], "dare": ["easy","medium","hard","extreme"]}
    emojis = {"truth": ["😊","😏","🌶️","🔥"],            "dare":  ["😄","😅","😬","🫣"]}
    keyboard = [[
        InlineKeyboardButton(f"{emojis[choice][i]} {lvl.capitalize()}", callback_data=f"{choice}|{lvl}")
        for i, lvl in enumerate(levels[choice])
    ]]
    icon = "😇" if choice == "truth" else "😈"
    await update.message.reply_text(
        f"{icon} The wheel landed on... *{choice.upper()}!*\nPick your level 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_tod(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer("Generating with AI... 🤖")
    user     = query.from_user
    name     = user.first_name or "Player"
    parts    = query.data.split("|")
    tod_type = parts[0]
    level    = parts[1]

    if tod_type == "truth":
        system = (
            "You are a fun, witty Truth or Dare game host for a Telegram group. "
            "Generate ONE truth question. Keep it appropriate for a friend group (16+). "
            "No explicit sexual content. Make it interesting and conversation-starting. "
            "Return ONLY the question, no preamble or extra text."
        )
        prompt = f"Give me a {level} level truth question for someone named {name}."
        emoji, label = "😇", "TRUTH"
    else:
        system = (
            "You are a fun, creative Truth or Dare game host for a Telegram group. "
            "Generate ONE dare challenge. Keep it safe, fun, and appropriate (16+). "
            "No harmful, illegal, or explicitly sexual dares. Be creative and funny. "
            "Return ONLY the dare, no preamble or extra text."
        )
        prompt = f"Give me a {level} level dare challenge for someone named {name}."
        emoji, label = "😈", "DARE"

    result = ask_claude(system, prompt, max_tokens=150)

    keyboard = [[
        InlineKeyboardButton("🔄 New One", callback_data=query.data),
        InlineKeyboardButton("✅ Done!",   callback_data="tod_done"),
    ]]
    await query.edit_message_text(
        f"{emoji} *{label} for {name}!*\n\n_{result}_\n\nLevel: *{level}*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_tod_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Nice! 👏")
    await query.edit_message_text("✅ Challenge completed! Use /tod /truth /dare for more 🎉")

# ───────────────────────── SITUATIONSHIP ─────────────────────────────────────

SITUATION_VIBES = [
    "awkward first date 🍝",
    "late night texting 🌙",
    "situationship where nobody confesses 💔",
    "two people pretending they're just friends 😶",
    "accidentally falling in love on a road trip 🚗",
    "rivals who secretly like each other ⚔️❤️",
    "childhood friends reuniting after years 🥺",
    "coffee shop regular and barista ☕",
    "fake dating turning real 💘",
    "one-sided crush who doesn't know it 😭",
    "strangers stuck together in an elevator 🛗",
    "best friend's sibling who is off limits 🚫💕",
]

SIT_SYSTEM = (
    "You are a creative, emotionally intelligent storyteller running a 'situationship' "
    "roleplay game for a Telegram group. Generate a short romantic/dramatic scenario "
    "(3-4 sentences) based on the vibe given. End with a cliffhanger question "
    "that the player must respond to. Keep it fun, emotionally engaging, and PG-13. "
    "No explicit content. Use emojis naturally."
)

async def situationship(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id  = update.effective_chat.id
    user     = update.effective_user
    name     = user.first_name or "Player"
    vibe     = random.choice(SITUATION_VIBES)

    await update.message.reply_text("💘 *Generating your situationship scenario...*", parse_mode="Markdown")

    scenario = ask_claude(SIT_SYSTEM, f"Create a situationship scenario for {name}. Vibe: {vibe}", max_tokens=250)

    SITUATIONSHIP[chat_id] = {
        "user_id": str(user.id),
        "name":    name,
        "vibe":    vibe,
        "history": [scenario],
    }

    keyboard = [[
        InlineKeyboardButton("💬 Continue",  callback_data="sit_continue"),
        InlineKeyboardButton("🔀 New",       callback_data="sit_new"),
        InlineKeyboardButton("💘 My Type",   callback_data="sit_mytype"),
    ]]
    await update.message.reply_text(
        f"💘 *Your Situationship* — _{vibe}_\n\n{scenario}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_situationship_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    action  = query.data
    user    = query.from_user
    name    = user.first_name or "Player"

    if action == "sit_new":
        vibe     = random.choice(SITUATION_VIBES)
        scenario = ask_claude(SIT_SYSTEM, f"Create a situationship scenario for {name}. Vibe: {vibe}", max_tokens=250)
        SITUATIONSHIP[chat_id] = {"user_id": str(user.id), "name": name, "vibe": vibe, "history": [scenario]}
        keyboard = [[
            InlineKeyboardButton("💬 Continue", callback_data="sit_continue"),
            InlineKeyboardButton("🔀 New",      callback_data="sit_new"),
            InlineKeyboardButton("💘 My Type",  callback_data="sit_mytype"),
        ]]
        await query.edit_message_text(
            f"💘 *New Situationship* — _{vibe}_\n\n{scenario}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif action == "sit_continue":
        state = SITUATIONSHIP.get(chat_id)
        if not state:
            await query.answer("Start a new one with /situationship!", show_alert=True)
            return
        context_str = "\n\n".join(state["history"][-3:])
        continuation = ask_claude(
            "You are continuing a situationship roleplay story. Add the next dramatic/romantic "
            "development in 3-4 sentences. Keep PG-13, emotionally engaging, end with a cliffhanger. Use emojis.",
            f"Story so far:\n{context_str}\n\nContinue for {state['name']} with vibe: {state['vibe']}",
            max_tokens=250
        )
        state["history"].append(continuation)
        keyboard = [[
            InlineKeyboardButton("💬 Continue", callback_data="sit_continue"),
            InlineKeyboardButton("🔀 New",      callback_data="sit_new"),
            InlineKeyboardButton("💘 My Type",  callback_data="sit_mytype"),
        ]]
        await query.edit_message_text(
            f"💘 *Situationship continues...* — _{state['vibe']}_\n\n{continuation}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif action == "sit_mytype":
        result = ask_claude(
            "You are a fun personality analyzer for a Telegram game. Tell someone their 'type' "
            "in relationships in a funny, witty way. Give them a situationship archetype title "
            "(e.g. 'The Midnight Texter', 'The One Who Leaves on Read', 'The Hopeless Romantic'). "
            "Then 2-3 fun sentences describing their vibe. PG-13. Use emojis.",
            f"Analyze the relationship type for someone named {name}.",
            max_tokens=200
        )
        await query.edit_message_text(
            f"💘 *{name}'s Situationship Type*\n\n{result}\n\n_Use /situationship to play again!_",
            parse_mode="Markdown"
        )

async def mytype(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "Player"
    await update.message.reply_text("🔮 *Analyzing your vibe...*", parse_mode="Markdown")
    result = ask_claude(
        "You are a fun personality analyzer for a Telegram game. Tell someone their 'type' "
        "in relationships in a funny, witty way. Give them a situationship archetype title "
        "(e.g. 'The Midnight Texter', 'The One Who Leaves on Read', 'The Hopeless Romantic'). "
        "Then 2-3 fun sentences describing their vibe. PG-13. Use emojis.",
        f"Analyze the relationship type for someone named {name}.",
        max_tokens=200
    )
    await update.message.reply_text(
        f"💘 *{name}'s Situationship Type*\n\n{result}",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",         start))
    app.add_handler(CommandHandler("help",          help_cmd))
    app.add_handler(CommandHandler("play",          play))
    app.add_handler(CommandHandler("leaderboard",   leaderboard))
    app.add_handler(CommandHandler("mystats",       mystats))
    app.add_handler(CommandHandler("truth",         truth))
    app.add_handler(CommandHandler("dare",          dare))
    app.add_handler(CommandHandler("tod",           tod))
    app.add_handler(CommandHandler("situationship", situationship))
    app.add_handler(CommandHandler("mytype",        mytype))

    app.add_handler(CallbackQueryHandler(handle_answer,           pattern=r"^ans\|"))
    app.add_handler(CallbackQueryHandler(handle_tod,              pattern=r"^(truth|dare)\|"))
    app.add_handler(CallbackQueryHandler(handle_tod_done,         pattern=r"^tod_done$"))
    app.add_handler(CallbackQueryHandler(handle_situationship_cb, pattern=r"^sit_"))

    print("🤖 Bot is running! All games active.")
    app.run_polling()

if __name__ == "__main__":
    main()
