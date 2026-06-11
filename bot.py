import telebot
from telebot import types
import os

# ⚠️ সরাসরি টোকেন ও আইডি বসানোর ঘর
API_TOKEN = '8008121647:AAF5rH0n9waO0UCye2oALM6fj3cEhKZ2yVs'  # এখানে আপনার বটের আসল টোকেন দিন
ADMIN_ID = 7275425971  # এখানে আপনার আসল টেলিগ্রাম আইডি দিন

bot = telebot.TeleBot(API_TOKEN, num_threads=4)

# ডাটাবেজের বদলে সরাসরি টেক্সট ফাইল দিয়ে নম্বর ম্যানেজ করার ফোল্ডার
DATA_DIR = "bot_numbers"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

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

def get_countries_with_numbers():
    if not os.path.exists(DATA_DIR):
        return []
    files = os.listdir(DATA_DIR)
    countries = []
    for f in files:
        if f.endswith(".txt"):
            filepath = os.path.join(DATA_DIR, f)
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                with open(filepath, "r", encoding="utf-8") as file:
                    lines = [l.strip() for l in file.readlines() if l.strip()]
                    if lines:
                        countries.append(f[:-4])
    return sorted(countries)

admin_states = {}

# ================= COMMAND HANDLERS =================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ Add Numbers (Paste Text)", "❌ Delete Country")
        markup.add("👥 View User Menu")
        bot.send_message(chat_id, "👑 **ওটিপি বট কন্ট্রোল প্যানেল (GitHub File Edition):**", reply_markup=markup, parse_mode='Markdown')
    else:
        show_user_countries(chat_id, is_edit=False)

def show_user_countries(chat_id, message_id=None, is_edit=False):
    countries = get_countries_with_numbers()
    
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
    for c in countries:
        flag = get_flag(c)
        buttons.append(types.InlineKeyboardButton(text=f"{flag} {c.title()}", callback_data=f"select_{c.lower().strip()}"))
    markup.add(*buttons)
    
    text = "🌍 **আপনার কাঙ্ক্ষিত দেশটি সিলেক্ট করুন:**"
    if is_edit and message_id:
        try: bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
        except: pass
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == "👥 View User Menu" and msg.chat.id == ADMIN_ID)
def admin_view_user(message):
    show_user_countries(message.chat.id, is_edit=False)

# ================= ADMIN ACTIONS =================

@bot.message_handler(func=lambda msg: msg.text in ["➕ Add Numbers (Paste Text)", "❌ Delete Country"] and msg.chat.id == ADMIN_ID)
def handle_admin_actions(message):
    action = message.text
    if action == "➕ Add Numbers (Paste Text)":
        admin_states[ADMIN_ID] = {"action": "add"}
        bot.send_message(ADMIN_ID, "✍️ প্রথমে দেশের নাম লিখুন (যেমন: Ghana, Sudan, India):")
    elif action == "❌ Delete Country":
        countries = get_countries_with_numbers()
        if not countries:
            bot.send_message(ADMIN_ID, "❌ ডিলিট করার মতো কোনো দেশ নেই।")
            return
        markup = types.InlineKeyboardMarkup()
        for c in countries:
            markup.add(types.InlineKeyboardButton(text=f"🗑️ Delete {c.upper()}", callback_data=f"del_{c.lower().strip()}"))
        bot.send_message(ADMIN_ID, "কোন দেশের সব নম্বর ডিলিট করতে চান সিলেক্ট করুন:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.chat.id == ADMIN_ID and ADMIN_ID in admin_states)
def handle_admin_input(message):
    state = admin_states[ADMIN_ID]
    if "country" not in state:
        country_name = message.text.strip().lower()
        admin_states[ADMIN_ID]["country"] = country_name
        bot.send_message(ADMIN_ID, f"📋 দেশ সিলেক্ট হয়েছে: `{country_name.upper()}`\n\nএবার নম্বরগুলো সরাসরি মেসেজে কপি-পেস্ট করে পাঠিয়ে দিন:", parse_mode='Markdown')
    else:
        country_name = state["country"]
        text_content = message.text.strip()
        import re
        extracted_numbers = re.findall(r'\b\d{7,15}\b', text_content)
        
        if not extracted_numbers:
            bot.reply_to(message, "❌ কোনো সঠিক নম্বর খুঁজে পাওয়া যায়নি! আবার নম্বরগুলো পেস্ট করুন।")
            return
            
        filepath = os.path.join(DATA_DIR, f"{country_name}.txt")
        with open(filepath, "a", encoding="utf-8") as f:
            for num in extracted_numbers:
                f.write(f"{num}\n")
                
        bot.send_message(ADMIN_ID, f"✅ **সফল হয়েছে!**\n🌍 দেশ: `{country_name.upper()}`\n📊 মোট `{len(extracted_numbers)}` টি নম্বর যুক্ত হয়েছে।", parse_mode='Markdown')
        admin_states.pop(ADMIN_ID, None)

# ================= USER CALLBACKS =================

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data.startswith("del_") and chat_id == ADMIN_ID:
        country_to_del = data.split("_")[1].lower().strip()
        filepath = os.path.join(DATA_DIR, f"{country_to_del}.txt")
        if os.path.exists(filepath):
            os.remove(filepath)
        bot.edit_message_text(f"🗑️ {country_to_del.upper()} এর সব নম্বর মুছে ফেলা হয়েছে।", chat_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        
    elif data == "menu_main":
        show_user_countries(chat_id, call.message.message_id, is_edit=True)
        bot.answer_callback_query(call.id)
        
    elif data.startswith("select_") or data.startswith("ref_"):
        country = data.split("_")[1].lower().strip()
        filepath = os.path.join(DATA_DIR, f"{country}.txt")
        
        if not os.path.exists(filepath):
            bot.answer_callback_query(call.id, text=f"🏁 {country.upper()} এর সব নম্বর শেষ!", show_alert=True)
            show_user_countries(chat_id, call.message.message_id, is_edit=True)
            return
            
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            
        if not lines:
            bot.answer_callback_query(call.id, text=f"🏁 {country.upper()} এর সব নম্বর শেষ!", show_alert=True)
            show_user_countries(chat_id, call.message.message_id, is_edit=True)
            return
            
        # একসাথে ৩টি নম্বর রিলিজ করা
        released_numbers = lines[:3]
        remaining_numbers = lines[3:]
        
        with open(filepath, "w", encoding="utf-8") as f:
            for num in remaining_numbers:
                f.write(f"{num}\n")
                
        flag = get_flag(country)
        msg_lines = [f"📋 {flag} `{num}`" for num in released_numbers]
        final_msg = "\n\n".join(msg_lines)
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(text="Change Country", callback_data="menu_main"),
            types.InlineKeyboardButton(text="Refresh", callback_data=f"ref_{country}")
        )
        
        try: bot.edit_message_text(final_msg, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)
        except Exception: pass
        bot.answer_callback_query(call.id)

bot.infinity_polling()
