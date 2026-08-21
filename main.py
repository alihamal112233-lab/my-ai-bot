# ============================================================
# PREMIUM MULTI AI TELEGRAM BOT + POINTS & ADMIN PANEL
# FULL SINGLE-FILE PRODUCTION VERSION (RENDER / CLOUD READY)
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
# KEEP-ALIVE SERVER (FOR RENDER & UPTIMEROBOT)
# ============================================================

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Telegram Multi-AI Bot is Running 24/7!")

    def log_message(self, format, *args):
        return


def run_keep_alive():
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
        print(f"[WEB SERVER] Running on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"[WEB SERVER ERROR] {e}")


threading.Thread(target=run_keep_alive, daemon=True).start()


# ============================================================
# CONFIGURATION & ECONOMY
# ============================================================

BOT_TOKEN = "6539038704:AAHmcuPjCpci4jhpa_WxHYqjJQArR2JvQlk"

# Telegram Numeric User ID
ADMIN_ID = 5504272381  # আপনার Telegram Numeric User ID

SUPPORT_USERNAME = "@forhadkhandakar"
OWNER_NAME = "Forhad Khandakar"

# Point System Settings
INITIAL_POINTS = 100      # নতুন ইউজারের জয়েনিং বোনাস (১০০ পয়েন্ট)
COST_PER_MESSAGE = 3      # প্রতি মেসেজে খরচ (৩ পয়েন্ট)
REFERRAL_POINTS = 50      # প্রতি রেফারে বোনাস (৫০ পয়েন্ট)

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

DATA_FILE = "multi_ai_bot_data.json"
API_FILE = "apis.json"

API_TIMEOUT = 12
MAX_WORKERS = 7


# ============================================================
# DEFAULT AI APIs
# ============================================================

DEFAULT_APIS = [
    {"name": "Gemini", "url": "https://r-bots-free-apis.co08.art/api/gemini", "enabled": True, "prompt": ""},
    {"name": "DeepSeek R1", "url": "https://r-bots-free-apis.co08.art/api/deepseek-r1", "enabled": True, "prompt": ""},
    {"name": "DeepSeek V3", "url": "https://r-bots-free-apis.co08.art/api/deepseek-v3", "enabled": True, "prompt": ""},
    {"name": "Cohere", "url": "https://r-bots-free-apis.co08.art/api/cohere", "enabled": True, "prompt": ""},
    {"name": "Qwen", "url": "https://r-bots-free-apis.co08.art/api/qwen", "enabled": True, "prompt": ""},
    {"name": "Llama Meta", "url": "https://r-bots-free-apis.co08.art/api/llama-meta", "enabled": True, "prompt": ""},
    {"name": "GPTLogic", "url": "https://r-bots-free-apis.co08.art/api/gptlogic", "enabled": True, "prompt": "be friendly"}
]


# ============================================================
# BOT INITIALIZATION
# ============================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True, num_threads=12)

data_lock = threading.RLock()
api_lock = threading.RLock()


# ============================================================
# DATA PERSISTENCE
# ============================================================

DATA = {
    "users": [],
    "verified_users": [],
    "blocked": [],
    "points": {},
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
# USER & POINT HELPERS
# ============================================================

def add_user(user_id):
    changed = False
    with data_lock:
        users = DATA.setdefault("users", [])
        if user_id not in users:
            users.append(user_id)
            changed = True

        points = DATA.setdefault("points", {})
        if str(user_id) not in points:
            points[str(user_id)] = INITIAL_POINTS
            changed = True

    if changed:
        save_data()


def get_user_points(user_id):
    with data_lock:
        return DATA.get("points", {}).get(str(user_id), INITIAL_POINTS)


def modify_user_points(user_id, amount):
    with data_lock:
        points = DATA.setdefault("points", {})
        current = points.get(str(user_id), INITIAL_POINTS)
        points[str(user_id)] = max(0, current + amount)
        save_data()
        return points[str(user_id)]


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
        points = DATA.setdefault("points", {})

        if str(user_id) in ref_by:
            return

        ref_by[str(user_id)] = inviter
        inviter_key = str(inviter)
        referrals[inviter_key] = referrals.get(inviter_key, 0) + 1

        # বোনাস পয়েন্ট যোগ
        points[inviter_key] = points.get(inviter_key, INITIAL_POINTS) + REFERRAL_POINTS

    save_data()

    try:
        bot.send_message(
            inviter,
            f"🎉 <b>NEW REFERRAL JOINED!</b>\n\n"
            f"একজন নতুন user আপনার referral link দিয়ে এসেছে।\n\n"
            f"🎁 আপনি পেয়েছেন: <b>+{REFERRAL_POINTS} Points!</b>\n"
            f"💰 আপনার বর্তমান পয়েন্ট: <b>{get_user_points(inviter)}</b>\n"
            f"👥 মোট রেফারেল: <b>{DATA['referrals'].get(str(inviter), 0)}</b>"
        )
    except Exception:
        pass


def referral_count(user_id):
    with data_lock:
        return DATA.get("referrals", {}).get(str(user_id), 0)


# ============================================================
# UI & KEYBOARDS
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
বটটি ফ্রিতে ব্যবহার করতে নিচের <b>{len(FORCE_BOTS)}টি Bot</b>-এ গিয়ে Start দিন।

Start দেওয়া শেষ হলে নিচে 
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
# ADMIN PANEL LOGIC & UI
# ============================================================

def admin_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("📊 Live Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
    )
    keyboard.add(
        types.InlineKeyboardButton("➕ Add Points", callback_data="admin_add_pts"),
        types.InlineKeyboardButton("➖ Deduct Points", callback_data="admin_deduct_pts")
    )
    keyboard.add(
        types.InlineKeyboardButton("🔍 Check User", callback_data="admin_chk_user"),
        types.InlineKeyboardButton("📁 Export DB", callback_data="admin_export")
    )
    keyboard.add(
        types.InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ Unban User", callback_data="admin_unban")
    )
    keyboard.add(
        types.InlineKeyboardButton("🤖 Manage AI Engines", callback_data="admin_apis")
    )
    return keyboard


@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 <b>Access Denied:</b> আপনি অ্যাডমিন নন!")
        return

    bot.send_message(
        message.chat.id,
        f"""
<b>👑 OWNER / ADMIN CONTROL PANEL</b>
━━━━━━━━━━━━━━━━━━
স্বাগতম <b>{OWNER_NAME}</b>!
নিচের অপশনগুলো দিয়ে আপনি পুরো বট ও পয়েন্ট নিয়ন্ত্রণ করতে পারেন।
━━━━━━━━━━━━━━━━━━
""",
        reply_markup=admin_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "🚫 Access Denied!", show_alert=True)
        return

    action = call.data

    if action == "admin_stats":
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
🟢 <b>Server Status:</b> Running 24/7
"""
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=admin_keyboard())

    elif action == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 <b>ব্রডকাস্ট মেসেজটি লিখে পাঠান:</b>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_broadcast)

    elif action == "admin_add_pts":
        msg = bot.send_message(call.message.chat.id, "➕ <b>ইউজার আইডি এবং পয়েন্ট দিন:</b>\n\nফরম্যাট: <code>User_ID Amount</code>\nউদাহরণ: <code>12345678 100</code>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_add_points)

    elif action == "admin_deduct_pts":
        msg = bot.send_message(call.message.chat.id, "➖ <b>ইউজার আইডি এবং মাইনাস করার পয়েন্ট দিন:</b>\n\nফরম্যাট: <code>User_ID Amount</code>\nউদাহরণ: <code>12345678 50</code>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_deduct_points)

    elif action == "admin_chk_user":
        msg = bot.send_message(call.message.chat.id, "🔍 <b>ইউজারের Telegram ID পাঠান:</b>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_check_user)

    elif action == "admin_ban":
        msg = bot.send_message(call.message.chat.id, "🚫 <b>ব্যান করতে ইউজারের Telegram ID পাঠান:</b>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_ban_user)

    elif action == "admin_unban":
        msg = bot.send_message(call.message.chat.id, "✅ <b>আনব্যান করতে ইউজারের Telegram ID পাঠান:</b>\n(বাতিল করতে /cancel লিখুন)")
        bot.register_next_step_handler(msg, process_unban_user)

    elif action == "admin_export":
        bot.answer_callback_query(call.id, "📤 ডাটাবেজ পাঠানো হচ্ছে...")
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "rb") as f:
                    bot.send_document(call.message.chat.id, f, caption="📁 <b>User Database Backup</b>")
            else:
                bot.send_message(call.message.chat.id, "❌ ডাটা ফাইল পাওয়া যায়নি।")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Export Error: {e}")

    elif action == "admin_apis":
        kb = types.InlineKeyboardMarkup(row_width=2)
        with api_lock:
            for idx, api in enumerate(APIS):
                status_icon = "🟢" if api.get("enabled", True) else "🔴"
                kb.add(types.InlineKeyboardButton(f"{status_icon} {api['name']}", callback_data=f"toggle_api_{idx}"))
        kb.add(types.InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back"))
        bot.edit_message_text("<b>🤖 AI ENGINE STATUS (ক্লিক করে On/Off করুন):</b>", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif action == "admin_back":
        bot.edit_message_text("<b>👑 ADMIN CONTROL PANEL</b>", call.message.chat.id, call.message.message_id, reply_markup=admin_keyboard())


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
    kb.add(types.InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back"))
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        pass


def process_add_points(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।", reply_markup=main_menu())
        return
    try:
        parts = message.text.strip().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ ফরম্যাট ভুল! লিখুন: <code>User_ID Amount</code>", reply_markup=main_menu())
            return
        uid = int(parts[0])
        amt = int(parts[1])

        new_pts = modify_user_points(uid, amt)
        bot.send_message(message.chat.id, f"✅ <b>User {uid} কে +{amt} পয়েন্ট দেওয়া হয়েছে!</b>\nবর্তমান মোট পয়েন্ট: <b>{new_pts}</b>", reply_markup=main_menu())

        try:
            bot.send_message(uid, f"🎁 <b>অ্যাডমিন আপনাকে +{amt} পয়েন্ট যুক্ত করে দিয়েছেন!</b>\n💰 আপনার বর্তমান পয়েন্ট: <b>{new_pts}</b>")
        except Exception:
            pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ সংখ্যা সঠিকভাবে দিন!", reply_markup=main_menu())


def process_deduct_points(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।", reply_markup=main_menu())
        return
    try:
        parts = message.text.strip().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ ফরম্যাট ভুল! লিখুন: <code>User_ID Amount</code>", reply_markup=main_menu())
            return
        uid = int(parts[0])
        amt = int(parts[1])

        new_pts = modify_user_points(uid, -amt)
        bot.send_message(message.chat.id, f"✅ <b>User {uid} থেকে -{amt} পয়েন্ট কাটা হয়েছে!</b>\nবর্তমান মোট পয়েন্ট: <b>{new_pts}</b>", reply_markup=main_menu())
    except ValueError:
        bot.send_message(message.chat.id, "❌ সংখ্যা সঠিকভাবে দিন!", reply_markup=main_menu())


def process_check_user(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।", reply_markup=main_menu())
        return
    try:
        uid = int(message.text.strip())
        pts = get_user_points(uid)
        refs = referral_count(uid)
        is_blk = is_blocked(uid)
        is_vrf = is_verified(uid)

        text = f"""
<b>🔍 USER DETAILS</b>
━━━━━━━━━━━━━━━━━━
🆔 User ID: <code>{uid}</code>
💰 Current Points: <b>{pts}</b>
👥 Total Referrals: <b>{refs}</b>
✅ Verified: <b>{'Yes' if is_vrf else 'No'}</b>
🚫 Blocked: <b>{'Yes' if is_blk else 'No'}</b>
━━━━━━━━━━━━━━━━━━
"""
        bot.send_message(message.chat.id, text, reply_markup=main_menu())
    except ValueError:
        bot.send_message(message.chat.id, "❌ অবৈধ User ID!", reply_markup=main_menu())


def process_broadcast(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ Broadcast বাতিল করা হয়েছে।", reply_markup=main_menu())
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
        reply_markup=main_menu()
    )


def process_ban_user(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।", reply_markup=main_menu())
        return
    try:
        target_id = int(message.text.strip())
        with data_lock:
            blocked = DATA.setdefault("blocked", [])
            if target_id not in blocked:
                blocked.append(target_id)
                save_data()
        bot.send_message(message.chat.id, f"🚫 <b>User {target_id} সফলভাবে ব্যান করা হয়েছে!</b>", reply_markup=main_menu())
    except ValueError:
        bot.send_message(message.chat.id, "❌ অবৈধ User ID!", reply_markup=main_menu())


def process_unban_user(message):
    if message.text and message.text.strip() == "/cancel":
        bot.send_message(message.chat.id, "❌ বাতিল করা হয়েছে।", reply_markup=main_menu())
        return
    try:
        target_id = int(message.text.strip())
        with data_lock:
            blocked = DATA.setdefault("blocked", [])
            if target_id in blocked:
                blocked.remove(target_id)
                save_data()
        bot.send_message(message.chat.id, f"✅ <b>User {target_id} সফলভাবে আনব্যান করা হয়েছে!</b>", reply_markup=main_menu())
    except ValueError:
        bot.send_message(message.chat.id, "❌ অবৈধ User ID!", reply_markup=main_menu())


# ============================================================
# BOT COMMANDS & NAVIGATION
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
        f"""
<b>📚 HELP CENTER</b>
━━━━━━━━━━━━━━━━━━
🤖 <b>AI CHAT:</b> প্রশ্ন লিখে পাঠান (খরচ: {COST_PER_MESSAGE} পয়েন্ট)।
🔗 <b>REFER:</b> বন্ধুদের ইনভাইট করে প্রতি রেফারে +{REFERRAL_POINTS} পয়েন্ট পান।
👤 <b>PROFILE:</b> নিজের ব্যালেন্স ও পয়েন্ট দেখুন।
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

    points = get_user_points(message.from_user.id)

    bot.send_message(
        message.chat.id,
        f"""
<b>🤖 AI CHAT MODE</b>
━━━━━━━━━━━━━━━━━━
💰 আপনার পয়েন্ট: <b>{points}</b>
💬 প্রতি মেসেজে খরচ: <b>{COST_PER_MESSAGE} Points</b>

আপনার যেকোনো প্রশ্ন এখন লিখে পাঠান।

উদাহরণ:
<code>বাংলাদেশের রাজধানী কী?</code>
<code>Python কী?</code>
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

    text = f"""
<b>👤 MY PROFILE</b>
━━━━━━━━━━━━━━━━━━
👤 Name: <b>{name}</b>
🔗 Username: <b>{html.escape(username)}</b>
🆔 Telegram ID: <code>{user.id}</code>
💰 Current Points: <b>{points} Points</b>
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
# API CALL & PARSING
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


def send_answer(chat_id, result, remaining_points):
    api_name = html.escape(result["api"])
    answer = result["answer"]
    elapsed = result["time"]

    safe_answer = html.escape(answer)

    text = (
        f"🤖 <b>{api_name}</b>\n"
        f"⚡ <b>{elapsed:.2f}s</b> | 💰 <b>বাকি পয়েন্ট: {remaining_points}</b>\n"
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
# USER TEXT HANDLER WITH POINT CHECKS
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

    # পয়েন্ট চেক (৩ পয়েন্ট আছে কি না)
    user_points = get_user_points(user_id)
    if user_points < COST_PER_MESSAGE:
        bot.send_message(
            message.chat.id,
            f"⚠️ <b>আপনার পর্যাপ্ত পয়েন্ট নেই!</b>\n\n"
            f"💰 বর্তমান পয়েন্ট: <b>{user_points}</b>\n"
            f"💬 প্রতি মেসেজে প্রয়োজন: <b>{COST_PER_MESSAGE} Points</b>\n\n"
            f"🎁 আরও পয়েন্ট পেতে আপনার রেফারেল লিংক বন্ধুদের পাঠান অথবা অ্যাডমিন {SUPPORT_USERNAME} এর সাথে যোগাযোগ করুন।",
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

    waiting = bot.send_message(chat_id, "⚡ <b>AI Processing...</b>\n\n🚀 Searching the fastest AI...")
    result = ask_ai(question)

    try:
        bot.delete_message(chat_id, waiting.message_id)
    except Exception:
        pass

    if result:
        # উত্তর সফল হলে ৩ পয়েন্ট কাটা হবে
        remaining = modify_user_points(user_id, -COST_PER_MESSAGE)

        with data_lock:
            DATA["stats"]["success"] = DATA["stats"].get("success", 0) + 1
        save_data()
        send_answer(chat_id, result, remaining)
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
# BOT RUNNER LOOP
# ============================================================

def run_bot():
    print()
    print("=" * 60)
    print("       PREMIUM MULTI AI TELEGRAM BOT + POINTS SYSTEM")
    print("=" * 60)
    print(f"Owner         : {OWNER_NAME} ({SUPPORT_USERNAME})")
    print(f"Admin ID      : {ADMIN_ID}")
    print(f"Join Bonus    : {INITIAL_POINTS} Points")
    print(f"Cost / Msg    : {COST_PER_MESSAGE} Points")
    print(f"Ref Bonus     : {REFERRAL_POINTS} Points")
    print(f"Status        : ONLINE (24/7)")
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
