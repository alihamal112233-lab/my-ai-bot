# ============================================================
# PREMIUM MULTI AI TELEGRAM BOT - FULL PRODUCTION MASTER EDITION
# ARCHITECTURE : SINGLE-FILE FULL STACK TELEGRAM BOT
# HOSTING      : RENDER / CLOUD / LINUX / VPS COMPATIBLE (24/7)
# OWNER        : Forhad Khandakar (@forhadkhandakar)
# ============================================================

import os
import sys
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
# SECTION 1: KEEP-ALIVE SERVER (FOR RENDER & UPTIMEROBOT 24/7)
# ============================================================

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        response_text = "Telegram Multi-AI Bot is Running 24/7 Online with Full Features!"
        self.wfile.write(response_text.encode("utf-8"))

    def log_message(self, format, *args):
        return  # Suppress console log spam from UptimeRobot pings


def run_keep_alive_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
        print(f"[KEEP-ALIVE] Web server started successfully on port {port}")
        server.serve_forever()
    except Exception as error:
        print(f"[KEEP-ALIVE ERROR] {error}")


# Start Keep-Alive Server in a Background Daemon Thread
keep_alive_thread = threading.Thread(target=run_keep_alive_server, daemon=True)
keep_alive_thread.start()


# ============================================================
# SECTION 2: CONFIGURATION & ECONOMY SETTINGS
# ============================================================

# Telegram Bot Token
BOT_TOKEN = "6539038704:AAHmcuPjCpci4jhpa_WxHYqjJQArR2JvQlk"

# Telegram Numeric User ID of Owner/Admin
ADMIN_ID = 6539038704

# Owner Profile Details
SUPPORT_USERNAME = "@forhadkhandakar"
OWNER_NAME = "Forhad Khandakar"

# Economy & Point System Rules
INITIAL_POINTS = 100       # নতুন ইউজারের জয়েনিং বোনাস
COST_PER_MESSAGE = 3       # প্রতি মেসেজে খরচ
REFERRAL_POINTS = 50       # প্রতি রেফারে বোনাস
DAILY_REWARD_POINTS = 20   # দৈনিক ফ্রি ক্লেইম বোনাস
DAILY_COOLDOWN = 86400     # ২৪ ঘণ্টা = ৮৬৪০০ সেকেন্ড

# Force Join / Task Verification Targets
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

# Database File Paths (Relative Paths for universal OS/Cloud compatibility)
DATA_FILE = "multi_ai_bot_data.json"
API_FILE = "apis.json"

# API & Worker Engine Limits
API_TIMEOUT = 12
MAX_WORKERS = 7
MAX_HISTORY_TURNS = 2      # ইউজারের আগের কতটি কথোপকথন মনে রাখবে


# ============================================================
# SECTION 3: DEFAULT AI ENGINES CONFIGURATION
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
# SECTION 4: BOT INITIALIZATION & THREAD LOCKS
# ============================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML",
    threaded=True,
    num_threads=16
)

data_lock = threading.RLock()
api_lock = threading.RLock()


# ============================================================
# SECTION 5: DATA PERSISTENCE & STORAGE MANAGEMENT
# ============================================================

DATA = {
    "users": [],
    "verified_users": [],
    "blocked": [],
    "points": {},
    "referrals": {},
    "ref_by": {},
    "daily_claims": {},
    "user_models": {},
    "admin_settings": {
        "notify_new_user": True
    },
    "stats": {
        "messages": 0,
        "success": 0,
        "failed": 0,
        "api_requests": 0
    }
}

USER_HISTORY = {}
APIS = [dict(x) for x in DEFAULT_APIS]


def save_data():
    try:
        with data_lock:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(DATA, file, ensure_ascii=False, indent=2)
        return True
    except Exception as error:
        print("[DATA SAVE ERROR]", error)
        return False


def load_data():
    global DATA
    if not os.path.exists(DATA_FILE):
        save_data()
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            loaded = json.load(file)
        if isinstance(loaded, dict):
            DATA.update(loaded)
    except Exception as error:
        print("[DATA LOAD ERROR]", error)


load_data()


def save_apis():
    try:
        with api_lock:
            with open(API_FILE, "w", encoding="utf-8") as file:
                json.dump(APIS, file, ensure_ascii=False, indent=2)
        return True
    except Exception as error:
        print("[API SAVE ERROR]", error)
        return False


def load_apis():
    global APIS
    if not os.path.exists(API_FILE):
        APIS = [dict(x) for x in DEFAULT_APIS]
        save_apis()
        return

    try:
        with open(API_FILE, "r", encoding="utf-8") as file:
            loaded = json.load(file)
        if isinstance(loaded, list):
            APIS = loaded
    except Exception as error:
        print("[API LOAD ERROR]", error)
        APIS = [dict(x) for x in DEFAULT_APIS]
        save_apis()


load_apis()


# ============================================================
# SECTION 6: USER, ECONOMY & STATE HELPERS
# ============================================================

def add_user(user_id, user_first_name=""):
    is_new = False
    with data_lock:
        users = DATA.setdefault("users", [])
        if user_id not in users:
            users.append(user_id)
            is_new = True

        points = DATA.setdefault("points", {})
        if str(user_id) not in points:
            points[str(user_id)] = INITIAL_POINTS

    if is_new:
        save_data()
        if DATA.get("admin_settings", {}).get("notify_new_user", True) and ADMIN_ID:
            try:
                bot.send_message(
                    ADMIN_ID,
                    f"🔔 <b>New User Notification!</b>\n\n"
                    f"👤 Name: <b>{html.escape(user_first_name or 'Friend')}</b>\n"
                    f"🆔 User ID: <code>{user_id}</code>\n"
                    f"👥 Total Users: <b>{len(DATA['users'])}</b>"
                )
            except Exception:
                pass


def get_user_points(user_id):
    with data_lock:
        return DATA.get("points", {}).get(str(user_id), INITIAL_POINTS)


def modify_user_points(user_id, amount):
    with data_lock:
        points = DATA.setdefault("points", {})
        current = points.get(str(user_id), INITIAL_POINTS)
        updated = max(0, current + amount)
        points[str(user_id)] = updated
        save_data()
        return updated


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


def get_user_model(user_id):
    with data_lock:
        return DATA.get("user_models", {}).get(str(user_id), "Auto")


def set_user_model(user_id, model_name):
    with data_lock:
        models = DATA.setdefault("user_models", {})
        models[str(user_id)] = model_name
        save_data()


# ============================================================
# SECTION 7: CHAT CONTEXT MEMORY SYSTEM
# ============================================================

def append_chat_history(user_id, user_msg, ai_msg):
    history = USER_HISTORY.setdefault(user_id, [])
    history.append((user_msg, ai_msg))
    if len(history) > MAX_HISTORY_TURNS:
        history.pop(0)


def build_context_prompt(user_id, current_question):
    history = USER_HISTORY.get(user_id, [])
    if not history:
        return current_question

    context_parts = []
    for prev_q, prev_a in history:
        clean_prev_a = prev_a[:200] + "..." if len(prev_a) > 200 else prev_a
        context_parts.append(f"User: {prev_q}\nAI: {clean_prev_a}")

    context_parts.append(f"User: {current_question}")
    return "\n".join(context_parts)


# ============================================================
# SECTION 8: REFERRAL ENGINE
# ============================================================

def get_bot_username():
    try:
        me = bot.get_me()
        return me.username
    except Exception as error:
        print("[BOT USERNAME ERROR]", error)
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
        points = DATA.setdefault("points", {})

        if str(user_id) in ref_by:
            return

        ref_by[str(user_id)] = inviter
        inviter_key = str(inviter)
        referrals[inviter_key] = referrals.get(inviter_key, 0) + 1
        points[inviter_key] = points.get(inviter_key, INITIAL_POINTS) + REFERRAL_POINTS

    save_data()

    try:
        bot.send_message(
            inviter,
            f"🎉 <b>NEW REFERRAL JOINED!</b>\n\n"
            f"একজন নতুন ব্যবহারকারী আপনার লিংক দিয়ে যুক্ত হয়েছেন।\n\n"
            f"🎁 বোনাস পয়েন্ট: <b>+{REFERRAL_POINTS} Points!</b>\n"
            f"💰 বর্তমান ব্যালেন্স: <b>{get_user_points(inviter)}</b>\n"
            f"👥 মোট রেফারেল: <b>{DATA['referrals'].get(str(inviter), 0)} জন</b>"
        )
    except Exception:
        pass


def referral_count(user_id):
    with data_lock:
        return DATA.get("referrals", {}).get(str(user_id), 0)


# ============================================================
# SECTION 9: KEYBOARDS & UI INTERFACES
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

Start দেওয়া শেষ হলে নিচে 
<b>✅ আমি সবগুলোতে Start দিয়েছি</b> বাটনে চাপ দিন।
━━━━━━━━━━━━━━━━━━
🔒 <b>Secure Access</b>
⚡ <b>Fast Verification</b>
🤖 <b>Multi-AI Assistant</b>
"""


# রেগুলার ইউজার কিবোর্ড
def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🤖 AI CHAT", "⚙️ CHOOSE AI")
    keyboard.row("🎁 DAILY REWARD", "👤 PROFILE")
    keyboard.row("🔗 REFER & EARN", "📊 MY STATS")
    keyboard.row("ℹ️ ABOUT", "🆘 SUPPORT")
    return keyboard


# অ্যাডমিনের জন্য ডেডিকেটেড কিবোর্ড
def admin_reply_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📊 Live Stats", "📢 Broadcast")
    keyboard.row("➕ Add Points", "➖ Deduct Points")
    keyboard.row("🎁 Gift All", "🔍 Check User")
    keyboard.row("🚫 Ban User", "✅ Unban User")
    keyboard.row("🤖 Manage APIs", "📁 Export DB")
    keyboard.row("🏠 Exit Admin Mode")
    return keyboard


def model_selector_keyboard(user_id):
    current = get_user_model(user_id)
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    auto_label = f"⚡ Auto (Fastest) {'✅' if current == 'Auto' else ''}"
    keyboard.add(types.InlineKeyboardButton(auto_label, callback_data="select_model_Auto"))

    buttons = []
    with api_lock:
        for api in APIS:
            name = api["name"]
            is_sel = "✅" if current == name else ""
            buttons.append(types.InlineKeyboardButton(f"{name} {is_sel}", callback_data=f"select_model_{name}"))

    keyboard.add(*buttons)
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
        with open(filename, "wb") as file:
            file.write(downloaded)

        return filename
    except Exception as error:
        print("[PROFILE PHOTO ERROR]", error)
        return None


def send_welcome(message):
    user = message.from_user
    user_id = user.id
    name = html.escape(user.first_name or "Friend")
    points = get_user_points(user_id)

    text = f"""
<b>🤖 PREMIUM AI ASSISTANT</b>
━━━━━━━━━━━━━━━━━━
👋 স্বাগতম <b>{name}</b>

আপনি এখন আমাদের Premium AI Assistant ব্যবহার করতে পারবেন।

🎁 জয়েনিং বোনাস: <b>{INITIAL_POINTS} Points</b> যুক্ত হয়েছে!
💬 প্রতি প্রশ্নে খরচ: <b>{COST_PER_MESSAGE} Points</b>
━━━━━━━━━━━━━━━━━━
💰 বর্তমান ব্যালেন্স: <b>{points} Points</b>
🔗 রেফারেল সংখ্যা: <b>{referral_count(user_id)} জন</b>
━━━━━━━━━━━━━━━━━━
নিচের <b>🤖 AI CHAT</b> বাটনে চাপ দিয়ে যেকোনো প্রশ্ন করুন।
"""
    photo = get_profile_photo(user_id)
    try:
        if photo and os.path.exists(photo):
            with open(photo, "rb") as file:
                bot.send_photo(message.chat.id, file, caption=text, reply_markup=main_menu())
            try:
                os.remove(photo)
            except Exception:
                pass
        else:
            bot.send_message(message.chat.id, text, reply_markup=main_menu())
    except Exception as error:
        print("[WELCOME ERROR]", error)
        bot.send_message(message.chat.id, text, reply_markup=main_menu())


# ============================================================
# SECTION 10: ADMIN PANEL ROUTING & ACTIONS
# ============================================================

@bot.message_handler(commands=["admin"])
def admin_panel_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 <b>Access Denied:</b> আপনি অ্যাডমিন নন!")
        return

    bot.send_message(
        message.chat.id,
        f"""
<b>👑 OWNER / ADMIN CONTROL PANEL</b>
━━━━━━━━━━━━━━━━━━
স্বাগতম <b>{OWNER_NAME}</b>!
আপনার নিচের কিবোর্ডটি **Admin Keyboard**-এ পরিবর্তন করা হয়েছে।

নিচের বাটনগুলো ব্যবহার করে পুরো বট নিয়ন্ত্রণ করুন।
━━━━━━━━━━━━━━━━━━
""",
        reply_markup=admin_reply_keyboard()
    )


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text in [
    "📊 Live Stats", "📢 Broadcast", "➕ Add Points", "➖ Deduct Points",
    "🎁 Gift All", "🔍 Check User", "🚫 Ban User", "✅ Unban User",
    "🤖 Manage APIs", "📁 Export DB", "🏠 Exit Admin Mode"
])
def admin_keyboard_handler(message):
    action = message.text

    if action == "📊 Live Stats":
        with data_lock:
            total_u = len(DATA.get("users", []))
            verified_u = len(DATA.get("verified_users", []))
            blocked_u = len(DATA.get("blocked", []))
            msgs = DATA.get("stats", {}).get("messages", 0)
            succ = DATA.get("stats", {}).get("success", 0)
            fail = DATA.get("stats", {}).get("failed", 0)
            reqs = DATA.get("stats", {}).get("api_requests", 0)

        text = f"""
<b>📊 LIVE BOT ANALYTICS</b>
━━━━━━━━━━━━━━━━━━
👥 <b>Total Users:</b> {total_u}
✅ <b>Verified Users:</b> {verified_u}
🚫 <b>Blocked Users:</b> {blocked_u}
━━━━━━━━━━━━━━━━━━
💬 <b>Total Messages:</b> {msgs}
🏆 <b>AI Success:</b> {succ}
❌ <b>AI Failed:</b> {fail}
⚡ <b>API Calls:</b> {reqs}
━━━━━━━━━━━━━━━━━━
🟢 <b>Server:</b> Online (24/7 Active)
"""
        bot.send_message(message.chat.id, text, reply_markup=admin_reply_keyboard())

    elif action == "📢 Broadcast":
        msg = bot.send_message(message.chat.id, "📢 <b>ব্রডকাস্ট মেসেজটি লিখে পাঠান:</b>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_broadcast)

    elif action == "➕ Add Points":
        msg = bot.send_message(message.chat.id, "➕ <b>ইউজার আইডি এবং পয়েন্ট দিন:</b>\n\nফরম্যাট: <code>User_ID Amount</code>\nউদাহরণ: <code>12345678 100</code>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_add_points)

    elif action == "➖ Deduct Points":
        msg = bot.send_message(message.chat.id, "➖ <b>ইউজার আইডি এবং মাইনাস করার পয়েন্ট দিন:</b>\n\nফরম্যাট: <code>User_ID Amount</code>\nউদাহরণ: <code>12345678 50</code>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_deduct_points)

    elif action == "🎁 Gift All":
        msg = bot.send_message(message.chat.id, "🎁 <b>সব ইউজারকে কত পয়েন্ট উপহার দিতে চান লিখুন:</b>\n\nউদাহরণ: <code>50</code>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_gift_all)

    elif action == "🔍 Check User":
        msg = bot.send_message(message.chat.id, "🔍 <b>ইউজারের Telegram ID পাঠান:</b>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_check_user)

    elif action == "🚫 Ban User":
        msg = bot.send_message(message.chat.id, "🚫 <b>ব্যান করতে ইউজারের Telegram ID পাঠান:</b>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_ban_user)

    elif action == "✅ Unban User":
        msg = bot.send_message(message.chat.id, "✅ <b>আনব্যান করতে ইউজারের Telegram ID পাঠান:</b>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_unban_user)

    elif action == "📁 Export DB":
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file, caption="📁 <b>User Database Backup (JSON)</b>", reply_markup=admin_reply_keyboard())
            else:
                bot.send_message(message.chat.id, "❌ ডাটা ফাইল পাওয়া যায়নি।", reply_markup=admin_reply_keyboard())
        except Exception as error:
            bot.send_message(message.chat.id, f"❌ Export Error: {error}", reply_markup=admin_reply_keyboard())

    elif action == "🤖 Manage APIs":
        kb = types.InlineKeyboardMarkup(row_width=2)
        with api_lock:
            for idx, api in enumerate(APIS):
                status_icon = "🟢" if api.get("enabled", True) else "🔴"
                kb.add(types.InlineKeyboardButton(f"{status_icon} {api['name']}", callback_data=f"toggle_api_{idx}"))
        bot.send_message(message.chat.id, "<b>🤖 AI ENGINE STATUS (ক্লিক করে On/Off করুন):</b>", reply_markup=kb)

    elif action == "🏠 Exit Admin Mode":
        bot.send_message(
            message.chat.id,
            "🏠 <b>Switched to User Menu!</b>\nআপনি এখন ইউজার মোডে আছেন।",
            reply_markup=main_menu()
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_api_"))
def toggle_api_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    idx = int(call.data.replace("toggle_api_", ""))
    with api_lock:
        if 0 <= idx < len(APIS):
            APIS[idx]["enabled"] = not APIS[idx].get("enabled", True)
            save_apis()

    kb = types.InlineKeyboardMarkup(row_width=2)
    with api_lock:
        for i, api in enumerate(APIS):
            status_icon = "🟢" if api.get("enabled", True) else "🔴"
            kb.add(types.InlineKeyboardButton(f"{status_icon} {api['name']}", callback_data=f"toggle_api_{i}"))
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        pass


def process_add_points(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।", reply_markup=admin_reply_keyboard())
        return
    try:
        parts = message.text.strip().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ ফরম্যাট ভুল! লিখুন: <code>User_ID Amount</code>", reply_markup=admin_reply_keyboard())
            return
        uid = int(parts[0])
        amt = int(parts[1])

        new_pts = modify_user_points(uid, amt)
        bot.send_message(message.chat.id, f"✅ <b>User {uid} কে +{amt} পয়েন্ট দেওয়া হয়েছে!</b>\nবর্তমান মোট পয়েন্ট: <b>{new_pts}</b>", reply_markup=admin_reply_keyboard())

        try:
            bot.send_message(uid, f"🎁 <b>অ্যাডমিন আপনাকে +{amt} পয়েন্ট যুক্ত করে দিয়েছেন!</b>\n💰 আপনার বর্তমান পয়েন্ট: <b>{new_pts}</b>")
        except Exception:
            pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ সংখ্যা সঠিকভাবে দিন!", reply_markup=admin_reply_keyboard())


def process_deduct_points(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।", reply_markup=admin_reply_keyboard())
        return
    try:
        parts = message.text.strip().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ ফরম্যাট ভুল! লিখুন: <code>User_ID Amount</code>", reply_markup=admin_reply_keyboard())
            return
        uid = int(parts[0])
        amt = int(parts[1])

        new_pts = modify_user_points(uid, -amt)
        bot.send_message(message.chat.id, f"✅ <b>User {uid} থেকে -{amt} পয়েন্ট কাটা হয়েছে!</b>\nবর্তমান মোট পয়েন্ট: <b>{new_pts}</b>", reply_markup=admin_reply_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "❌ সংখ্যা সঠিকভাবে দিন!", reply_markup=admin_reply_keyboard())


def process_gift_all(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।", reply_markup=admin_reply_keyboard())
        return
    try:
        amt = int(message.text.strip())
        if amt <= 0:
            bot.send_message(message.chat.id, "❌ পয়েন্ট সংখ্যা ধনাত্মক হতে হবে।", reply_markup=admin_reply_keyboard())
            return

        with data_lock:
            users = list(DATA.get("users", []))
            points = DATA.setdefault("points", {})
            for u in users:
                points[str(u)] = points.get(str(u), INITIAL_POINTS) + amt
        save_data()

        bot.send_message(message.chat.id, f"🎉 <b>সফল!</b> সকল ({len(users)}) ইউজারকে <b>+{amt} পয়েন্ট</b> উপহার দেওয়া হয়েছে!", reply_markup=admin_reply_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "❌ সংখ্যা সঠিকভাবে দিন!", reply_markup=admin_reply_keyboard())


def process_check_user(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।", reply_markup=admin_reply_keyboard())
        return
    try:
        uid = int(message.text.strip())
        pts = get_user_points(uid)
        refs = referral_count(uid)
        is_blk = is_blocked(uid)
        is_vrf = is_verified(uid)
        model = get_user_model(uid)

        text = f"""
<b>🔍 USER DETAILS</b>
━━━━━━━━━━━━━━━━━━
🆔 User ID: <code>{uid}</code>
💰 Current Points: <b>{pts}</b>
🤖 Selected Model: <b>{model}</b>
👥 Total Referrals: <b>{refs}</b>
✅ Verified: <b>{'Yes' if is_vrf else 'No'}</b>
🚫 Blocked: <b>{'Yes' if is_blk else 'No'}</b>
━━━━━━━━━━━━━━━━━━
"""
        bot.send_message(message.chat.id, text, reply_markup=admin_reply_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "❌ অবৈধ User ID!", reply_markup=admin_reply_keyboard())


def process_broadcast(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ Broadcast বাতিল করা হয়েছে।", reply_markup=admin_reply_keyboard())
        return

    with data_lock:
        users = list(DATA.get("users", []))

    bot.send_message(message.chat.id, f"🚀 <b>{len(users)}</b> জন ইউজারের কাছে ব্রডকাস্ট শুরু হয়েছে...")

    success = 0
    failed = 0

    for uid in users:
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            success += 1
            time.sleep(0.05)
        except Exception:
            failed += 1

    bot.send_message(
        message.chat.id,
        f"✅ <b>Broadcast সম্পন্ন হয়েছে!</b>\n\n🎯 সফল: {success}\n❌ ব্যর্থ: {failed}",
        reply_markup=admin_reply_keyboard()
    )


def process_ban_user(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।", reply_markup=admin_reply_keyboard())
        return
    try:
        target_id = int(message.text.strip())
        with data_lock:
            blocked = DATA.setdefault("blocked", [])
            if target_id not in blocked:
                blocked.append(target_id)
                save_data()
        bot.send_message(message.chat.id, f"🚫 <b>User {target_id} সফলভাবে ব্যান করা হয়েছে!</b>", reply_markup=admin_reply_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "❌ অবৈধ User ID!", reply_markup=admin_reply_keyboard())


def process_unban_user(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।", reply_markup=admin_reply_keyboard())
        return
    try:
        target_id = int(message.text.strip())
        with data_lock:
            blocked = DATA.setdefault("blocked", [])
            if target_id in blocked:
                blocked.remove(target_id)
                save_data()
        bot.send_message(message.chat.id, f"✅ <b>User {target_id} সফলভাবে আনব্যান করা হয়েছে!</b>", reply_markup=admin_reply_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "❌ অবৈধ User ID!", reply_markup=admin_reply_keyboard())


# ============================================================
# SECTION 11: USER COMMANDS & HANDLERS
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):
    user = message.from_user
    user_id = user.id

    add_user(user_id, user.first_name)

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


@bot.message_handler(commands=["daily"])
@bot.message_handler(func=lambda m: m.text == "🎁 DAILY REWARD")
def daily_reward_handler(message):
    user_id = message.from_user.id
    if not is_verified(user_id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    now = int(time.time())
    with data_lock:
        claims = DATA.setdefault("daily_claims", {})
        last_claim = claims.get(str(user_id), 0)

        if now - last_claim >= DAILY_COOLDOWN:
            claims[str(user_id)] = now
            new_balance = modify_user_points(user_id, DAILY_REWARD_POINTS)
            bot.send_message(
                message.chat.id,
                f"🎁 <b>DAILY REWARD CLAIMED!</b>\n\n"
                f"আপনি পেয়েছেন: <b>+{DAILY_REWARD_POINTS} Points</b>\n"
                f"💰 আপনার বর্তমান ব্যালেন্স: <b>{new_balance} Points</b>\n\n"
                f"আগামীকাল আবার ফ্রি পয়েন্ট ক্লেইম করতে পারবেন!",
                reply_markup=main_menu()
            )
        else:
            rem_sec = DAILY_COOLDOWN - (now - last_claim)
            hours = rem_sec // 3600
            mins = (rem_sec % 3600) // 60
            bot.send_message(
                message.chat.id,
                f"⏳ <b>আপনি আজকের রিওয়ার্ড অলরেডি নিয়েছেন!</b>\n\n"
                f"পরবর্তী রিওয়ার্ড পেতে অপেক্ষা করুন:\n"
                f"🕒 <b>{hours} ঘণ্টা {mins} মিনিট</b>\n\n"
                f"💡 আরও পয়েন্ট পেতে বন্ধুদের রেফার করুন!",
                reply_markup=main_menu()
            )


@bot.message_handler(func=lambda m: m.text == "⚙️ CHOOSE AI")
def choose_ai_handler(message):
    user_id = message.from_user.id
    if not is_verified(user_id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    current = get_user_model(user_id)
    bot.send_message(
        message.chat.id,
        f"<b>⚙️ AI ENGINE SELECTOR</b>\n━━━━━━━━━━━━━━━━━━\nবর্তমান মডেল: <b>{current}</b>\n\nপছন্দমতো AI সিলেক্ট করুন:",
        reply_markup=model_selector_keyboard(user_id)
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_model_"))
def select_model_callback(call):
    user_id = call.from_user.id
    model_name = call.data.replace("select_model_", "")
    set_user_model(user_id, model_name)

    bot.answer_callback_query(call.id, f"✅ Selected: {model_name}")
    bot.edit_message_text(
        f"<b>⚙️ AI ENGINE SELECTOR</b>\n━━━━━━━━━━━━━━━━━━\nবর্তমান মডেল: <b>{model_name}</b>\n\nপছন্দমতো AI সিলেক্ট করুন:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=model_selector_keyboard(user_id)
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    if not is_verified(message.from_user.id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    bot.send_message(
        message.chat.id,
        f"""
<b>📚 HELP CENTER</b>
━━━━━━━━━━━━━━━━━━
🤖 <b>AI CHAT:</b> যেকোনো প্রশ্ন লিখে পাঠান (খরচ: {COST_PER_MESSAGE} পয়েন্ট)।
⚙️ <b>CHOOSE AI:</b> আপনার পছন্দের এআই ইঞ্জিন সিলেক্ট করুন।
🎁 <b>DAILY REWARD:</b> প্রতিদিন একবার ফ্রি +{DAILY_REWARD_POINTS} পয়েন্ট নিন।
🔗 <b>REFER:</b> বন্ধুদের ইনভাইট করে প্রতি রেফারে +{REFERRAL_POINTS} পয়েন্ট পান।
👤 <b>PROFILE:</b> নিজের ব্যালেন্স ও পয়েন্ট দেখুন।
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

    points = get_user_points(message.from_user.id)
    selected = get_user_model(message.from_user.id)

    bot.send_message(
        message.chat.id,
        f"""
<b>🤖 AI CHAT MODE</b>
━━━━━━━━━━━━━━━━━━
💰 বর্তমান পয়েন্ট: <b>{points}</b>
🤖 বর্তমান এআই: <b>{selected}</b>
💬 প্রতি মেসেজে খরচ: <b>{COST_PER_MESSAGE} Points</b>

আপনার যেকোনো প্রশ্ন এখন লিখে পাঠান।
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
    points = get_user_points(user.id)
    model = get_user_model(user.id)

    text = f"""
<b>👤 MY PROFILE</b>
━━━━━━━━━━━━━━━━━━
👤 Name: <b>{name}</b>
🔗 Username: <b>{html.escape(username)}</b>
🆔 Telegram ID: <code>{user.id}</code>
💰 Current Points: <b>{points} Points</b>
🤖 Selected AI: <b>{model}</b>
🎁 My Referrals: <b>{count} জন</b>
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
    share_url = f"https://t.me/share/url?url={link}&text=🤖 Premium AI Assistant ব্যবহার করুন এবং ফ্রি পয়েন্ট পান!"
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
🎁 প্রতি রেফারে পাবেন: <b>+{REFERRAL_POINTS} Points!</b>
👥 Total Referrals: <b>{count}</b>

বন্ধুদের এই Link পাঠান। তারা Bot-এ আসলে আপনার অ্যাকাউন্টে সরাসরি +{REFERRAL_POINTS} পয়েন্ট যুক্ত হবে।
""",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data == "my_referrals")
def my_referrals(call):
    count = referral_count(call.from_user.id)
    pts = get_user_points(call.from_user.id)
    bot.answer_callback_query(call.id)
    try:
        bot.send_message(
            call.message.chat.id,
            f"<b>📊 REFERRAL STATISTICS</b>\n━━━━━━━━━━━━━━━━━━\n👥 Successful Referrals: <b>{count}</b>\n💰 Total Points: <b>{pts}</b>\n🔗 Link: <code>{referral_link(call.from_user.id)}</code>"
        )
    except Exception:
        pass


@bot.message_handler(func=lambda m: m.text == "📊 MY STATS")
def my_stats(message):
    if not is_verified(message.from_user.id):
        bot.send_message(message.chat.id, force_join_message(), reply_markup=force_join_keyboard())
        return

    count = referral_count(message.from_user.id)
    points = get_user_points(message.from_user.id)
    with data_lock:
        total = len(DATA.get("users", []))

    bot.send_message(
        message.chat.id,
        f"""
<b>📊 MY STATISTICS</b>
━━━━━━━━━━━━━━━━━━
💰 Your Points: <b>{points}</b>
🎁 Your Referrals: <b>{count}</b>
👥 Total Bot Users: <b>{total}</b>
🟢 Bot Status: <b>ONLINE (24/7)</b>
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
🧠 Context Memory
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
# SECTION 12: API PARSING & EXECUTION ENGINE
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
            headers={"User-Agent": "Premium-MultiAI-Bot/3.0"}
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


def ask_ai(user_id, question):
    contextual_prompt = build_context_prompt(user_id, question)
    selected_model = get_user_model(user_id)

    with api_lock:
        if selected_model != "Auto":
            target_api = next((api for api in APIS if api["name"] == selected_model and api.get("enabled", True)), None)
            if target_api:
                return call_api(target_api, contextual_prompt)

        enabled_apis = [dict(api) for api in APIS if api.get("enabled", True)]

    if not enabled_apis:
        return None

    executor = ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(enabled_apis)))
    futures = []

    try:
        for api in enabled_apis:
            futures.append(executor.submit(call_api, api, contextual_prompt))

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
# SECTION 13: MESSAGE ROUTING & USER HANDLERS
# ============================================================

@bot.message_handler(content_types=["text"])
def user_message(message):
    user_id = message.from_user.id
    menu_buttons = [
        "🤖 AI CHAT", "⚙️ CHOOSE AI", "🎁 DAILY REWARD",
        "👤 PROFILE", "🔗 REFER & EARN", "📊 MY STATS", "ℹ️ ABOUT", "🆘 SUPPORT",
        "📊 Live Stats", "📢 Broadcast", "➕ Add Points", "➖ Deduct Points",
        "🎁 Gift All", "🔍 Check User", "🚫 Ban User", "✅ Unban User",
        "🤖 Manage APIs", "📁 Export DB", "🏠 Exit Admin Mode"
    ]

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

    add_user(user_id, message.from_user.first_name)

    user_points = get_user_points(user_id)
    if user_points < COST_PER_MESSAGE:
        bot.send_message(
            message.chat.id,
            f"⚠️ <b>আপনার পর্যাপ্ত পয়েন্ট নেই!</b>\n\n"
            f"💰 বর্তমান পয়েন্ট: <b>{user_points}</b>\n"
            f"💬 প্রতি মেসেজে প্রয়োজন: <b>{COST_PER_MESSAGE} Points</b>\n\n"
            f"🎁 প্রতিদিনের ফ্রি পয়েন্ট নিতে <b>🎁 DAILY REWARD</b> বাটনে চাপ দিন অথবা বন্ধুদের রেফার করুন!",
            reply_markup=main_menu()
        )
        return

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

    waiting = bot.send_message(chat_id, "⚡ <b>AI Processing...</b>\n\n🚀 Generating best response...")
    result = ask_ai(user_id, question)

    try:
        bot.delete_message(chat_id, waiting.message_id)
    except Exception:
        pass

    if result:
        remaining_points = modify_user_points(user_id, -COST_PER_MESSAGE)
        append_chat_history(user_id, question, result["answer"])

        with data_lock:
            DATA["stats"]["success"] = DATA["stats"].get("success", 0) + 1
        save_data()

        send_answer(chat_id, result)

        if remaining_points <= COST_PER_MESSAGE:
            bot.send_message(
                chat_id,
                f"⚠️ <b>সতর্কতা:</b> আপনার পয়েন্ট প্রায় শেষ (বাকি: {remaining_points})! ফ্রি পয়েন্ট পেতে <b>🎁 DAILY REWARD</b> নিন বা বন্ধুদের রেফার করুন।"
            )
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
# SECTION 14: INFINITY POLLING LOOP RUNNER
# ============================================================

def run_bot():
    print()
    print("=" * 60)
    print("       PREMIUM MULTI AI TELEGRAM BOT (MASTER EDITION)")
    print("=" * 60)
    print(f"Owner Name    : {OWNER_NAME} ({SUPPORT_USERNAME})")
    print(f"Admin ID      : {ADMIN_ID}")
    print(f"Join Bonus    : {INITIAL_POINTS} Points")
    print(f"Cost / Msg    : {COST_PER_MESSAGE} Points")
    print(f"Daily Bonus   : {DAILY_REWARD_POINTS} Points")
    print(f"Ref Bonus     : {REFERRAL_POINTS} Points")
    print(f"Max Workers   : {MAX_WORKERS}")
    print(f"Timeout       : {API_TIMEOUT}s")
    print(f"Status        : ONLINE (24/7)")
    print("=" * 60)
    print()

    while True:
        try:
            bot.delete_webhook(drop_pending_updates=True)
            time.sleep(1)
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
        except KeyboardInterrupt:
            print("\n[BOT] Stopped by User.")
            break
        except Exception as error:
            print("[BOT RUNNER ERROR]", error)
            time.sleep(5)


if __name__ == "__main__":
    run_bot()
