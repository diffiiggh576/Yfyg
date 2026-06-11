import telebot
from telebot import types
import sqlite3
import re
import os

# 🔒 GitHub Secrets থেকে টোকেন এবং আইডি অটোমেটিক নিয়ে নেবে
API_TOKEN = os.getenv('8008121647:AAF5rH0n9waO0UCye2oALM6fj3cEhKZ2yVs')  
ADMIN_ID = int(os.getenv('7275425971'))

bot = telebot.TeleBot(API_TOKEN, num_threads=4)
DB_NAME = "bot_database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT,
            number TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

FLAG_MAPPING = {
    "angola": "🇦🇴", "cameroon": "🇨🇲", "ecuador": "🇪🇨", "ethiopia": "🇪🇹",
    "ghana": "🇬🇭", "guinea": "🇬🇳", "haiti": "🇭🇹", "indonesia": "🇮🇩",
    "iraq": "🇮🇶", "jordan": "🇯🇴", "kenya": "🇰🇪", "kyrgyzstan": "🇰🇬",
    "madagascar": "🇲🇬", "mozambique": "🇲🇿", "nigeria": "🇳🇬", "pakistan": "🇵🇰",
    "palestine": "🇵🇸", "sudan": "🇸🇩", "togo": "🇹🇬", "tunisia": "🇹🇳",
    "ukraine": "🇺🇦", "uzbekistan": "🇺🇿", "zambia": "🇿🇲", "zimbabwe": "🇿🇼",
    "bangladesh": "🇧🇩", "india": "🇮🇳", "saudi arabia": "🇸🇦", "uae": "🇦🇪", "usa": "🇺🇸"
}

def get_flag(country):
    return FLAG_MAPPING.get(country.lower().strip(), "🌐")

admin_states = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ Add Numbers", "🔄 Replace Numbers", "❌ Delete Country")
        markup.add("👥 View User Menu")
        bot.send_message(chat_id, "👑 **প্রফেশনাল ওটিপি বট কন্ট্রোল প্যানেল (GitHub 24/7 Edition):**", reply_markup=markup, parse_mode='Markdown')
    else:
        show_user_countries(chat_id, is_edit=False)

def show_user_countries(chat_id, message_id=None, is_edit=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT LOWER(country) FROM numbers")
    countries = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    
    if not countries:
        text = "😔 এই মুহূর্তে ওটিপি বটে কোনো দেশের নম্বর উপলব্ধ নেই।"
        if is_edit and message_id:
            try: bot.edit_message_text(text, chat_id, message_id)
            except: pass
        else:
            bot.send_message(chat_id, text)
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for c in sorted(countries):
        flag = get_flag(c)
        buttons.append(types.InlineKeyboardButton(text=f"{flag} {c.title()}", callback_data=f"select_{c.lower().strip()}"))
    markup.add(*buttons)
    
    text = "🌍 **আপনার কাঙ্ক্ষিত দেশটি সিলেক্ট করুন:**"
    if is_edit and message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
        except Exception:
            try: bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')
            except: pass
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == "👥 View User Menu" and msg.chat.id == ADMIN_ID)
def admin_view_user(message):
    show_user_countries(message.chat.id, is_edit=False)

# ================= ADMIN ACTIONS =================

@bot.message_handler(func=lambda msg: msg.text in ["➕ Add Numbers", "🔄 Replace Numbers", "❌ Delete Country"] and msg.chat.id == ADMIN_ID)
def handle_admin_actions(message):
    action = message.text
    admin_states[ADMIN_ID] = {"action": action}
    bot.send_message(ADMIN_ID, "📝 **নম্বর যোগ করার নিয়ম:**\n\n👉 সরাসরি নম্বরগুলো মেসেজে পেস্ট করে দিন\n👉 অথবা নম্বর থাকা `.txt` ফাইলটি আপলোড করুন।", parse_mode='Markdown')

@bot.message_handler(content_types=['document'], func=lambda msg: msg.chat.id == ADMIN_ID)
def handle_admin_file(message):
    if ADMIN_ID not in admin_states or admin_states[ADMIN_ID]['action'] not in ["➕ Add Numbers", "🔄 Replace Numbers"]:
        return
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        text_content = downloaded_file.decode('utf-8').strip()
        extracted_numbers = re.findall(r'\b\d{7,15}\b', text_content)
        
        if not extracted_numbers:
            bot.reply_to(message, "❌ ফাইলে কোনো সঠিক নম্বর খুঁজে পাওয়া যায়নি!")
            return
            
        admin_states[ADMIN_ID]['temp_numbers'] = extracted_numbers
        msg = bot.send_message(ADMIN_ID, f"🎯 **ফাইল চেক সম্পন্ন!**\n\n📊 মোট নম্বর পাওয়া গেছে: `{len(extracted_numbers)}` টি।\n\n✍️ এবার দেশের নাম (Country Name) লিখুন (যেমন: Ghana, Sudan):", parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_country_name)
    except Exception as e:
        bot.reply_to(message, f"❌ ফাইল রিড করতে সমস্যা হয়েছে: {str(e)}")

@bot.message_handler(func=lambda msg: msg.chat.id == ADMIN_ID and msg.text not in ["➕ Add Numbers", "🔄 Replace Numbers", "❌ Delete Country", "👥 View User Menu"])
def handle_admin_text_numbers(message):
    if ADMIN_ID not in admin_states or admin_states[ADMIN_ID]['action'] not in ["➕ Add Numbers", "🔄 Replace Numbers"]:
        return
    try:
        text_content = message.text.strip()
        extracted_numbers = re.findall(r'\b\d{7,15}\b', text_content)
        
        if not extracted_numbers:
            bot.reply_to(message, "❌ মেসেজে কোনো সঠিক নম্বর খুঁজে পাওয়া যায়নি! আবার চেষ্টা করুন।")
            return
            
        admin_states[ADMIN_ID]['temp_numbers'] = extracted_numbers
        msg = bot.send_message(ADMIN_ID, f"🎯 **মেসেজ借েক সম্পন্ন!**\n\n📊 মোট নম্বর পাওয়া গেছে: `{len(extracted_numbers)}` টি।\n\n✍️ এবার দেশের নাম (Country Name) লিখুন (যেমন: Ghana, Sudan):", parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_country_name)
    except Exception as e:
        bot.reply_to(message, f"❌ সমস্যা হয়েছে: {str(e)}")

def process_country_name(message):
    country_name = message.text.strip().lower()
    if ADMIN_ID not in admin_states or 'temp_numbers' not in admin_states[ADMIN_ID]:
        return
        
    action = admin_states[ADMIN_ID]['action']
    numbers = admin_states[ADMIN_ID]['temp_numbers']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if action == "🔄 Replace Numbers":
        cursor.execute("DELETE FROM numbers WHERE LOWER(country) = ?", (country_name,))
        
    success_count = 0
    for num in numbers:
        cursor.execute("INSERT INTO numbers (country, number) VALUES (?, ?)", (country_name, num))
        success_count += 1
            
    conn.commit()
    conn.close()
    
    bot.send_message(ADMIN_ID, f"✅ **সফল হয়েছে!**\n\n🌍 দেশ: `{country_name.upper()}`\n📊 মোট `{success_count}` টি নম্বর ডাটাবেজে সেভ হয়েছে।", parse_mode='Markdown')
    admin_states.pop(ADMIN_ID, None)

# ================= USER CALLBACKS =================

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data == "menu_main":
        show_user_countries(chat_id, call.message.message_id, is_edit=True)
        bot.answer_callback_query(call.id)
        
    elif data.startswith("select_") or data.startswith("ref_"):
        country = data.split("_")[1].lower().strip()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, number FROM numbers WHERE LOWER(country) = ? LIMIT 3", (country,))
        rows = cursor.fetchall()
        
        if not rows:
            bot.answer_callback_query(call.id, text=f"🏁 {country.upper()} এর সব নম্বর শেষ!", show_alert=True)
            show_user_countries(chat_id, call.message.message_id, is_edit=True)
            conn.close()
            return
            
        for row in rows:
            cursor.execute("DELETE FROM numbers WHERE id = ?", (row[0],))
        conn.commit()
        conn.close()
        
        flag = get_flag(country)
        msg_lines = []
        for row in rows:
            msg_lines.append(f"📋 {flag} `{row[1]}`")
            
        final_msg = "\n\n".join(msg_lines)
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        change_btn = types.InlineKeyboardButton(text="Change Country", callback_data="menu_main")
        refresh_btn = types.InlineKeyboardButton(text="Refresh", callback_data=f"ref_{country}")
        markup.add(change_btn, refresh_btn)
        
        try:
            bot.edit_message_text(final_msg, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)
        except Exception:
            try: bot.send_message(chat_id, final_msg, parse_mode='Markdown', reply_markup=markup)
            except: pass
            
        bot.answer_callback_query(call.id)

bot.infinity_polling()
