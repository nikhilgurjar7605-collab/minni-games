import os
import json
import random
import asyncio
import logging
import datetime
from openai import AsyncOpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    MessageHandler, 
    filters
)

# ─── LOGGING SYSTEM ──────────────────────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── CONFIGURATION & CREDENTIALS ──────────────────────────────────────────────
# Replace these with your actual keys from BotFather and OpenAI
BOT_TOKEN   = "8380616064:AAGCdwaWNRDxa0tThc8JMprWJfWhtQ5bl-4"
OPENAI_KEY  = "sk-5678efgh5678efgh5678efgh5678efgh5678efgh"
SCORES_FILE = "scores.json"

# Initialize OpenAI Async Client
client = AsyncOpenAI(api_key=OPENAI_KEY)

# Global In-Memory States
ACTIVE_QUESTIONS = {}  # chat_id -> quiz data
SITUATIONSHIP    = {}  # chat_id -> roleplay data
USER_COOLDOWNS   = {}  # user_id -> last_command_time

# ─── MASSIVE QUESTION BANK (Expanded for Length & Variety) ────────────────────
QUESTIONS = [
    {"q": "What is the capital of France?", "options": ["Berlin","Madrid","Paris","Rome"], "answer": "Paris"},
    {"q": "Which planet is closest to the Sun?", "options": ["Venus","Earth","Mercury","Mars"], "answer": "Mercury"},
    {"q": "How many sides does a hexagon have?", "options": ["5","6","7","8"], "answer": "6"},
    {"q": "Who wrote 'Romeo and Juliet'?", "options": ["Dickens","Shakespeare","Austen","Twain"], "answer": "Shakespeare"},
    {"q": "What is 12 × 12?", "options": ["132","144","124","148"], "answer": "144"},
    {"q": "Which ocean is the largest?", "options": ["Atlantic","Indian","Arctic","Pacific"], "answer": "Pacific"},
    {"q": "What gas do plants absorb?", "options": ["Oxygen","Nitrogen","CO2","Hydrogen"], "answer": "CO2"},
    {"q": "How many continents are there?", "options": ["5","6","7","8"], "answer": "7"},
    {"q": "What is the fastest land animal?", "options": ["Lion","Cheetah","Horse","Leopard"], "answer": "Cheetah"},
    {"q": "Which element has symbol 'Au'?", "options": ["Silver","Copper","Gold","Aluminium"], "answer": "Gold"},
    {"q": "How many bones in adult human body?", "options": ["196","206","216","226"], "answer": "206"},
    {"q": "What year did World War II end?", "options": ["1943","1944","1945","1946"], "answer": "1945"},
    {"q": "What is the square root of 144?", "options": ["11","12","13","14"], "answer": "12"},
    {"q": "Which country invented pizza?", "options": ["USA","France","Italy","Spain"], "answer": "Italy"},
    {"q": "How many days in a leap year?", "options": ["364","365","366","367"], "answer": "366"},
    {"q": "Who painted the Mona Lisa?", "options": ["Van Gogh","Da Vinci","Picasso","Dalí"], "answer": "Da Vinci"},
    {"q": "What is the largest desert on Earth?", "options": ["Sahara","Gobi","Antarctica","Kalahari"], "answer": "Antarctica"},
    {"q": "Which planet is known as the Red Planet?", "options": ["Jupiter","Saturn","Mars","Venus"], "answer": "Mars"},
    {"q": "What is the chemical symbol for Water?", "options": ["H2O","CO2","O2","NaCl"], "answer": "H2O"},
    {"q": "How many colors are in a rainbow?", "options": ["6","7","8","9"], "answer": "7"},
    {"q": "Which is the smallest country?", "options": ["Monaco","Vatican City","Malta","San Marino"], "answer": "Vatican City"},
    {"q": "What is the tallest mountain?", "options": ["K2","Everest","Makalu","Lhotse"], "answer": "Everest"},
    {"q": "Which animal is known as the King of the Jungle?", "options": ["Tiger","Lion","Elephant","Gorilla"], "answer": "Lion"},
    {"q": "What is the primary language of Brazil?", "options": ["Spanish","English","Portuguese","French"], "answer": "Portuguese"},
    {"q": "How many players are on a soccer team?", "options": ["10","11","12","9"], "answer": "11"},
    {"q": "Which is the longest river?", "options": ["Amazon","Nile","Yangtze","Mississippi"], "answer": "Nile"},
    {"q": "What is the hardest natural substance?", "options": ["Gold","Iron","Diamond","Quartz"], "answer": "Diamond"},
    {"q": "Who discovered gravity?", "options": ["Einstein","Newton","Galileo","Tesla"], "answer": "Newton"},
    {"q": "What is the currency of Japan?", "options": ["Yuan","Won","Yen","Ringgit"], "answer": "Yen"},
    {"q": "Which gas do humans breathe out?", "options": ["Oxygen","Nitrogen","CO2","Methane"], "answer": "CO2"},
    {"q": "What is the capital of Italy?", "options": ["Milan","Naples","Venice","Rome"], "answer": "Rome"},
    {"q": "Which organ pumps blood?", "options": ["Lungs","Brain","Heart","Liver"], "answer": "Heart"},
    {"q": "How many years in a century?", "options": ["10","50","100","1000"], "answer": "100"},
    {"q": "What is the freezing point of water?", "options": ["0°C","10°C","32°C","-1°C"], "answer": "0°C"},
    {"q": "Who was the first man on the moon?", "options": ["Buzz Aldrin","Neil Armstrong","Yuri Gagarin","Elon Musk"], "answer": "Neil Armstrong"},
    {"q": "Which country is the largest by area?", "options": ["USA","China","Russia","Canada"], "answer": "Russia"},
    {"q": "What is the capital of Japan?", "options": ["Kyoto","Osaka","Hiroshima","Tokyo"], "answer": "Tokyo"},
    {"q": "How many eyes does a spider have?", "options": ["2","4","6","8"], "answer": "8"},
    {"q": "Which fruit is known for having its seeds on the outside?", "options": ["Apple","Banana","Strawberry","Grape"], "answer": "Strawberry"},
    {"q": "What is the largest mammal?", "options": ["Elephant","Blue Whale","Giraffe","Orca"], "answer": "Blue Whale"},
    {"q": "Which planet has a ring?", "options": ["Mars","Jupiter","Saturn","Neptune"], "answer": "Saturn"},
    {"q": "What is the capital of Australia?", "options": ["Sydney","Melbourne","Canberra","Perth"], "answer": "Canberra"},
    {"q": "Who wrote 'Harry Potter'?", "options": ["Tolkien","Rowling","Lewis","Martin"], "answer": "Rowling"},
    {"q": "What is the boiling point of water?", "options": ["50°C","100°C","150°C","200°C"], "answer": "100°C"},
    {"q": "How many legs does a butterfly have?", "options": ["4","6","8","10"], "answer": "6"},
    {"q": "Which is the smallest continent?", "options": ["Europe","Africa","Australia","Antarctica"], "answer": "Australia"},
    {"q": "What is the most spoken language?", "options": ["English","Spanish","Mandarin","Hindi"], "answer": "Mandarin"},
    {"q": "Which vitamin comes from sunlight?", "options": ["Vit A","Vit B","Vit C","Vit D"], "answer": "Vit D"},
    {"q": "How many players in a basketball team?", "options": ["5","6","7","11"], "answer": "5"},
    {"q": "What is the capital of Germany?", "options": ["Munich","Frankfurt","Hamburg","Berlin"], "answer": "Berlin"},
    {"q": "Which metal is liquid at room temp?", "options": ["Iron","Mercury","Lead","Zinc"], "answer": "Mercury"},
    {"q": "What is the main ingredient in chocolate?", "options": ["Sugar","Milk","Cocoa","Vanilla"], "answer": "Cocoa"},
    {"q": "How many days in a year?", "options": ["360","364","365","366"], "answer": "365"},
    {"q": "Which is the nearest star?", "options": ["Sirius","Alpha Centauri","The Sun","Vega"], "answer": "The Sun"},
    {"q": "Who is known as the Iron Man of India?", "options": ["Nehru","Gandhi","Patel","Ambedkar"], "answer": "Patel"},
    {"q": "What is the square root of 64?", "options": ["6","7","8","9"], "answer": "8"},
    {"q": "Which country is famous for the Eiffel Tower?", "options": ["Germany","Italy","France","UK"], "answer": "France"},
    {"q": "What is the center of an atom called?", "options": ["Electron","Proton","Neutron","Nucleus"], "answer": "Nucleus"},
    {"q": "Which ocean is between USA and UK?", "options": ["Pacific","Atlantic","Indian","Arctic"], "answer": "Atlantic"},
    {"q": "How many strings on a standard guitar?", "options": ["4","5","6","7"], "answer": "6"},
    {"q": "What is the national animal of India?", "options": ["Lion","Tiger","Elephant","Peacock"], "answer": "Tiger"},
    {"q": "Which gas is used in balloons?", "options": ["Oxygen","Helium","Nitrogen","CO2"], "answer": "Helium"},
    {"q": "What is the capital of Canada?", "options": ["Toronto","Vancouver","Ottawa","Montreal"], "answer": "Ottawa"},
    {"q": "Who invented the light bulb?", "options": ["Tesla","Edison","Graham Bell","Newton"], "answer": "Edison"},
    {"q": "How many hours in a day?", "options": ["12","24","48","60"], "answer": "24"},
    {"q": "Which is the largest bird?", "options": ["Eagle","Ostrich","Penguin","Albatross"], "answer": "Ostrich"},
    {"q": "What is the capital of Spain?", "options": ["Barcelona","Seville","Madrid","Valencia"], "answer": "Madrid"},
    {"q": "Which element is needed for breathing?", "options": ["Nitrogen","Oxygen","Hydrogen","Carbon"], "answer": "Oxygen"},
    {"q": "How many colors in the Indian flag?", "options": ["2","3","4","5"], "answer": "3"},
    {"q": "Which is the tallest animal?", "options": ["Elephant","Giraffe","Ostrich","Camel"], "answer": "Giraffe"},
    {"q": "What is the capital of Russia?", "options": ["Saint Petersburg","Moscow","Kiev","Sochi"], "answer": "Moscow"},
    {"q": "Who is the god of Cricket?", "options": ["Dhoni","Kohli","Tendulkar","Ponting"], "answer": "Tendulkar"},
    {"q": "What is the chemical symbol for Gold?", "options": ["Ag","Fe","Au","Pb"], "answer": "Au"}
]

SITUATION_VIBES = [
    "awkward first date 🍝", "late night texting 🌙", "situationship 💔",
    "friends to lovers 😶", "road trip romance 🚗", "rivals who secret like each other ⚔️❤️",
    "childhood friends 🥺", "barista and regular ☕", "fake dating 💘", "enemies to lovers 📚"
]

# ─── DATABASE & PERSISTENCE ───────────────────────────────────────────────────
def init_db():
    if not os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "w") as f:
            json.dump({}, f)
        logger.info("Created new database file.")

def load_scores():
    try:
        with open(SCORES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_scores(data):
    with open(SCORES_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_user_stats(user_id, username, is_correct):
    db = load_scores()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"name": username, "score": 0, "correct": 0, "wrong": 0, "xp": 0, "level": 1}
    
    db[uid]["name"] = username
    if is_correct:
        db[uid]["score"] += 1
        db[uid]["correct"] += 1
        db[uid]["xp"] += 20
    else:
        db[uid]["wrong"] += 1
        db[uid]["xp"] += 5
    
    # Simple Leveling System
    new_level = (db[uid]["xp"] // 100) + 1
    if new_level > db[uid]["level"]:
        db[uid]["level"] = new_level
        
    save_scores(db)
    return db[uid]

# ─── AI ENGINE ────────────────────────────────────────────────────────────────
async def ask_gpt(system_prompt: str, user_msg: str, max_tokens: int = 350) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "⚠️ The AI is currently unavailable. Please try again later!"

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"🌟 *Hello {user.first_name}!* 🌟\n\n"
        "Welcome to the most complete Telegram Bot Script.\n\n"
        "🎮 /play — Quiz Time\n"
        "🏆 /leaderboard — Global Ranks\n"
        "📊 /mystats — My Performance\n"
        "😈 /tod — Truth or Dare\n"
        "💘 /situationship — Romantic Roleplay\n"
        "🔮 /mytype — AI Vibe Analysis"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def play(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in ACTIVE_QUESTIONS:
        await update.message.reply_text("⚠️ Answer the current question first!")
        return

    q_data = random.choice(QUESTIONS)
    opts = list(q_data["options"])
    random.shuffle(opts)

    ACTIVE_QUESTIONS[chat_id] = {"answer": q_data["answer"], "question": q_data["q"]}
    keyboard = [[InlineKeyboardButton(o, callback_data=f"ans|{o}")] for o in opts]
    
    sent = await update.message.reply_text(
        f"❓ *QUESTION:*\n\n{q_data['q']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    ACTIVE_QUESTIONS[chat_id]["msg_id"] = sent.message_id
    asyncio.create_task(timer(ctx, chat_id, sent.message_id))

async def timer(ctx, chat_id, msg_id):
    await asyncio.sleep(30)
    if chat_id in ACTIVE_QUESTIONS and ACTIVE_QUESTIONS[chat_id]["msg_id"] == msg_id:
        ans = ACTIVE_QUESTIONS[chat_id]["answer"]
        del ACTIVE_QUESTIONS[chat_id]
        try:
            await ctx.bot.edit_message_text(chat_id, msg_id, text=f"⏰ *TIME'S UP!*\nAnswer: *{ans}*", parse_mode="Markdown")
        except: pass

async def handle_quiz_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    user = query.from_user
    
    if chat_id not in ACTIVE_QUESTIONS:
        await query.answer("❌ Expired!", show_alert=True)
        return

    choice = query.data.split("|")[1]
    correct = ACTIVE_QUESTIONS[chat_id]["answer"]
    
    if choice == correct:
        stats = update_user_stats(user.id, user.first_name, True)
        await query.answer("✅ Correct!", show_alert=True)
        await query.edit_message_text(f"🎉 *CORRECT!*\nAnswer: *{correct}*\n🏅 Level: {stats['level']}", parse_mode="Markdown")
    else:
        update_user_stats(user.id, user.first_name, False)
        await query.answer("❌ Wrong!", show_alert=True)
        await query.edit_message_text(f"😔 *WRONG!*\nCorrect answer: *{correct}*", parse_mode="Markdown")
    
    del ACTIVE_QUESTIONS[chat_id]

async def leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    db = load_scores()
    if not db:
        await update.message.reply_text("🏆 No one has played yet!")
        return
    sorted_u = sorted(db.items(), key=lambda x: x[1]["score"], reverse=True)[:10]
    txt = "🏆 *TOP 10 PLAYERS*\n\n"
    for i, (uid, s) in enumerate(sorted_u):
        txt += f"{i+1}. *{s['name']}* — Lvl {s['level']} | {s['score']} pts\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def tod_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    choice = random.choice(["truth", "dare"])
    keyboard = [[InlineKeyboardButton(f"🔥 {l}", callback_data=f"tod|{choice}|{l.lower()}")] for l in ["Mild", "Medium", "Spicy", "Savage"]]
    await update.message.reply_text(f"🎲 Wheel: *{choice.upper()}*\nSelect level:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_tod_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer("Generating...")
    _, t_type, lvl = query.data.split("|")
    res = await ask_gpt(f"Party host. One {t_type} challenge. Level: {lvl}. Short.", f"For {query.from_user.first_name}")
    await query.edit_message_text(f"✨ *{t_type.upper()} ({lvl})*\n\n_{res}_", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Done!", callback_data="tod_done")]]), parse_mode="Markdown")

async def situationship(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; user = update.effective_user; vibe = random.choice(SITUATION_VIBES)
    res = await ask_gpt("Romance writer. 3 sentences. Cliffhanger.", f"Vibe: {vibe} for {user.first_name}")
    SITUATIONSHIP[chat_id] = {"user_id": str(user.id), "history": [res], "vibe": vibe}
    btns = [[InlineKeyboardButton("💬 Continue", callback_data="sit_continue")], [InlineKeyboardButton("🔀 New Story", callback_data="sit_new")]]
    await update.message.reply_text(f"💘 *SITUATIONSHIP: {vibe.upper()}*\n\n{res}", reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

async def handle_sit_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; chat_id = query.message.chat_id
    if query.data == "sit_continue":
        state = SITUATIONSHIP.get(chat_id)
        if not state: return
        res = await ask_gpt("Continue story. 2 sentences. Cliffhanger.", f"Last: {state['history'][-1]}")
        state["history"].append(res)
        await query.edit_message_text(f"💘 *STORY...*\n\n{res}", reply_markup=query.message.reply_markup, parse_mode="Markdown")
    elif query.data == "sit_new": await situationship(update, ctx)

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("tod", tod_menu))
    app.add_handler(CommandHandler("situationship", situationship))
    app.add_handler(CommandHandler("mystats", lambda u, c: u.message.reply_text("Use /play to see stats!")))

    # THE FIX: Using raw strings (r"") prevents the "invalid escape sequence" error on Render
    app.add_handler(CallbackQueryHandler(handle_quiz_callback, pattern=r"^ans\|"))
    app.add_handler(CallbackQueryHandler(handle_tod_callback, pattern=r"^tod\|"))
    app.add_handler(CallbackQueryHandler(handle_sit_callback, pattern=r"^sit_"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.edit_message_text("✅ Task Finished!"), pattern="^tod_done$"))

    print("🚀 DEPLOYED SUCCESSFULLY ON RENDER")
    app.run_polling()

if __name__ == "__main__":
    main()import os
import json
import random
import asyncio
import logging
import datetime
from openai import AsyncOpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    MessageHandler, 
    filters
)

# ─── LOGGING SYSTEM ──────────────────────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── CONFIGURATION & CREDENTIALS ──────────────────────────────────────────────
# Replace these with your actual keys from BotFather and OpenAI
BOT_TOKEN   = "8380616064:AAGCdwaWNRDxa0tThc8JMprWJfWhtQ5bl-4"
OPENAI_KEY  = "sk-5678efgh5678efgh5678efgh5678efgh5678efgh"
SCORES_FILE = "scores.json"

# Initialize OpenAI Async Client
client = AsyncOpenAI(api_key=OPENAI_KEY)

# Global In-Memory States
ACTIVE_QUESTIONS = {}  # chat_id -> quiz data
SITUATIONSHIP    = {}  # chat_id -> roleplay data
USER_COOLDOWNS   = {}  # user_id -> last_command_time

# ─── MASSIVE QUESTION BANK (Expanded for Length & Variety) ────────────────────
QUESTIONS = [
    {"q": "What is the capital of France?", "options": ["Berlin","Madrid","Paris","Rome"], "answer": "Paris"},
    {"q": "Which planet is closest to the Sun?", "options": ["Venus","Earth","Mercury","Mars"], "answer": "Mercury"},
    {"q": "How many sides does a hexagon have?", "options": ["5","6","7","8"], "answer": "6"},
    {"q": "Who wrote 'Romeo and Juliet'?", "options": ["Dickens","Shakespeare","Austen","Twain"], "answer": "Shakespeare"},
    {"q": "What is 12 × 12?", "options": ["132","144","124","148"], "answer": "144"},
    {"q": "Which ocean is the largest?", "options": ["Atlantic","Indian","Arctic","Pacific"], "answer": "Pacific"},
    {"q": "What gas do plants absorb?", "options": ["Oxygen","Nitrogen","CO2","Hydrogen"], "answer": "CO2"},
    {"q": "How many continents are there?", "options": ["5","6","7","8"], "answer": "7"},
    {"q": "What is the fastest land animal?", "options": ["Lion","Cheetah","Horse","Leopard"], "answer": "Cheetah"},
    {"q": "Which element has symbol 'Au'?", "options": ["Silver","Copper","Gold","Aluminium"], "answer": "Gold"},
    {"q": "How many bones in adult human body?", "options": ["196","206","216","226"], "answer": "206"},
    {"q": "What year did World War II end?", "options": ["1943","1944","1945","1946"], "answer": "1945"},
    {"q": "What is the square root of 144?", "options": ["11","12","13","14"], "answer": "12"},
    {"q": "Which country invented pizza?", "options": ["USA","France","Italy","Spain"], "answer": "Italy"},
    {"q": "How many days in a leap year?", "options": ["364","365","366","367"], "answer": "366"},
    {"q": "Who painted the Mona Lisa?", "options": ["Van Gogh","Da Vinci","Picasso","Dalí"], "answer": "Da Vinci"},
    {"q": "What is the largest desert on Earth?", "options": ["Sahara","Gobi","Antarctica","Kalahari"], "answer": "Antarctica"},
    {"q": "Which planet is known as the Red Planet?", "options": ["Jupiter","Saturn","Mars","Venus"], "answer": "Mars"},
    {"q": "What is the chemical symbol for Water?", "options": ["H2O","CO2","O2","NaCl"], "answer": "H2O"},
    {"q": "How many colors are in a rainbow?", "options": ["6","7","8","9"], "answer": "7"},
    {"q": "Which is the smallest country?", "options": ["Monaco","Vatican City","Malta","San Marino"], "answer": "Vatican City"},
    {"q": "What is the tallest mountain?", "options": ["K2","Everest","Makalu","Lhotse"], "answer": "Everest"},
    {"q": "Which animal is known as the King of the Jungle?", "options": ["Tiger","Lion","Elephant","Gorilla"], "answer": "Lion"},
    {"q": "What is the primary language of Brazil?", "options": ["Spanish","English","Portuguese","French"], "answer": "Portuguese"},
    {"q": "How many players are on a soccer team?", "options": ["10","11","12","9"], "answer": "11"},
    {"q": "Which is the longest river?", "options": ["Amazon","Nile","Yangtze","Mississippi"], "answer": "Nile"},
    {"q": "What is the hardest natural substance?", "options": ["Gold","Iron","Diamond","Quartz"], "answer": "Diamond"},
    {"q": "Who discovered gravity?", "options": ["Einstein","Newton","Galileo","Tesla"], "answer": "Newton"},
    {"q": "What is the currency of Japan?", "options": ["Yuan","Won","Yen","Ringgit"], "answer": "Yen"},
    {"q": "Which gas do humans breathe out?", "options": ["Oxygen","Nitrogen","CO2","Methane"], "answer": "CO2"},
    {"q": "What is the capital of Italy?", "options": ["Milan","Naples","Venice","Rome"], "answer": "Rome"},
    {"q": "Which organ pumps blood?", "options": ["Lungs","Brain","Heart","Liver"], "answer": "Heart"},
    {"q": "How many years in a century?", "options": ["10","50","100","1000"], "answer": "100"},
    {"q": "What is the freezing point of water?", "options": ["0°C","10°C","32°C","-1°C"], "answer": "0°C"},
    {"q": "Who was the first man on the moon?", "options": ["Buzz Aldrin","Neil Armstrong","Yuri Gagarin","Elon Musk"], "answer": "Neil Armstrong"},
    {"q": "Which country is the largest by area?", "options": ["USA","China","Russia","Canada"], "answer": "Russia"},
    {"q": "What is the capital of Japan?", "options": ["Kyoto","Osaka","Hiroshima","Tokyo"], "answer": "Tokyo"},
    {"q": "How many eyes does a spider have?", "options": ["2","4","6","8"], "answer": "8"},
    {"q": "Which fruit is known for having its seeds on the outside?", "options": ["Apple","Banana","Strawberry","Grape"], "answer": "Strawberry"},
    {"q": "What is the largest mammal?", "options": ["Elephant","Blue Whale","Giraffe","Orca"], "answer": "Blue Whale"},
    {"q": "Which planet has a ring?", "options": ["Mars","Jupiter","Saturn","Neptune"], "answer": "Saturn"},
    {"q": "What is the capital of Australia?", "options": ["Sydney","Melbourne","Canberra","Perth"], "answer": "Canberra"},
    {"q": "Who wrote 'Harry Potter'?", "options": ["Tolkien","Rowling","Lewis","Martin"], "answer": "Rowling"},
    {"q": "What is the boiling point of water?", "options": ["50°C","100°C","150°C","200°C"], "answer": "100°C"},
    {"q": "How many legs does a butterfly have?", "options": ["4","6","8","10"], "answer": "6"},
    {"q": "Which is the smallest continent?", "options": ["Europe","Africa","Australia","Antarctica"], "answer": "Australia"},
    {"q": "What is the most spoken language?", "options": ["English","Spanish","Mandarin","Hindi"], "answer": "Mandarin"},
    {"q": "Which vitamin comes from sunlight?", "options": ["Vit A","Vit B","Vit C","Vit D"], "answer": "Vit D"},
    {"q": "How many players in a basketball team?", "options": ["5","6","7","11"], "answer": "5"},
    {"q": "What is the capital of Germany?", "options": ["Munich","Frankfurt","Hamburg","Berlin"], "answer": "Berlin"},
    {"q": "Which metal is liquid at room temp?", "options": ["Iron","Mercury","Lead","Zinc"], "answer": "Mercury"},
    {"q": "What is the main ingredient in chocolate?", "options": ["Sugar","Milk","Cocoa","Vanilla"], "answer": "Cocoa"},
    {"q": "How many days in a year?", "options": ["360","364","365","366"], "answer": "365"},
    {"q": "Which is the nearest star?", "options": ["Sirius","Alpha Centauri","The Sun","Vega"], "answer": "The Sun"},
    {"q": "Who is known as the Iron Man of India?", "options": ["Nehru","Gandhi","Patel","Ambedkar"], "answer": "Patel"},
    {"q": "What is the square root of 64?", "options": ["6","7","8","9"], "answer": "8"},
    {"q": "Which country is famous for the Eiffel Tower?", "options": ["Germany","Italy","France","UK"], "answer": "France"},
    {"q": "What is the center of an atom called?", "options": ["Electron","Proton","Neutron","Nucleus"], "answer": "Nucleus"},
    {"q": "Which ocean is between USA and UK?", "options": ["Pacific","Atlantic","Indian","Arctic"], "answer": "Atlantic"},
    {"q": "How many strings on a standard guitar?", "options": ["4","5","6","7"], "answer": "6"},
    {"q": "What is the national animal of India?", "options": ["Lion","Tiger","Elephant","Peacock"], "answer": "Tiger"},
    {"q": "Which gas is used in balloons?", "options": ["Oxygen","Helium","Nitrogen","CO2"], "answer": "Helium"},
    {"q": "What is the capital of Canada?", "options": ["Toronto","Vancouver","Ottawa","Montreal"], "answer": "Ottawa"},
    {"q": "Who invented the light bulb?", "options": ["Tesla","Edison","Graham Bell","Newton"], "answer": "Edison"},
    {"q": "How many hours in a day?", "options": ["12","24","48","60"], "answer": "24"},
    {"q": "Which is the largest bird?", "options": ["Eagle","Ostrich","Penguin","Albatross"], "answer": "Ostrich"},
    {"q": "What is the capital of Spain?", "options": ["Barcelona","Seville","Madrid","Valencia"], "answer": "Madrid"},
    {"q": "Which element is needed for breathing?", "options": ["Nitrogen","Oxygen","Hydrogen","Carbon"], "answer": "Oxygen"},
    {"q": "How many colors in the Indian flag?", "options": ["2","3","4","5"], "answer": "3"},
    {"q": "Which is the tallest animal?", "options": ["Elephant","Giraffe","Ostrich","Camel"], "answer": "Giraffe"},
    {"q": "What is the capital of Russia?", "options": ["Saint Petersburg","Moscow","Kiev","Sochi"], "answer": "Moscow"},
    {"q": "Who is the god of Cricket?", "options": ["Dhoni","Kohli","Tendulkar","Ponting"], "answer": "Tendulkar"},
    {"q": "What is the chemical symbol for Gold?", "options": ["Ag","Fe","Au","Pb"], "answer": "Au"}
]

SITUATION_VIBES = [
    "awkward first date 🍝", "late night texting 🌙", "situationship 💔",
    "friends to lovers 😶", "road trip romance 🚗", "rivals who secret like each other ⚔️❤️",
    "childhood friends 🥺", "barista and regular ☕", "fake dating 💘", "enemies to lovers 📚"
]

# ─── DATABASE & PERSISTENCE ───────────────────────────────────────────────────
def init_db():
    if not os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "w") as f:
            json.dump({}, f)
        logger.info("Created new database file.")

def load_scores():
    try:
        with open(SCORES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_scores(data):
    with open(SCORES_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_user_stats(user_id, username, is_correct):
    db = load_scores()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"name": username, "score": 0, "correct": 0, "wrong": 0, "xp": 0, "level": 1}
    
    db[uid]["name"] = username
    if is_correct:
        db[uid]["score"] += 1
        db[uid]["correct"] += 1
        db[uid]["xp"] += 20
    else:
        db[uid]["wrong"] += 1
        db[uid]["xp"] += 5
    
    # Simple Leveling System
    new_level = (db[uid]["xp"] // 100) + 1
    if new_level > db[uid]["level"]:
        db[uid]["level"] = new_level
        
    save_scores(db)
    return db[uid]

# ─── AI ENGINE ────────────────────────────────────────────────────────────────
async def ask_gpt(system_prompt: str, user_msg: str, max_tokens: int = 350) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "⚠️ The AI is currently unavailable. Please try again later!"

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"🌟 *Hello {user.first_name}!* 🌟\n\n"
        "Welcome to the most complete Telegram Bot Script.\n\n"
        "🎮 /play — Quiz Time\n"
        "🏆 /leaderboard — Global Ranks\n"
        "📊 /mystats — My Performance\n"
        "😈 /tod — Truth or Dare\n"
        "💘 /situationship — Romantic Roleplay\n"
        "🔮 /mytype — AI Vibe Analysis"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def play(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in ACTIVE_QUESTIONS:
        await update.message.reply_text("⚠️ Answer the current question first!")
        return

    q_data = random.choice(QUESTIONS)
    opts = list(q_data["options"])
    random.shuffle(opts)

    ACTIVE_QUESTIONS[chat_id] = {"answer": q_data["answer"], "question": q_data["q"]}
    keyboard = [[InlineKeyboardButton(o, callback_data=f"ans|{o}")] for o in opts]
    
    sent = await update.message.reply_text(
        f"❓ *QUESTION:*\n\n{q_data['q']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    ACTIVE_QUESTIONS[chat_id]["msg_id"] = sent.message_id
    asyncio.create_task(timer(ctx, chat_id, sent.message_id))

async def timer(ctx, chat_id, msg_id):
    await asyncio.sleep(30)
    if chat_id in ACTIVE_QUESTIONS and ACTIVE_QUESTIONS[chat_id]["msg_id"] == msg_id:
        ans = ACTIVE_QUESTIONS[chat_id]["answer"]
        del ACTIVE_QUESTIONS[chat_id]
        try:
            await ctx.bot.edit_message_text(chat_id, msg_id, text=f"⏰ *TIME'S UP!*\nAnswer: *{ans}*", parse_mode="Markdown")
        except: pass

async def handle_quiz_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    user = query.from_user
    
    if chat_id not in ACTIVE_QUESTIONS:
        await query.answer("❌ Expired!", show_alert=True)
        return

    choice = query.data.split("|")[1]
    correct = ACTIVE_QUESTIONS[chat_id]["answer"]
    
    if choice == correct:
        stats = update_user_stats(user.id, user.first_name, True)
        await query.answer("✅ Correct!", show_alert=True)
        await query.edit_message_text(f"🎉 *CORRECT!*\nAnswer: *{correct}*\n🏅 Level: {stats['level']}", parse_mode="Markdown")
    else:
        update_user_stats(user.id, user.first_name, False)
        await query.answer("❌ Wrong!", show_alert=True)
        await query.edit_message_text(f"😔 *WRONG!*\nCorrect answer: *{correct}*", parse_mode="Markdown")
    
    del ACTIVE_QUESTIONS[chat_id]

async def leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    db = load_scores()
    if not db:
        await update.message.reply_text("🏆 No one has played yet!")
        return
    sorted_u = sorted(db.items(), key=lambda x: x[1]["score"], reverse=True)[:10]
    txt = "🏆 *TOP 10 PLAYERS*\n\n"
    for i, (uid, s) in enumerate(sorted_u):
        txt += f"{i+1}. *{s['name']}* — Lvl {s['level']} | {s['score']} pts\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def tod_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    choice = random.choice(["truth", "dare"])
    keyboard = [[InlineKeyboardButton(f"🔥 {l}", callback_data=f"tod|{choice}|{l.lower()}")] for l in ["Mild", "Medium", "Spicy", "Savage"]]
    await update.message.reply_text(f"🎲 Wheel: *{choice.upper()}*\nSelect level:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_tod_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer("Generating...")
    _, t_type, lvl = query.data.split("|")
    res = await ask_gpt(f"Party host. One {t_type} challenge. Level: {lvl}. Short.", f"For {query.from_user.first_name}")
    await query.edit_message_text(f"✨ *{t_type.upper()} ({lvl})*\n\n_{res}_", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Done!", callback_data="tod_done")]]), parse_mode="Markdown")

async def situationship(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; user = update.effective_user; vibe = random.choice(SITUATION_VIBES)
    res = await ask_gpt("Romance writer. 3 sentences. Cliffhanger.", f"Vibe: {vibe} for {user.first_name}")
    SITUATIONSHIP[chat_id] = {"user_id": str(user.id), "history": [res], "vibe": vibe}
    btns = [[InlineKeyboardButton("💬 Continue", callback_data="sit_continue")], [InlineKeyboardButton("🔀 New Story", callback_data="sit_new")]]
    await update.message.reply_text(f"💘 *SITUATIONSHIP: {vibe.upper()}*\n\n{res}", reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

async def handle_sit_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; chat_id = query.message.chat_id
    if query.data == "sit_continue":
        state = SITUATIONSHIP.get(chat_id)
        if not state: return
        res = await ask_gpt("Continue story. 2 sentences. Cliffhanger.", f"Last: {state['history'][-1]}")
        state["history"].append(res)
        await query.edit_message_text(f"💘 *STORY...*\n\n{res}", reply_markup=query.message.reply_markup, parse_mode="Markdown")
    elif query.data == "sit_new": await situationship(update, ctx)

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("tod", tod_menu))
    app.add_handler(CommandHandler("situationship", situationship))
    app.add_handler(CommandHandler("mystats", lambda u, c: u.message.reply_text("Use /play to see stats!")))

    # THE FIX: Using raw strings (r"") prevents the "invalid escape sequence" error on Render
    app.add_handler(CallbackQueryHandler(handle_quiz_callback, pattern=r"^ans\|"))
    app.add_handler(CallbackQueryHandler(handle_tod_callback, pattern=r"^tod\|"))
    app.add_handler(CallbackQueryHandler(handle_sit_callback, pattern=r"^sit_"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.edit_message_text("✅ Task Finished!"), pattern="^tod_done$"))

    print("🚀 DEPLOYED SUCCESSFULLY ON RENDER")
    app.run_polling()

if __name__ == "__main__":
    main()import os
import json
import random
import asyncio
import logging
import datetime
from openai import AsyncOpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    MessageHandler, 
    filters
)

# ─── LOGGING SYSTEM ──────────────────────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── CONFIGURATION & CREDENTIALS ──────────────────────────────────────────────
# Replace these with your actual keys from BotFather and OpenAI
BOT_TOKEN   = "8380616064:AAGCdwaWNRDxa0tThc8JMprWJfWhtQ5bl-4"
OPENAI_KEY  = "sk-5678efgh5678efgh5678efgh5678efgh5678efgh"
SCORES_FILE = "scores.json"

# Initialize OpenAI Async Client
client = AsyncOpenAI(api_key=OPENAI_KEY)

# Global In-Memory States
ACTIVE_QUESTIONS = {}  # chat_id -> quiz data
SITUATIONSHIP    = {}  # chat_id -> roleplay data
USER_COOLDOWNS   = {}  # user_id -> last_command_time

# ─── MASSIVE QUESTION BANK (Expanded for Length & Variety) ────────────────────
QUESTIONS = [
    {"q": "What is the capital of France?", "options": ["Berlin","Madrid","Paris","Rome"], "answer": "Paris"},
    {"q": "Which planet is closest to the Sun?", "options": ["Venus","Earth","Mercury","Mars"], "answer": "Mercury"},
    {"q": "How many sides does a hexagon have?", "options": ["5","6","7","8"], "answer": "6"},
    {"q": "Who wrote 'Romeo and Juliet'?", "options": ["Dickens","Shakespeare","Austen","Twain"], "answer": "Shakespeare"},
    {"q": "What is 12 × 12?", "options": ["132","144","124","148"], "answer": "144"},
    {"q": "Which ocean is the largest?", "options": ["Atlantic","Indian","Arctic","Pacific"], "answer": "Pacific"},
    {"q": "What gas do plants absorb?", "options": ["Oxygen","Nitrogen","CO2","Hydrogen"], "answer": "CO2"},
    {"q": "How many continents are there?", "options": ["5","6","7","8"], "answer": "7"},
    {"q": "What is the fastest land animal?", "options": ["Lion","Cheetah","Horse","Leopard"], "answer": "Cheetah"},
    {"q": "Which element has symbol 'Au'?", "options": ["Silver","Copper","Gold","Aluminium"], "answer": "Gold"},
    {"q": "How many bones in adult human body?", "options": ["196","206","216","226"], "answer": "206"},
    {"q": "What year did World War II end?", "options": ["1943","1944","1945","1946"], "answer": "1945"},
    {"q": "What is the square root of 144?", "options": ["11","12","13","14"], "answer": "12"},
    {"q": "Which country invented pizza?", "options": ["USA","France","Italy","Spain"], "answer": "Italy"},
    {"q": "How many days in a leap year?", "options": ["364","365","366","367"], "answer": "366"},
    {"q": "Who painted the Mona Lisa?", "options": ["Van Gogh","Da Vinci","Picasso","Dalí"], "answer": "Da Vinci"},
    {"q": "What is the largest desert on Earth?", "options": ["Sahara","Gobi","Antarctica","Kalahari"], "answer": "Antarctica"},
    {"q": "Which planet is known as the Red Planet?", "options": ["Jupiter","Saturn","Mars","Venus"], "answer": "Mars"},
    {"q": "What is the chemical symbol for Water?", "options": ["H2O","CO2","O2","NaCl"], "answer": "H2O"},
    {"q": "How many colors are in a rainbow?", "options": ["6","7","8","9"], "answer": "7"},
    {"q": "Which is the smallest country?", "options": ["Monaco","Vatican City","Malta","San Marino"], "answer": "Vatican City"},
    {"q": "What is the tallest mountain?", "options": ["K2","Everest","Makalu","Lhotse"], "answer": "Everest"},
    {"q": "Which animal is known as the King of the Jungle?", "options": ["Tiger","Lion","Elephant","Gorilla"], "answer": "Lion"},
    {"q": "What is the primary language of Brazil?", "options": ["Spanish","English","Portuguese","French"], "answer": "Portuguese"},
    {"q": "How many players are on a soccer team?", "options": ["10","11","12","9"], "answer": "11"},
    {"q": "Which is the longest river?", "options": ["Amazon","Nile","Yangtze","Mississippi"], "answer": "Nile"},
    {"q": "What is the hardest natural substance?", "options": ["Gold","Iron","Diamond","Quartz"], "answer": "Diamond"},
    {"q": "Who discovered gravity?", "options": ["Einstein","Newton","Galileo","Tesla"], "answer": "Newton"},
    {"q": "What is the currency of Japan?", "options": ["Yuan","Won","Yen","Ringgit"], "answer": "Yen"},
    {"q": "Which gas do humans breathe out?", "options": ["Oxygen","Nitrogen","CO2","Methane"], "answer": "CO2"},
    {"q": "What is the capital of Italy?", "options": ["Milan","Naples","Venice","Rome"], "answer": "Rome"},
    {"q": "Which organ pumps blood?", "options": ["Lungs","Brain","Heart","Liver"], "answer": "Heart"},
    {"q": "How many years in a century?", "options": ["10","50","100","1000"], "answer": "100"},
    {"q": "What is the freezing point of water?", "options": ["0°C","10°C","32°C","-1°C"], "answer": "0°C"},
    {"q": "Who was the first man on the moon?", "options": ["Buzz Aldrin","Neil Armstrong","Yuri Gagarin","Elon Musk"], "answer": "Neil Armstrong"},
    {"q": "Which country is the largest by area?", "options": ["USA","China","Russia","Canada"], "answer": "Russia"},
    {"q": "What is the capital of Japan?", "options": ["Kyoto","Osaka","Hiroshima","Tokyo"], "answer": "Tokyo"},
    {"q": "How many eyes does a spider have?", "options": ["2","4","6","8"], "answer": "8"},
    {"q": "Which fruit is known for having its seeds on the outside?", "options": ["Apple","Banana","Strawberry","Grape"], "answer": "Strawberry"},
    {"q": "What is the largest mammal?", "options": ["Elephant","Blue Whale","Giraffe","Orca"], "answer": "Blue Whale"},
    {"q": "Which planet has a ring?", "options": ["Mars","Jupiter","Saturn","Neptune"], "answer": "Saturn"},
    {"q": "What is the capital of Australia?", "options": ["Sydney","Melbourne","Canberra","Perth"], "answer": "Canberra"},
    {"q": "Who wrote 'Harry Potter'?", "options": ["Tolkien","Rowling","Lewis","Martin"], "answer": "Rowling"},
    {"q": "What is the boiling point of water?", "options": ["50°C","100°C","150°C","200°C"], "answer": "100°C"},
    {"q": "How many legs does a butterfly have?", "options": ["4","6","8","10"], "answer": "6"},
    {"q": "Which is the smallest continent?", "options": ["Europe","Africa","Australia","Antarctica"], "answer": "Australia"},
    {"q": "What is the most spoken language?", "options": ["English","Spanish","Mandarin","Hindi"], "answer": "Mandarin"},
    {"q": "Which vitamin comes from sunlight?", "options": ["Vit A","Vit B","Vit C","Vit D"], "answer": "Vit D"},
    {"q": "How many players in a basketball team?", "options": ["5","6","7","11"], "answer": "5"},
    {"q": "What is the capital of Germany?", "options": ["Munich","Frankfurt","Hamburg","Berlin"], "answer": "Berlin"},
    {"q": "Which metal is liquid at room temp?", "options": ["Iron","Mercury","Lead","Zinc"], "answer": "Mercury"},
    {"q": "What is the main ingredient in chocolate?", "options": ["Sugar","Milk","Cocoa","Vanilla"], "answer": "Cocoa"},
    {"q": "How many days in a year?", "options": ["360","364","365","366"], "answer": "365"},
    {"q": "Which is the nearest star?", "options": ["Sirius","Alpha Centauri","The Sun","Vega"], "answer": "The Sun"},
    {"q": "Who is known as the Iron Man of India?", "options": ["Nehru","Gandhi","Patel","Ambedkar"], "answer": "Patel"},
    {"q": "What is the square root of 64?", "options": ["6","7","8","9"], "answer": "8"},
    {"q": "Which country is famous for the Eiffel Tower?", "options": ["Germany","Italy","France","UK"], "answer": "France"},
    {"q": "What is the center of an atom called?", "options": ["Electron","Proton","Neutron","Nucleus"], "answer": "Nucleus"},
    {"q": "Which ocean is between USA and UK?", "options": ["Pacific","Atlantic","Indian","Arctic"], "answer": "Atlantic"},
    {"q": "How many strings on a standard guitar?", "options": ["4","5","6","7"], "answer": "6"},
    {"q": "What is the national animal of India?", "options": ["Lion","Tiger","Elephant","Peacock"], "answer": "Tiger"},
    {"q": "Which gas is used in balloons?", "options": ["Oxygen","Helium","Nitrogen","CO2"], "answer": "Helium"},
    {"q": "What is the capital of Canada?", "options": ["Toronto","Vancouver","Ottawa","Montreal"], "answer": "Ottawa"},
    {"q": "Who invented the light bulb?", "options": ["Tesla","Edison","Graham Bell","Newton"], "answer": "Edison"},
    {"q": "How many hours in a day?", "options": ["12","24","48","60"], "answer": "24"},
    {"q": "Which is the largest bird?", "options": ["Eagle","Ostrich","Penguin","Albatross"], "answer": "Ostrich"},
    {"q": "What is the capital of Spain?", "options": ["Barcelona","Seville","Madrid","Valencia"], "answer": "Madrid"},
    {"q": "Which element is needed for breathing?", "options": ["Nitrogen","Oxygen","Hydrogen","Carbon"], "answer": "Oxygen"},
    {"q": "How many colors in the Indian flag?", "options": ["2","3","4","5"], "answer": "3"},
    {"q": "Which is the tallest animal?", "options": ["Elephant","Giraffe","Ostrich","Camel"], "answer": "Giraffe"},
    {"q": "What is the capital of Russia?", "options": ["Saint Petersburg","Moscow","Kiev","Sochi"], "answer": "Moscow"},
    {"q": "Who is the god of Cricket?", "options": ["Dhoni","Kohli","Tendulkar","Ponting"], "answer": "Tendulkar"},
    {"q": "What is the chemical symbol for Gold?", "options": ["Ag","Fe","Au","Pb"], "answer": "Au"}
]

SITUATION_VIBES = [
    "awkward first date 🍝", "late night texting 🌙", "situationship 💔",
    "friends to lovers 😶", "road trip romance 🚗", "rivals who secret like each other ⚔️❤️",
    "childhood friends 🥺", "barista and regular ☕", "fake dating 💘", "enemies to lovers 📚"
]

# ─── DATABASE & PERSISTENCE ───────────────────────────────────────────────────
def init_db():
    if not os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "w") as f:
            json.dump({}, f)
        logger.info("Created new database file.")

def load_scores():
    try:
        with open(SCORES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_scores(data):
    with open(SCORES_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_user_stats(user_id, username, is_correct):
    db = load_scores()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"name": username, "score": 0, "correct": 0, "wrong": 0, "xp": 0, "level": 1}
    
    db[uid]["name"] = username
    if is_correct:
        db[uid]["score"] += 1
        db[uid]["correct"] += 1
        db[uid]["xp"] += 20
    else:
        db[uid]["wrong"] += 1
        db[uid]["xp"] += 5
    
    # Simple Leveling System
    new_level = (db[uid]["xp"] // 100) + 1
    if new_level > db[uid]["level"]:
        db[uid]["level"] = new_level
        
    save_scores(db)
    return db[uid]

# ─── AI ENGINE ────────────────────────────────────────────────────────────────
async def ask_gpt(system_prompt: str, user_msg: str, max_tokens: int = 350) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "⚠️ The AI is currently unavailable. Please try again later!"

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"🌟 *Hello {user.first_name}!* 🌟\n\n"
        "Welcome to the most complete Telegram Bot Script.\n\n"
        "🎮 /play — Quiz Time\n"
        "🏆 /leaderboard — Global Ranks\n"
        "📊 /mystats — My Performance\n"
        "😈 /tod — Truth or Dare\n"
        "💘 /situationship — Romantic Roleplay\n"
        "🔮 /mytype — AI Vibe Analysis"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def play(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in ACTIVE_QUESTIONS:
        await update.message.reply_text("⚠️ Answer the current question first!")
        return

    q_data = random.choice(QUESTIONS)
    opts = list(q_data["options"])
    random.shuffle(opts)

    ACTIVE_QUESTIONS[chat_id] = {"answer": q_data["answer"], "question": q_data["q"]}
    keyboard = [[InlineKeyboardButton(o, callback_data=f"ans|{o}")] for o in opts]
    
    sent = await update.message.reply_text(
        f"❓ *QUESTION:*\n\n{q_data['q']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    ACTIVE_QUESTIONS[chat_id]["msg_id"] = sent.message_id
    asyncio.create_task(timer(ctx, chat_id, sent.message_id))

async def timer(ctx, chat_id, msg_id):
    await asyncio.sleep(30)
    if chat_id in ACTIVE_QUESTIONS and ACTIVE_QUESTIONS[chat_id]["msg_id"] == msg_id:
        ans = ACTIVE_QUESTIONS[chat_id]["answer"]
        del ACTIVE_QUESTIONS[chat_id]
        try:
            await ctx.bot.edit_message_text(chat_id, msg_id, text=f"⏰ *TIME'S UP!*\nAnswer: *{ans}*", parse_mode="Markdown")
        except: pass

async def handle_quiz_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    user = query.from_user
    
    if chat_id not in ACTIVE_QUESTIONS:
        await query.answer("❌ Expired!", show_alert=True)
        return

    choice = query.data.split("|")[1]
    correct = ACTIVE_QUESTIONS[chat_id]["answer"]
    
    if choice == correct:
        stats = update_user_stats(user.id, user.first_name, True)
        await query.answer("✅ Correct!", show_alert=True)
        await query.edit_message_text(f"🎉 *CORRECT!*\nAnswer: *{correct}*\n🏅 Level: {stats['level']}", parse_mode="Markdown")
    else:
        update_user_stats(user.id, user.first_name, False)
        await query.answer("❌ Wrong!", show_alert=True)
        await query.edit_message_text(f"😔 *WRONG!*\nCorrect answer: *{correct}*", parse_mode="Markdown")
    
    del ACTIVE_QUESTIONS[chat_id]

async def leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    db = load_scores()
    if not db:
        await update.message.reply_text("🏆 No one has played yet!")
        return
    sorted_u = sorted(db.items(), key=lambda x: x[1]["score"], reverse=True)[:10]
    txt = "🏆 *TOP 10 PLAYERS*\n\n"
    for i, (uid, s) in enumerate(sorted_u):
        txt += f"{i+1}. *{s['name']}* — Lvl {s['level']} | {s['score']} pts\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def tod_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    choice = random.choice(["truth", "dare"])
    keyboard = [[InlineKeyboardButton(f"🔥 {l}", callback_data=f"tod|{choice}|{l.lower()}")] for l in ["Mild", "Medium", "Spicy", "Savage"]]
    await update.message.reply_text(f"🎲 Wheel: *{choice.upper()}*\nSelect level:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_tod_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer("Generating...")
    _, t_type, lvl = query.data.split("|")
    res = await ask_gpt(f"Party host. One {t_type} challenge. Level: {lvl}. Short.", f"For {query.from_user.first_name}")
    await query.edit_message_text(f"✨ *{t_type.upper()} ({lvl})*\n\n_{res}_", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Done!", callback_data="tod_done")]]), parse_mode="Markdown")

async def situationship(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; user = update.effective_user; vibe = random.choice(SITUATION_VIBES)
    res = await ask_gpt("Romance writer. 3 sentences. Cliffhanger.", f"Vibe: {vibe} for {user.first_name}")
    SITUATIONSHIP[chat_id] = {"user_id": str(user.id), "history": [res], "vibe": vibe}
    btns = [[InlineKeyboardButton("💬 Continue", callback_data="sit_continue")], [InlineKeyboardButton("🔀 New Story", callback_data="sit_new")]]
    await update.message.reply_text(f"💘 *SITUATIONSHIP: {vibe.upper()}*\n\n{res}", reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

async def handle_sit_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; chat_id = query.message.chat_id
    if query.data == "sit_continue":
        state = SITUATIONSHIP.get(chat_id)
        if not state: return
        res = await ask_gpt("Continue story. 2 sentences. Cliffhanger.", f"Last: {state['history'][-1]}")
        state["history"].append(res)
        await query.edit_message_text(f"💘 *STORY...*\n\n{res}", reply_markup=query.message.reply_markup, parse_mode="Markdown")
    elif query.data == "sit_new": await situationship(update, ctx)

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("tod", tod_menu))
    app.add_handler(CommandHandler("situationship", situationship))
    app.add_handler(CommandHandler("mystats", lambda u, c: u.message.reply_text("Use /play to see stats!")))

    # THE FIX: Using raw strings (r"") prevents the "invalid escape sequence" error on Render
    app.add_handler(CallbackQueryHandler(handle_quiz_callback, pattern=r"^ans\|"))
    app.add_handler(CallbackQueryHandler(handle_tod_callback, pattern=r"^tod\|"))
    app.add_handler(CallbackQueryHandler(handle_sit_callback, pattern=r"^sit_"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.edit_message_text("✅ Task Finished!"), pattern="^tod_done$"))

    print("🚀 DEPLOYED SUCCESSFULLY ON RENDER")
    app.run_polling()

if __name__ == "__main__":
    main()import os
import json
import random
import asyncio
import logging
import datetime
from openai import AsyncOpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    MessageHandler, 
    filters
)

# ─── LOGGING SYSTEM ──────────────────────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── CONFIGURATION & CREDENTIALS ──────────────────────────────────────────────
# Replace these with your actual keys from BotFather and OpenAI
BOT_TOKEN   = "8380616064:AAGCdwaWNRDxa0tThc8JMprWJfWhtQ5bl-4"
OPENAI_KEY  = "sk-5678efgh5678efgh5678efgh5678efgh5678efgh"
SCORES_FILE = "scores.json"

# Initialize OpenAI Async Client
client = AsyncOpenAI(api_key=OPENAI_KEY)

# Global In-Memory States
ACTIVE_QUESTIONS = {}  # chat_id -> quiz data
SITUATIONSHIP    = {}  # chat_id -> roleplay data
USER_COOLDOWNS   = {}  # user_id -> last_command_time

# ─── MASSIVE QUESTION BANK (Expanded for Length & Variety) ────────────────────
QUESTIONS = [
    {"q": "What is the capital of France?", "options": ["Berlin","Madrid","Paris","Rome"], "answer": "Paris"},
    {"q": "Which planet is closest to the Sun?", "options": ["Venus","Earth","Mercury","Mars"], "answer": "Mercury"},
    {"q": "How many sides does a hexagon have?", "options": ["5","6","7","8"], "answer": "6"},
    {"q": "Who wrote 'Romeo and Juliet'?", "options": ["Dickens","Shakespeare","Austen","Twain"], "answer": "Shakespeare"},
    {"q": "What is 12 × 12?", "options": ["132","144","124","148"], "answer": "144"},
    {"q": "Which ocean is the largest?", "options": ["Atlantic","Indian","Arctic","Pacific"], "answer": "Pacific"},
    {"q": "What gas do plants absorb?", "options": ["Oxygen","Nitrogen","CO2","Hydrogen"], "answer": "CO2"},
    {"q": "How many continents are there?", "options": ["5","6","7","8"], "answer": "7"},
    {"q": "What is the fastest land animal?", "options": ["Lion","Cheetah","Horse","Leopard"], "answer": "Cheetah"},
    {"q": "Which element has symbol 'Au'?", "options": ["Silver","Copper","Gold","Aluminium"], "answer": "Gold"},
    {"q": "How many bones in adult human body?", "options": ["196","206","216","226"], "answer": "206"},
    {"q": "What year did World War II end?", "options": ["1943","1944","1945","1946"], "answer": "1945"},
    {"q": "What is the square root of 144?", "options": ["11","12","13","14"], "answer": "12"},
    {"q": "Which country invented pizza?", "options": ["USA","France","Italy","Spain"], "answer": "Italy"},
    {"q": "How many days in a leap year?", "options": ["364","365","366","367"], "answer": "366"},
    {"q": "Who painted the Mona Lisa?", "options": ["Van Gogh","Da Vinci","Picasso","Dalí"], "answer": "Da Vinci"},
    {"q": "What is the largest desert on Earth?", "options": ["Sahara","Gobi","Antarctica","Kalahari"], "answer": "Antarctica"},
    {"q": "Which planet is known as the Red Planet?", "options": ["Jupiter","Saturn","Mars","Venus"], "answer": "Mars"},
    {"q": "What is the chemical symbol for Water?", "options": ["H2O","CO2","O2","NaCl"], "answer": "H2O"},
    {"q": "How many colors are in a rainbow?", "options": ["6","7","8","9"], "answer": "7"},
    {"q": "Which is the smallest country?", "options": ["Monaco","Vatican City","Malta","San Marino"], "answer": "Vatican City"},
    {"q": "What is the tallest mountain?", "options": ["K2","Everest","Makalu","Lhotse"], "answer": "Everest"},
    {"q": "Which animal is known as the King of the Jungle?", "options": ["Tiger","Lion","Elephant","Gorilla"], "answer": "Lion"},
    {"q": "What is the primary language of Brazil?", "options": ["Spanish","English","Portuguese","French"], "answer": "Portuguese"},
    {"q": "How many players are on a soccer team?", "options": ["10","11","12","9"], "answer": "11"},
    {"q": "Which is the longest river?", "options": ["Amazon","Nile","Yangtze","Mississippi"], "answer": "Nile"},
    {"q": "What is the hardest natural substance?", "options": ["Gold","Iron","Diamond","Quartz"], "answer": "Diamond"},
    {"q": "Who discovered gravity?", "options": ["Einstein","Newton","Galileo","Tesla"], "answer": "Newton"},
    {"q": "What is the currency of Japan?", "options": ["Yuan","Won","Yen","Ringgit"], "answer": "Yen"},
    {"q": "Which gas do humans breathe out?", "options": ["Oxygen","Nitrogen","CO2","Methane"], "answer": "CO2"},
    {"q": "What is the capital of Italy?", "options": ["Milan","Naples","Venice","Rome"], "answer": "Rome"},
    {"q": "Which organ pumps blood?", "options": ["Lungs","Brain","Heart","Liver"], "answer": "Heart"},
    {"q": "How many years in a century?", "options": ["10","50","100","1000"], "answer": "100"},
    {"q": "What is the freezing point of water?", "options": ["0°C","10°C","32°C","-1°C"], "answer": "0°C"},
    {"q": "Who was the first man on the moon?", "options": ["Buzz Aldrin","Neil Armstrong","Yuri Gagarin","Elon Musk"], "answer": "Neil Armstrong"},
    {"q": "Which country is the largest by area?", "options": ["USA","China","Russia","Canada"], "answer": "Russia"},
    {"q": "What is the capital of Japan?", "options": ["Kyoto","Osaka","Hiroshima","Tokyo"], "answer": "Tokyo"},
    {"q": "How many eyes does a spider have?", "options": ["2","4","6","8"], "answer": "8"},
    {"q": "Which fruit is known for having its seeds on the outside?", "options": ["Apple","Banana","Strawberry","Grape"], "answer": "Strawberry"},
    {"q": "What is the largest mammal?", "options": ["Elephant","Blue Whale","Giraffe","Orca"], "answer": "Blue Whale"},
    {"q": "Which planet has a ring?", "options": ["Mars","Jupiter","Saturn","Neptune"], "answer": "Saturn"},
    {"q": "What is the capital of Australia?", "options": ["Sydney","Melbourne","Canberra","Perth"], "answer": "Canberra"},
    {"q": "Who wrote 'Harry Potter'?", "options": ["Tolkien","Rowling","Lewis","Martin"], "answer": "Rowling"},
    {"q": "What is the boiling point of water?", "options": ["50°C","100°C","150°C","200°C"], "answer": "100°C"},
    {"q": "How many legs does a butterfly have?", "options": ["4","6","8","10"], "answer": "6"},
    {"q": "Which is the smallest continent?", "options": ["Europe","Africa","Australia","Antarctica"], "answer": "Australia"},
    {"q": "What is the most spoken language?", "options": ["English","Spanish","Mandarin","Hindi"], "answer": "Mandarin"},
    {"q": "Which vitamin comes from sunlight?", "options": ["Vit A","Vit B","Vit C","Vit D"], "answer": "Vit D"},
    {"q": "How many players in a basketball team?", "options": ["5","6","7","11"], "answer": "5"},
    {"q": "What is the capital of Germany?", "options": ["Munich","Frankfurt","Hamburg","Berlin"], "answer": "Berlin"},
    {"q": "Which metal is liquid at room temp?", "options": ["Iron","Mercury","Lead","Zinc"], "answer": "Mercury"},
    {"q": "What is the main ingredient in chocolate?", "options": ["Sugar","Milk","Cocoa","Vanilla"], "answer": "Cocoa"},
    {"q": "How many days in a year?", "options": ["360","364","365","366"], "answer": "365"},
    {"q": "Which is the nearest star?", "options": ["Sirius","Alpha Centauri","The Sun","Vega"], "answer": "The Sun"},
    {"q": "Who is known as the Iron Man of India?", "options": ["Nehru","Gandhi","Patel","Ambedkar"], "answer": "Patel"},
    {"q": "What is the square root of 64?", "options": ["6","7","8","9"], "answer": "8"},
    {"q": "Which country is famous for the Eiffel Tower?", "options": ["Germany","Italy","France","UK"], "answer": "France"},
    {"q": "What is the center of an atom called?", "options": ["Electron","Proton","Neutron","Nucleus"], "answer": "Nucleus"},
    {"q": "Which ocean is between USA and UK?", "options": ["Pacific","Atlantic","Indian","Arctic"], "answer": "Atlantic"},
    {"q": "How many strings on a standard guitar?", "options": ["4","5","6","7"], "answer": "6"},
    {"q": "What is the national animal of India?", "options": ["Lion","Tiger","Elephant","Peacock"], "answer": "Tiger"},
    {"q": "Which gas is used in balloons?", "options": ["Oxygen","Helium","Nitrogen","CO2"], "answer": "Helium"},
    {"q": "What is the capital of Canada?", "options": ["Toronto","Vancouver","Ottawa","Montreal"], "answer": "Ottawa"},
    {"q": "Who invented the light bulb?", "options": ["Tesla","Edison","Graham Bell","Newton"], "answer": "Edison"},
    {"q": "How many hours in a day?", "options": ["12","24","48","60"], "answer": "24"},
    {"q": "Which is the largest bird?", "options": ["Eagle","Ostrich","Penguin","Albatross"], "answer": "Ostrich"},
    {"q": "What is the capital of Spain?", "options": ["Barcelona","Seville","Madrid","Valencia"], "answer": "Madrid"},
    {"q": "Which element is needed for breathing?", "options": ["Nitrogen","Oxygen","Hydrogen","Carbon"], "answer": "Oxygen"},
    {"q": "How many colors in the Indian flag?", "options": ["2","3","4","5"], "answer": "3"},
    {"q": "Which is the tallest animal?", "options": ["Elephant","Giraffe","Ostrich","Camel"], "answer": "Giraffe"},
    {"q": "What is the capital of Russia?", "options": ["Saint Petersburg","Moscow","Kiev","Sochi"], "answer": "Moscow"},
    {"q": "Who is the god of Cricket?", "options": ["Dhoni","Kohli","Tendulkar","Ponting"], "answer": "Tendulkar"},
    {"q": "What is the chemical symbol for Gold?", "options": ["Ag","Fe","Au","Pb"], "answer": "Au"}
]

SITUATION_VIBES = [
    "awkward first date 🍝", "late night texting 🌙", "situationship 💔",
    "friends to lovers 😶", "road trip romance 🚗", "rivals who secret like each other ⚔️❤️",
    "childhood friends 🥺", "barista and regular ☕", "fake dating 💘", "enemies to lovers 📚"
]

# ─── DATABASE & PERSISTENCE ───────────────────────────────────────────────────
def init_db():
    if not os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "w") as f:
            json.dump({}, f)
        logger.info("Created new database file.")

def load_scores():
    try:
        with open(SCORES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_scores(data):
    with open(SCORES_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_user_stats(user_id, username, is_correct):
    db = load_scores()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"name": username, "score": 0, "correct": 0, "wrong": 0, "xp": 0, "level": 1}
    
    db[uid]["name"] = username
    if is_correct:
        db[uid]["score"] += 1
        db[uid]["correct"] += 1
        db[uid]["xp"] += 20
    else:
        db[uid]["wrong"] += 1
        db[uid]["xp"] += 5
    
    # Simple Leveling System
    new_level = (db[uid]["xp"] // 100) + 1
    if new_level > db[uid]["level"]:
        db[uid]["level"] = new_level
        
    save_scores(db)
    return db[uid]

# ─── AI ENGINE ────────────────────────────────────────────────────────────────
async def ask_gpt(system_prompt: str, user_msg: str, max_tokens: int = 350) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return "⚠️ The AI is currently unavailable. Please try again later!"

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"🌟 *Hello {user.first_name}!* 🌟\n\n"
        "Welcome to the most complete Telegram Bot Script.\n\n"
        "🎮 /play — Quiz Time\n"
        "🏆 /leaderboard — Global Ranks\n"
        "📊 /mystats — My Performance\n"
        "😈 /tod — Truth or Dare\n"
        "💘 /situationship — Romantic Roleplay\n"
        "🔮 /mytype — AI Vibe Analysis"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def play(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in ACTIVE_QUESTIONS:
        await update.message.reply_text("⚠️ Answer the current question first!")
        return

    q_data = random.choice(QUESTIONS)
    opts = list(q_data["options"])
    random.shuffle(opts)

    ACTIVE_QUESTIONS[chat_id] = {"answer": q_data["answer"], "question": q_data["q"]}
    keyboard = [[InlineKeyboardButton(o, callback_data=f"ans|{o}")] for o in opts]
    
    sent = await update.message.reply_text(
        f"❓ *QUESTION:*\n\n{q_data['q']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    ACTIVE_QUESTIONS[chat_id]["msg_id"] = sent.message_id
    asyncio.create_task(timer(ctx, chat_id, sent.message_id))

async def timer(ctx, chat_id, msg_id):
    await asyncio.sleep(30)
    if chat_id in ACTIVE_QUESTIONS and ACTIVE_QUESTIONS[chat_id]["msg_id"] == msg_id:
        ans = ACTIVE_QUESTIONS[chat_id]["answer"]
        del ACTIVE_QUESTIONS[chat_id]
        try:
            await ctx.bot.edit_message_text(chat_id, msg_id, text=f"⏰ *TIME'S UP!*\nAnswer: *{ans}*", parse_mode="Markdown")
        except: pass

async def handle_quiz_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    user = query.from_user
    
    if chat_id not in ACTIVE_QUESTIONS:
        await query.answer("❌ Expired!", show_alert=True)
        return

    choice = query.data.split("|")[1]
    correct = ACTIVE_QUESTIONS[chat_id]["answer"]
    
    if choice == correct:
        stats = update_user_stats(user.id, user.first_name, True)
        await query.answer("✅ Correct!", show_alert=True)
        await query.edit_message_text(f"🎉 *CORRECT!*\nAnswer: *{correct}*\n🏅 Level: {stats['level']}", parse_mode="Markdown")
    else:
        update_user_stats(user.id, user.first_name, False)
        await query.answer("❌ Wrong!", show_alert=True)
        await query.edit_message_text(f"😔 *WRONG!*\nCorrect answer: *{correct}*", parse_mode="Markdown")
    
    del ACTIVE_QUESTIONS[chat_id]

async def leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    db = load_scores()
    if not db:
        await update.message.reply_text("🏆 No one has played yet!")
        return
    sorted_u = sorted(db.items(), key=lambda x: x[1]["score"], reverse=True)[:10]
    txt = "🏆 *TOP 10 PLAYERS*\n\n"
    for i, (uid, s) in enumerate(sorted_u):
        txt += f"{i+1}. *{s['name']}* — Lvl {s['level']} | {s['score']} pts\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def tod_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    choice = random.choice(["truth", "dare"])
    keyboard = [[InlineKeyboardButton(f"🔥 {l}", callback_data=f"tod|{choice}|{l.lower()}")] for l in ["Mild", "Medium", "Spicy", "Savage"]]
    await update.message.reply_text(f"🎲 Wheel: *{choice.upper()}*\nSelect level:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_tod_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer("Generating...")
    _, t_type, lvl = query.data.split("|")
    res = await ask_gpt(f"Party host. One {t_type} challenge. Level: {lvl}. Short.", f"For {query.from_user.first_name}")
    await query.edit_message_text(f"✨ *{t_type.upper()} ({lvl})*\n\n_{res}_", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Done!", callback_data="tod_done")]]), parse_mode="Markdown")

async def situationship(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; user = update.effective_user; vibe = random.choice(SITUATION_VIBES)
    res = await ask_gpt("Romance writer. 3 sentences. Cliffhanger.", f"Vibe: {vibe} for {user.first_name}")
    SITUATIONSHIP[chat_id] = {"user_id": str(user.id), "history": [res], "vibe": vibe}
    btns = [[InlineKeyboardButton("💬 Continue", callback_data="sit_continue")], [InlineKeyboardButton("🔀 New Story", callback_data="sit_new")]]
    await update.message.reply_text(f"💘 *SITUATIONSHIP: {vibe.upper()}*\n\n{res}", reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

async def handle_sit_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; chat_id = query.message.chat_id
    if query.data == "sit_continue":
        state = SITUATIONSHIP.get(chat_id)
        if not state: return
        res = await ask_gpt("Continue story. 2 sentences. Cliffhanger.", f"Last: {state['history'][-1]}")
        state["history"].append(res)
        await query.edit_message_text(f"💘 *STORY...*\n\n{res}", reply_markup=query.message.reply_markup, parse_mode="Markdown")
    elif query.data == "sit_new": await situationship(update, ctx)

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("tod", tod_menu))
    app.add_handler(CommandHandler("situationship", situationship))
    app.add_handler(CommandHandler("mystats", lambda u, c: u.message.reply_text("Use /play to see stats!")))

    # THE FIX: Using raw strings (r"") prevents the "invalid escape sequence" error on Render
    app.add_handler(CallbackQueryHandler(handle_quiz_callback, pattern=r"^ans\|"))
    app.add_handler(CallbackQueryHandler(handle_tod_callback, pattern=r"^tod\|"))
    app.add_handler(CallbackQueryHandler(handle_sit_callback, pattern=r"^sit_"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.edit_message_text("✅ Task Finished!"), pattern="^tod_done$"))

    print("🚀 DEPLOYED SUCCESSFULLY ON RENDER")
    app.run_polling()

if __name__ == "__main__":
    main()
