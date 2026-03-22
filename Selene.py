import telebot
import sqlite3
import os
import smtplib
import time
import requests
from email.message import EmailMessage
from datetime import datetime, date

# ================= CONFIG =================
BOT_TOKEN = "8390807268:AAF_Xy3qVqoomsFPqmmZUQMdw28GNq-w6hc"
OWNER_ID = 6402924254  # هذا ايديك انت
bot = telebot.TeleBot(BOT_TOKEN)

DB_NAME = "numbers.db"
LOG_FILE = "console-log"

# ======== EMAIL ROTATION CONFIG ========
EMAIL_ACCOUNTS = [
    {"email": "freelancer123124@gmail.com", "password": "lgkujmqlhbislszw"},
    {"email": "uuii9178@gmail.com", "password": "wtfeiulbuudnkqhg"},
    {"email": "owij401@gmail.com", "password": "tfrdhnudabziacgv"},
    {"email": "llalanana7@gmail.com", "password": "vskxkybtnhyqxcjk"},
    {"email": "wqwaxaxaca@gmail.com", "password": "flzcyaoynjzzpoum"},
    {"email": "cicada001101@gmail.com", "password": "zyuutbqypkutnfhg"},
]

EMAIL_RECEIVER = "support@support.whatsapp.com"

EMAIL_TEXT = """Здравствуйте, служба поддержки WhatsApp.

У меня проблема с регистрацией номера.
Пожалуйста, помогите и отправьте код.

Мой номер: {phone}
"""

email_index = 0

# ================= LOGGING =================
def write_log(text):
    print(text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def get_server_geo():
    try:
        r = requests.get("http://ip-api.com/json", timeout=5).json()
        return {
            "ip": r.get("query"),
            "country": r.get("country"),
            "region": r.get("regionName"),
            "city": r.get("city"),
            "isp": r.get("isp"),
        }
    except:
        return {
            "ip": "Unknown",
            "country": "Unknown",
            "region": "Unknown",
            "city": "Unknown",
            "isp": "Unknown",
        }

def log_start_user(message):
    u = message.from_user
    geo = get_server_geo()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log = f"""
============================
🚀 START COMMAND
============================
👤 Name     : {u.first_name}
🧾 Username : @{u.username}
🆔 User ID  : {u.id}
🌍 Language : {u.language_code}
⭐ Premium  : {u.is_premium}

🌐 IP       : {geo['ip']}
🏳️ Country  : {geo['country']}
📍 Region   : {geo['region']}
🏙 City     : {geo['city']}
📡 ISP      : {geo['isp']}

⏰ Time     : {now}
============================
"""
    write_log(log)

def log_phone(user_id, phone):
    write_log(f"📱 PHONE | User:{user_id} | {phone} | {datetime.now()}")

# ================= CHECK IF USER IS OWNER =================
def is_owner(user_id):
    return user_id == OWNER_ID

# ================= DATABASE =================
def setup_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        phone TEXT,
        timestamp TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        timestamp TEXT
    )""")

    conn.commit()
    conn.close()

def phone_exists(user_id, phone):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM numbers WHERE user_id=? AND phone=?", (user_id, phone))
    r = c.fetchone()
    conn.close()
    return r is not None

def save_phone(user_id, phone):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO numbers (user_id, phone, timestamp) VALUES (?, ?, ?)",
        (user_id, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def log_email(phone):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO emails (phone, timestamp) VALUES (?, ?)",
        (phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

# ================= EMAIL =================
def send_whatsapp_email(phone):
    global email_index
    acc = EMAIL_ACCOUNTS[email_index]
    email_index = (email_index + 1) % len(EMAIL_ACCOUNTS)

    msg = EmailMessage()
    msg["From"] = acc["email"]
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "WhatsApp Registration Problem"
    msg.set_content(EMAIL_TEXT.format(phone=phone))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(acc["email"], acc["password"])
        smtp.send_message(msg)

    log_email(phone)

# ================= HELPERS =================
def is_valid_phone(phone):
    p = phone.replace("+", "").replace(" ", "")
    return p.isdigit() and len(p) >= 10

# ================= COMMANDS =================
@bot.message_handler(commands=["start"])
def start(message):
    log_start_user(message)
    bot.reply_to(
        message,
        f"👋 مرحباً بك في البوت!\n\n"
        f"📱 الأوامر المتاحة:\n"
        f"📋 /list - عرض أرقامك\n"
        f"📤 /export - تصدير الأرقام\n"
        f"🗑 /clear - مسح القائمة\n"
        f"✉️ /fix رقم - إرسال إيميل\n"
        f"📊 /stats - إحصائيات\n"
        f"➕ /plusfile - رفع ملف"
    )

@bot.message_handler(commands=["list"])
def list_numbers(message):
    uid = message.from_user.id
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT phone, timestamp FROM numbers WHERE user_id=?", (uid,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        bot.reply_to(message, "📭 ليستتك فاضية")
        return

    text = "📋 أرقامك:\n\n"
    for i, (p, t) in enumerate(rows, 1):
        text += f"{i}. {p} - {t}\n"
    bot.reply_to(message, text)

@bot.message_handler(commands=["export"])
def export_numbers(message):
    uid = message.from_user.id
    fname = f"numbers_{uid}.txt"

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT phone FROM numbers WHERE user_id=?", (uid,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        bot.reply_to(message, "📭 لا يوجد أرقام")
        return

    with open(fname, "w") as f:
        for (p,) in rows:
            f.write(p + "\n")

    with open(fname, "rb") as f:
        bot.send_document(message.chat.id, f)
    os.remove(fname)

@bot.message_handler(commands=["clear"])
def clear_list(message):
    uid = message.from_user.id
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM numbers WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()
    bot.reply_to(message, "🗑 تم مسح ليستتك")

@bot.message_handler(commands=["fix"])
def fix(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❌ /fix 9725xxxxxxx")
        return
    phone = parts[1]
    if not is_valid_phone(phone):
        bot.reply_to(message, "❌ رقم غير صالح")
        return
    send_whatsapp_email(phone)
    bot.reply_to(message, "✅ تم إرسال الإيميل")

@bot.message_handler(commands=["stats"])
def stats(message):
    start = time.time()
    msg = bot.send_message(message.chat.id, "⏳ ...")
    latency = int((time.time() - start) * 1000)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM emails")
    total = c.fetchone()[0]

    today = date.today().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM emails WHERE timestamp LIKE ?", (today + "%",))
    today_count = c.fetchone()[0]
    conn.close()

    bot.edit_message_text(
        f"📊 BOT STATS\n\n"
        f"⚡ Ping: {latency} ms\n"
        f"✉️ Total Emails: {total}\n"
        f"📅 Today Emails: {today_count}",
        message.chat.id,
        msg.message_id
    )

@bot.message_handler(commands=["plusfile"])
def plusfile(message):
    bot.reply_to(message, "📎 ابعت ملف TXT فيه الأرقام")

@bot.message_handler(content_types=["document"])
def handle_file(message):
    file = bot.download_file(bot.get_file(message.document.file_id).file_path)
    inp = "input.txt"
    out = "output.txt"

    with open(inp, "wb") as f:
        f.write(file)

    with open(inp, "r", errors="ignore") as f, open(out, "w") as o:
        for line in f:
            n = line.strip().replace("+", "")
            if n.isdigit():
                o.write("+" + n + "\n")

    with open(out, "rb") as f:
        bot.send_document(message.chat.id, f)

    os.remove(inp)
    os.remove(out)

@bot.message_handler(func=lambda m: not m.text.startswith("/"))
def handle_phone(message):
    phone = message.text.strip()
    uid = message.from_user.id

    if not is_valid_phone(phone):
        bot.reply_to(message, "❌ رقم غير صالح")
        return

    if phone_exists(uid, phone):
        bot.reply_to(message, "⚠️ الرقم مسجل قبل كده")
        return

    save_phone(uid, phone)
    log_phone(uid, phone)
    bot.reply_to(message, "✅ تم حفظ الرقم")

# ================= RUN =================
if __name__ == "__main__":
    setup_database()
    print("=" * 50)
    print("✅ BOT STARTED")
    print(f"🤖 Token: {BOT_TOKEN[:15]}...")
    print(f"👤 Owner ID: {OWNER_ID}")
    print("=" * 50)
    print("✅ البوت يعمل الآن...")
    bot.polling(none_stop=True)