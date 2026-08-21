# ============================================================
# PREMIUM MULTI AI TELEGRAM BOT
# FULL SINGLE-FILE VERSION (CLOUD / RENDER COMPATIBLE)
# ============================================================

import os
import json
import time
import html
import threading
import requests
import telebot

from http.server import HTTPServer, BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from telebot import types


# ============================================================
# KEEP-ALIVE DUMMY WEB SERVER FOR RENDER / UPTIMEROBOT
# ============================================================

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Telegram Multi-AI Bot is Running 24/7!")

    def log_message(self, format, *args):
        return  # Suppress logging for keep-alive pings


def run_keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
    print(f"[WEB SERVER] Listening on port {port}")
    server.serve_forever()


# Start Keep-Alive Server in Background
threading.Thread(target=run_keep_alive, daemon=True).start()


# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = "6539038704:AAEH1wnpI14F6HWG8A9xa3mD4sz4jY_xrj0"

# Owner & Support Information
SUPPORT_USERNAME = "@forhadkhandakar"
OWNER_NAME = "Forhad Khandakar"

# Force Task / Follow Bots
FORCE_BOTS = [
    {
        "title": "🤖 Number Info Bot",
        "username": "@number_info00_bot",
        "url": "https://t.me/number_info00_bot"
    },
    {
        "title": "⚡ SMS Hack Bot",
        "username": "@smshack78bot",
        "url": "https://t.me/smshack78bot"
    }
]

# Relative Paths for Storage
DATA_FILE = "multi_ai_bot_data.json"
API_FILE = "apis.json"

# Execution Settings
API_TIMEOUT = 12
MAX_WORKERS = 7


# ============================================================
# DEFAULT AI APIs
# ============================================================

DEFAULT_APIS = [
    {
        "name": "Gemini",
        "url": "https://r-bots-free-apis.co08.art/api/gemini",
        "enabled": True,
        "prompt": ""
    },
    {
        "name": "DeepSeek R1",
        "url": "https://r-bots-free-apis.co08.art/api/deepseek-r1",
        "enabled": True,
        "prompt": ""
    },
    {
        "name": "DeepSeek V3",
        "url": "https://r-bots-free-apis.co08.art/api/deepseek-v3",
        "enabled": True,
        "prompt": ""
    },
    {
        "name": "Cohere",
        "url": "https://r-bots-free-apis.co08.art/api/cohere",
        "enabled": True,
        "prompt": ""
    },
    {
        "name": "Qwen",
        "url": "https://r-bots-free-apis.co08.art/api/qwen",
        "enabled": True,
        "prompt": ""
    },
    {
        "name": "Llama Meta",
        "url": "https://r-bots-free-apis.co08.art/api/llama-meta",
        "enabled": True,
        "prompt": ""
    },
    {
        "name": "GPTLogic",
        "url": "https://r-bots-free-apis.co08.art/api/gptlogic",
        "enabled": True,
        "prompt": "be friendly"
    }
]


# ============================================================
# BOT INITIALIZATION & LOCKS
# ============================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML",
    threaded=True,
    num_threads=12
)

data_lock = threading.RLock()
api_lock = threading.RLock()


# ============================================================
# DATA STORAGE & PERSISTENCE
# ============================================================

DATA = {
    "users": [],
    "verified_users": [],
    "blocked": [],
    "referrals": {},
    "ref_by": {},
    "stats": {
        "messages": 0,
        "success": 0,
        "failed": 0,
        "api_requests": 0
    }
}

APIS = [dict(x) for x in DEFAULT_APIS]


def save_data():
    try:
        with data_lock:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(DATA, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print("[DATA SAVE ERROR]", e)
        return False


def load_data():
    global DATA
    if not os.path.exists(DATA_FILE):
        save_data()
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            DATA.update(loaded)
    except Exception as e:
        print("[DATA LOAD ERROR]", e)


load_data()


def save_apis():
    try:
        with api_lock:
            with open(API_FILE, "w", encoding="utf-8") as f:
                json.dump(APIS, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print("[API SAVE ERROR]", e)
        return False


def load_apis():
    global APIS
    if not os.path.exists(API_FILE):
        APIS = [dict(x) for x in DEFAULT_APIS]
        save_apis()
        return

    try:
        with open(API_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, list):
            APIS = loaded
    except Exception as e:
        print("[API LOAD ERROR]", e)
        APIS = [dict(x) for x in DEFAULT_APIS]
        save_apis()


load_apis()


# ============================================================
# USER & VERIFICATION HELPERS
# ============================================================

def add_user(user_id):
    changed = False
    with data_lock:
        users = DATA.setdefault("users", [])
        if user_id not in users:
            users.append(user_id)
            changed = True
    if changed:
        save_data()


def is_verified(user_id):
    with data_lock:
        return user_id in DATA.get("verified_users", [])


def set_verified(user_id):
    with data_lock:
        verified = DATA.setdefault("verified_users", [])
        if user_id not in verified:
            verified.append(user_id)
            save_data()


def is_blocked(user_id):
    with data_lock:
        return user_id in DATA.get("blocked", [])


def total_users():
    with data_lock:
        return len(DATA.get("users", []))


# ============================================================
# REFERRAL HELPERS
# ============================================================

def get_bot_username():
    try:
        me = bot.get_me()
        return me.username
    except Exception as e:
        print("[BOT USERNAME ERROR]", e)
        return None


BOT_USERNAME = get_bot_username()


def referral_link(user_id):
    if not BOT_USERNAME:
        return ""
    return f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"


def process_referral(user_id, start_parameter):
    if not start_parameter or not start_parameter.startswith("ref_"):
        return

    raw = start_parameter.replace("ref_", "", 1).strip()
    try:
        inviter = int(raw)
    except ValueError:
        return

    if inviter == user_id:
        return

    with data_lock:
        ref_by = DATA.setdefault("ref_by", {})
        referrals = DATA.setdefault("referrals", {})

        if str(user_id) in ref_by:
            return

        ref_by[str(user_id)] = inviter
        inviter_key = str(inviter)
        referrals[inviter_key] = referrals.get(inviter_key, 0) + 1

    save_data()

    try:
        bot.send_message(
            inviter,
            f"🎉 <b>NEW REFERRAL!</b>\n\n"
            f"একজন নতুন user আপনার referral link দিয়ে bot-এ এসেছে।\n\n"
            f"👤 User ID: <code>{user_id}</code>\n"
            f"🎁 আপনার মোট referral: <b>{DATA['referrals'].get(str(inviter), 0)}</b>"
        )
    except Exception:
        pass


def referral_count(user_id):
    with data_lock:
        return DATA.get("referrals", {}).get(str(user_id), 0)


# ============================================================
# KEYBOARDS & MESSAGES
# ============================================================

def force_join_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for target in FORCE_BOTS:
        keyboard.add(types.InlineKeyboardButton(target["title"], url=target["url"]))
    keyboard.add(types.InlineKeyboardButton("✅ আমি সবগুলোতে Start দিয়েছি", callback_data="verify_join"))
    keyboard.add(types.InlineKeyboardButton("🆘 Support", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}"))
    return keyboard


def force_join_message():
    return f"""
<b>🔐 ACCESS VERIFICATION</b>
━━━━━━━━━━━━━━━━━━
বটটি সম্পূর্ণ ফ্রিতে ব্যবহার করতে নিচের <b>{len(FORCE_BOTS)}টি Bot</b>-এ গিয়ে Start দিন।

নিচের বাটনগুলোতে ক্লিক করে Start দেওয়া শেষ হলে 
<b>✅ আমি সবগুলোতে Start দিয়েছি</b> বাটনে চাপ দিন।
━━━━━━━━━━━━━━━━━━
🔒 <b>Secure Access</b>
⚡ <b>Fast Verification</b>
🤖 <b>Multi-AI Assistant</b>
"""


def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🤖 AI CHAT", "👤 PROFILE")
    keyboard.row("🔗 REFER & EARN", "📊 MY STATS")
    keyboard.row("ℹ️ ABOUT", "🆘 SUPPORT")
    return keyboard


def get_profile_photo(user_id):
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if not photos or photos.total_count == 0:
            return None

        photo = photos.photos[0][-1]
        file_info = bot.get_file(photo.file_id)
        downloaded = bot.download_file(file_info.file_path)

        filename = f"profile_{user_id}.jpg"
        with open(filename, "wb") as f:
            f.write(downloaded)

        return filename
    except Exception as e:
        print("[PROFILE PHOTO ERROR]", e)
        return None


def send_welcome(message):
    user = message.from_user
    user_id = user.id
    name = html.escape(user.first_name or "Friend")

    text = f"""
<b>🤖 PREMIUM AI ASSISTANT</b>
━━━━━━━━━━━━━━━━━━
👋 স্বাগতম <b>{name}</b>

আপনি এখন আমাদের Premium AI Assistant ব্যবহার করতে পারবেন।

⚡ <b>7 AI Engines</b>
🚀 <b>Parallel Processing</b>
🏆 <b>First Valid Response</b>
🔄 <b>Automatic Fallback</b>
🛡 <b>Smart Error Handling</b>
━━━━━━━━━━━━━━━━━━
নিচের <b>🤖 AI CHAT</b> বাটনে চাপ দিয়ে যেকোনো প্রশ্ন করুন।
━━━━━━━━━━━━━━━━━━
🔗 Referral: <b>{referral_count(user_id)}</b> জন
"""
    photo = get_profile_photo(user_id)
    try:
        if photo and os.path.exists(photo):
            with open(photo, "rb") as f:
                bot.send_photo(message.chat.id, f, caption=text, reply_markup=main_menu())
            try:
                os.remove(photo)
            except Exception:
                pass
        else:
            bot.send_message(message.chat.id, text, reply_markup=main_menu())
    except Exception as e:
        print("[WELCOME ERROR]", e)
        bot.send_message(message.chat.id, text, reply_markup=main_menu())


# ============================================================
# BOT COMMANDS & HANDLERS
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):
    user = message.from_user
    user_id = user.id

    add_user(user_id)

    parts = message.text.split(maxsplit=1)
    parameter = parts[1] if len(parts) > 1 else ""
    process_referral(user_id, parameter)

    if not is_verified(user_id):
        name = html.escape(user.first_name or "Friend")
        text = f"""
<b>👋 WELCOME, {name}</b>
━━━━━━━━━━━━━━━━━━
🤖 <b>PREMIUM MULTI AI</b>

একাধিক AI ব্যবহার করে দ্রুত ও স্মার্ট উত্তর পাওয়ার জন্য এই Bot তৈরি করা হয়েছে।

প্রথমে নিচের Bot গুলোতে Visit/Start করুন এবং ভেরিফাই বাটনে চাপ দিন।
━━━━━━━━━━━━━━━━━━
"""
        bot.send_message(message.chat.id, text, reply_markup=force_join_keyboard())
        return

    send_welcome(message)


@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    user_id = call.from_user.id
    set_verified(user_id)

    bot.answer_callback_query(call.id, "✅ Verification Successful!")
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    send_welcome(call.message)


@bot.message_handler(commands=["help"])
def help_command(message):
    if not is_verified(message.from_user.id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    bot.send_message(
        message.chat.id,
        """
<b>📚 HELP CENTER</b>
━━━━━━━━━━━━━━━━━━
🤖 <b>AI CHAT:</b> প্রশ্ন লিখে পাঠান।
🔗 <b>REFER:</b> নিজের referral link শেয়ার করুন।
👤 <b>PROFILE:</b> নিজের Telegram তথ্য দেখুন।
📊 <b>MY STATS:</b> নিজের পরিসংখ্যান দেখুন।
🆘 <b>SUPPORT:</b> Support-এর সাথে যোগাযোগ করুন।
━━━━━━━━━━━━━━━━━━
/cancel — Main Menu
""",
        reply_markup=main_menu()
    )


@bot.message_handler(commands=["cancel"])
def cancel(message):
    if not is_verified(message.from_user.id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    bot.send_message(message.chat.id, "🏠 <b>Main Menu</b>", reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text == "🤖 AI CHAT")
def ai_chat(message):
    if not is_verified(message.from_user.id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    bot.send_message(
        message.chat.id,
        """
<b>🤖 AI CHAT MODE</b>
━━━━━━━━━━━━━━━━━━
আপনার যেকোনো প্রশ্ন এখন লিখে পাঠান।

উদাহরণ:
<code>বাংলাদেশের রাজধানী কী?</code>
<code>Python কী?</code>
<code>একটি সুন্দর ফেসবুক ক্যাপশন লিখে দাও</code>
━━━━━━━━━━━━━━━━━━
❌ Main Menu-তে যেতে: /cancel
""",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(func=lambda m: m.text == "👤 PROFILE")
def profile(message):
    if not is_verified(message.from_user.id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    user = message.from_user
    name = html.escape(user.first_name or "Not Set")
    username = "@" + user.username if user.username else "Not Set"
    count = referral_count(user.id)

    text = f"""
<b>👤 MY PROFILE</b>
━━━━━━━━━━━━━━━━━━
👤 Name: <b>{name}</b>
🔗 Username: <b>{html.escape(username)}</b>
🆔 Telegram ID: <code>{user.id}</code>
🎁 My Referrals: <b>{count}</b>
━━━━━━━━━━━━━━━━━━
🤖 Premium AI User
"""
    bot.send_message(message.chat.id, text, reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text == "🔗 REFER & EARN")
def refer_button(message):
    if not is_verified(message.from_user.id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    link = referral_link(message.from_user.id)
    count = referral_count(message.from_user.id)

    keyboard = types.InlineKeyboardMarkup()
    share_url = f"https://t.me/share/url?url={link}&text=🤖 Premium AI Assistant ব্যবহার করুন!"
    keyboard.add(types.InlineKeyboardButton("📤 SHARE REFERRAL LINK", url=share_url))
    keyboard.add(types.InlineKeyboardButton("📊 MY REFERRALS", callback_data="my_referrals"))

    bot.send_message(
        message.chat.id,
        f"""
<b>🔗 REFER & EARN</b>
━━━━━━━━━━━━━━━━━━
আপনার Personal Referral Link:
<code>{link}</code>
━━━━━━━━━━━━━━━━━━
👥 Total Referrals: <b>{count}</b>

বন্ধুদের এই Link পাঠান। তারা Bot-এ আসলে আপনার Referral যোগ হবে।
""",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data == "my_referrals")
def my_referrals(call):
    count = referral_count(call.from_user.id)
    bot.answer_callback_query(call.id)
    try:
        bot.send_message(
            call.message.chat.id,
            f"<b>📊 REFERRAL STATISTICS</b>\n━━━━━━━━━━━━━━━━━━\n👥 Successful Referrals: <b>{count}</b>\n🔗 Link: <code>{referral_link(call.from_user.id)}</code>"
        )
    except Exception:
        pass


@bot.message_handler(func=lambda m: m.text == "📊 MY STATS")
def my_stats(message):
    if not is_verified(message.from_user.id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    count = referral_count(message.from_user.id)
    with data_lock:
        total = len(DATA.get("users", []))

    bot.send_message(
        message.chat.id,
        f"""
<b>📊 MY STATISTICS</b>
━━━━━━━━━━━━━━━━━━
🎁 Your Referrals: <b>{count}</b>
👥 Total Bot Users: <b>{total}</b>
🟢 Bot Status: <b>ONLINE</b>
━━━━━━━━━━━━━━━━━━
""",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda m: m.text == "ℹ️ ABOUT")
def about(message):
    if not is_verified(message.from_user.id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    bot.send_message(
        message.chat.id,
        """
<b>ℹ️ ABOUT PREMIUM AI</b>
━━━━━━━━━━━━━━━━━━
🤖 Multi AI Assistant

এই Bot একই সময়ে একাধিক AI API-তে Request পাঠায় এবং সবার আগে পাওয়া সেরা উত্তরটি প্রদান করে।

⚡ Fast Response
🚀 Parallel Processing
🔄 Auto Fallback
🛡 Error Handling
━━━━━━━━━━━━━━━━━━
Developed for Premium AI Experience.
""",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda m: m.text == "🆘 SUPPORT")
def support(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🆘 CONTACT SUPPORT", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}"))

    bot.send_message(
        message.chat.id,
        f"""
<b>🆘 SUPPORT CENTER</b>
━━━━━━━━━━━━━━━━━━
যেকোনো সহায়তার জন্য যোগাযোগ করুন:
👤 Support: <b>{SUPPORT_USERNAME}</b>
""",
        reply_markup=keyboard
    )


@bot.message_handler(func=lambda m: m.text.strip().startswith("/2"))
def support_id_command(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "<b>🆘 FORMAT:</b> <code>/2 @username</code>")
        return

    support_id = parts[1].strip()
    if not support_id.startswith("@"):
        support_id = "@" + support_id

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🆘 CONTACT SUPPORT", url=f"https://t.me/{support_id.replace('@', '')}"))

    bot.send_message(
        message.chat.id,
        f"<b>🆘 SUPPORT</b>\n━━━━━━━━━━━━━━━━━━\nSupport ID: <b>{html.escape(support_id)}</b>",
        reply_markup=keyboard
    )


def is_identity_question(text):
    text = text.lower().strip()
    keywords = [
        "তোমাকে কে বানিয়েছে", "তোরে কে বানাইছে", "কে তোমাকে বানিয়েছে",
        "কে বানিয়েছে তোমাকে", "তোমারে কে বানাইছে", "তোমাকে কে তৈরি করেছে",
        "who made you", "who created you", "who built you", "owner"
    ]
    return any(keyword in text for keyword in keywords)


def identity_answer():
    return f"""
আমি একটি স্মার্ট Multi-AI সহকারী। 🤖

আমাকে তৈরি ও নিয়ন্ত্রণ করেছেন <b>{OWNER_NAME}</b> ({SUPPORT_USERNAME})।

আপনার যেকোনো প্রশ্নের উত্তর দিতে আমি প্রস্তুত!
""".strip()


# ============================================================
# API CALL & HANDLING
# ============================================================

def extract_response(data):
    if isinstance(data, str):
        text = data.strip()
        return text if text else None

    if isinstance(data, list):
        for item in data:
            result = extract_response(item)
            if result:
                return result
        return None

    if not isinstance(data, dict):
        return None

    fields = ["response", "answer", "message", "result", "content", "text", "output", "generated_text"]
    for field in fields:
        value = data.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for key in ["data", "result", "response", "choices"]:
        nested = data.get(key)
        if isinstance(nested, (dict, list)):
            result = extract_response(nested)
            if result:
                return result

    return None


def clean_response(text):
    if not text:
        return None

    text = str(text).strip()
     if "</think>" in text:
        text = text.split("</think>", 1)[1].strip()

    if "<think>" in text and "</think>" not in text:
        return None

    return text if text else None


def call_api(api, question):
    name = api.get("name", "Unknown")
    url = api.get("url")
    if not url:
        return None

    try:
        params = {"q": question}
        prompt = api.get("prompt", "")
        if prompt:
            params["prompt"] = prompt

        with data_lock:
            DATA.setdefault("stats", {})
            DATA["stats"]["api_requests"] = DATA["stats"].get("api_requests", 0) + 1

        started = time.perf_counter()
        response = requests.get(
            url,
            params=params,
            timeout=API_TIMEOUT,
            headers={"User-Agent": "Premium-MultiAI-Bot/2.0"}
        )
        elapsed = time.perf_counter() - started

        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except Exception:
            data = response.text

        answer = extract_response(data)
        answer = clean_response(answer)

        if not answer:
            return None

        return {
            "api": name,
            "answer": answer,
            "time": elapsed
        }
    except Exception:
        return None


def ask_ai(question):
    with api_lock:
        enabled_apis = [dict(api) for api in APIS if api.get("enabled", True)]

    if not enabled_apis:
        return None

    executor = ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(enabled_apis)))
    futures = []

    try:
        for api in enabled_apis:
            futures.append(executor.submit(call_api, api, question))

        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception:
                continue

            if result:
                for other in futures:
                    if other != future:
                        other.cancel()
                return result
    finally:
        try:
            executor.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            executor.shutdown(wait=False)

    return None


def send_answer(chat_id, result):
    api_name = html.escape(result["api"])
    answer = result["answer"]
    elapsed = result["time"]

    safe_answer = html.escape(answer)

    text = (
        f"🤖 <b>{api_name}</b>\n"
        f"⚡ <b>{elapsed:.2f}s</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{safe_answer}"
    )

    limit = 3900
    if len(text) <= limit:
        bot.send_message(chat_id, text)
        return

    for start_idx in range(0, len(text), limit):
        bot.send_message(chat_id, text[start_idx:start_idx + limit])


# ============================================================
# USER TEXT HANDLER
# ============================================================

@bot.message_handler(content_types=["text"])
def user_message(message):
    user_id = message.from_user.id
    menu_buttons = ["🤖 AI CHAT", "👤 PROFILE", "🔗 REFER & EARN", "📊 MY STATS", "ℹ️ ABOUT", "🆘 SUPPORT"]

    if message.text in menu_buttons or message.text.startswith("/"):
        return

    if is_blocked(user_id):
        bot.send_message(message.chat.id, "🚫 আপনি এই Bot ব্যবহার করতে পারবেন না।")
        return

    if not is_verified(user_id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    question = message.text.strip()
    if not question:
        return

    add_user(user_id)

    with data_lock:
        DATA["stats"]["messages"] = DATA["stats"].get("messages", 0) + 1
    save_data()

    if is_identity_question(question):
        bot.send_message(message.chat.id, identity_answer())
        with data_lock:
            DATA["stats"]["success"] = DATA["stats"].get("success", 0) + 1
        save_data()
        return

    chat_id = message.chat.id
    try:
        bot.send_chat_action(chat_id, "typing")
    except Exception:
        pass

    waiting = bot.send_message(chat_id, "⚡ <b>AI Processing...</b>\n\n🚀 Searching the fastest AI...")
    result = ask_ai(question)

    try:
        bot.delete_message(chat_id, waiting.message_id)
    except Exception:
        pass

    if result:
        with data_lock:
            DATA["stats"]["success"] = DATA["stats"].get("success", 0) + 1
        save_data()
        send_answer(chat_id, result)
    else:
        with data_lock:
            DATA["stats"]["failed"] = DATA["stats"].get("failed", 0) + 1
        save_data()
        bot.send_message(
            chat_id,
            "❌ <b>AI Response পাওয়া যায়নি</b>\n\nসব enabled AI বর্তমানে Unavailable অথবা Timeout করেছে।\n🔄 কিছুক্ষণ পরে আবার চেষ্টা করুন।",
            reply_markup=main_menu()
        )


@bot.message_handler(content_types=["photo", "video", "document", "audio", "voice", "sticker", "animation", "location", "contact"])
def unsupported_message(message):
    if not is_verified(message.from_user.id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return
    bot.send_message(
        message.chat.id,
        "⚠️ <b>Text Message ব্যবহার করুন।</b>\n\nAI-কে প্রশ্ন করতে আপনার প্রশ্নটি Text হিসেবে লিখে পাঠান।",
        reply_markup=main_menu()
    )


# ============================================================
# BOT RUNNER
# ============================================================

def run_bot():
    print()
    print("=" * 60)
    print("       PREMIUM MULTI AI TELEGRAM BOT")
    print("=" * 60)
    print(f"Owner         : {OWNER_NAME} ({SUPPORT_USERNAME})")
    print(f"Workers       : {MAX_WORKERS}")
    print(f"Timeout       : {API_TIMEOUT}s")
    print(f"Status        : ONLINE")
    print("=" * 60)
    print()

    while True:
        try:
            bot.delete_webhook(drop_pending_updates=True)
            time.sleep(1)
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
        except KeyboardInterrupt:
            print("\n[BOT] Stopped.")
            break
        except Exception as e:
            print("[BOT ERROR]", e)
            time.sleep(5)


if __name__ == "__main__":
    run_bot()
