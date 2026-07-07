import os
import random
import time
import requests
import sqlite3
import threading
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Flask для Render
app = Flask('')

@app.route('/')
def home():
    return "🤖 Black Russia Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

TELEGRAM_TOKEN = "8612396180:AAF7LNaZyWVUJX-hB-Gy06jQWJ8lYf9bqUA"
TELEGRAM_CHAT_ID = "7276498444"
OWNER_ID = int(TELEGRAM_CHAT_ID)

SERVERS = [
    "RED", "GREEN", "BLUE", "YELLOW", "ORANGE", "PURPLE",
    "MOSCOW", "SPB", "SOCHI", "KAZAN", "SAMARA",
    "ROSTOV", "ANAPA", "EKB", "KRASNODAR", "NOVOSIB",
    "CHITA", "IVANOVO"
]

DB_PATH = "black_russia_bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nickname TEXT,
                  password TEXT,
                  server TEXT,
                  level INTEGER DEFAULT 1,
                  created_at TEXT)''')
    conn.commit()
    conn.close()

def add_account(nickname, password, server):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO accounts (nickname, password, server, created_at) VALUES (?, ?, ?, ?)",
              (nickname, password, server, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_accounts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT nickname, password, server, level FROM accounts ORDER BY id DESC")
    accounts = c.fetchall()
    conn.close()
    return accounts

def generate_nick():
    prefixes = ["Bjorn", "Erik", "Lars", "Magnus", "Sven", "Alexei", "Dmitry", "Ivan",
                "James", "John", "William", "Oliver", "Diego", "Santiago", "Mateo",
                "Ethan", "Noah", "Liam", "Mason", "Lukas", "Maximilian", "Felix"]
    suffixes = ["Alez", "Vex", "Kuro", "Drake", "Fury", "Shin", "Storm",
                "Venom", "Hawk", "Wolf", "Tiger", "Dragon", "Knight"]
    return f"{random.choice(prefixes)}_{random.choice(suffixes)}"

class BlackRussiaBot:
    def __init__(self, bot_id, bot_instance):
        self.bot_id = bot_id
        self.bot_instance = bot_instance
        self.nickname = generate_nick()
        self.server = random.choice(SERVERS)
        self.password = "vorivate8888"
        self.running = True
        self.is_registered = False
        self.is_authenticated = False
        self.level = 1
        self.xp = 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://blackrussia.online/"
        })

    def register(self):
        try:
            data = {
                "username": self.nickname,
                "password": self.password,
                "password_confirm": self.password,
                "server": self.server,
                "referral": "IZHSDR"
            }
            response = self.session.post(
                "https://blackrussia.online/refreg/register.php",
                data=data,
                timeout=30,
                allow_redirects=True
            )
            if response.status_code == 200:
                content = response.text.lower()
                if "успешно" in content or "success" in content or "зарегистрирован" in content:
                    self.is_registered = True
                    add_account(self.nickname, self.password, self.server)
                    self.bot_instance.send_message(
                        chat_id=OWNER_ID,
                        text=f"✅ НОВЫЙ АККАУНТ!\n👤 {self.nickname}\n🔑 {self.password}\n🌍 {self.server}"
                    )
                    return True
                elif "занят" in content or "already" in content:
                    self.nickname = generate_nick()
                    return False
                else:
                    return False
            else:
                return False
        except:
            return False

    def login(self):
        try:
            data = {"username": self.nickname, "password": self.password, "server": self.server}
            response = self.session.post(
                "https://blackrussia.online/api/login",
                json=data,
                timeout=30
            )
            if response.status_code == 200:
                try:
                    if response.json().get("success"):
                        self.is_authenticated = True
                        print(f"✅ {self.nickname} вошёл в игру")
                        self.bot_instance.send_message(
                            chat_id=OWNER_ID,
                            text=f"🎮 {self.nickname} ВОШЕЛ В ИГРУ!\n🌍 {self.server}"
                        )
                        return True
                except:
                    pass
            return False
        except:
            return False

    def check_level_up(self):
        self.xp += 1
        if self.xp >= self.level * 21.6:
            self.level += 1
            self.xp = 0
            self.bot_instance.send_message(
                chat_id=OWNER_ID,
                text=f"⬆️ {self.nickname} ПОВЫСИЛ УРОВЕНЬ!\n📊 Уровень: {self.level}"
            )
            return True
        return False

    def send_message(self):
        if not self.is_authenticated:
            return
        msgs = ["👋 Всем привет!", "😊 Хорошего дня!", "🤗 Всем мира!", "🔥 Погнали!"]
        try:
            self.session.post("https://blackrussia.online/api/chat",
                              json={"message": random.choice(msgs), "channel": "global", "server": self.server},
                              timeout=15)
        except:
            pass

    def run(self):
        for _ in range(5):
            if self.register():
                break
            time.sleep(3)
        if not self.is_registered:
            print(f"❌ {self.nickname} - не удалось зарегистрироваться")
            return
        if not self.login():
            print(f"❌ {self.nickname} - не удалось войти")
            return
        while self.running:
            self.send_message()
            self.check_level_up()
            time.sleep(30)

    def stop(self):
        self.running = False

bots = []
bot_running = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("📊 Аккаунты", callback_data='accounts')],
            [InlineKeyboardButton("▶️ Запустить", callback_data='start_bots')],
            [InlineKeyboardButton("⏹️ Остановить", callback_data='stop_bots')],
        ]
        await update.message.reply_text(
            "👑 *ВЛАДЕЛЕЦ*\n\n"
            "/start_bots - запустить 6 ботов\n"
            "/stop_bots - остановить\n"
            "/bots - список аккаунтов",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("👤 Запрос отправлен владельцу.")

async def start_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_running, bots
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Только владелец!")
        return
    if bot_running:
        await update.message.reply_text("⚠️ Уже запущены!")
        return
    bot_running = True
    bots = []
    await update.message.reply_text("🚀 Запуск 6 ботов...")
    init_db()
    for i in range(6):
        bot = BlackRussiaBot(i+1, context.bot)
        thread = threading.Thread(target=bot.run)
        thread.daemon = True
        thread.start()
        bots.append(bot)
        time.sleep(3)
    await update.message.reply_text(f"✅ Запущено {len(bots)} ботов!")

async def stop_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_running
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Только владелец!")
        return
    if not bot_running:
        await update.message.reply_text("⚠️ Уже остановлены!")
        return
    bot_running = False
    for bot in bots:
        bot.stop()
    await update.message.reply_text("⏹️ Остановлены!")

async def bots_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Только владелец!")
        return
    accounts = get_accounts()
    if not accounts:
        await update.message.reply_text("📭 Нет аккаунтов.")
        return
    text = "📋 *АККАУНТЫ*\n\n"
    for nick, pwd, server, level in accounts:
        text += f"• `{nick}` | {server} | Ур.{level} | пароль: `{pwd}`\n"
    await update.message.reply_text(text, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'accounts':
        await bots_list(update, context)
    elif data == 'start_bots':
        await start_bots(update, context)
    elif data == 'stop_bots':
        await stop_bots(update, context)

def main():
    print("🤖 Запуск...")
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start_bots", start_bots))
    app.add_handler(CommandHandler("stop_bots", stop_bots))
    app.add_handler(CommandHandler("bots", bots_list))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("✅ Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    time.sleep(2)
    main()