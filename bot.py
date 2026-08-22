import telebot
import psycopg2
import threading
import time
import os
from urllib.parse import urlparse
from telebot import types
from flask import Flask

# Dummy web server for Render port check
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

BOT_TOKEN = "8883200935:AAENl0wiCSeZAZuaSPxtUlRHhGVbgLo106s"
ADMIN_IDS = {8346926801, 6714126072}
DELETE_AFTER = 3 * 60 * 60

def db_connect():
    return psycopg2.connect(
        dbname="postgres",
        user="postgres.sliizidimtqvpbotgmhk",
        password="qwer12334ty2179",
        host="aws-0-ap-south-1.pooler.supabase.com",
        port=6543
    )
    def db_connect():
    return psycopg2.connect(
        dbname="postgres",
        user="postgres.sliizidimtqvpbotgmhk",
        password="qwer12334ty2179",
        host="aws-0-ap-south-1.pooler.supabase.com",
        port=6543
    )

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
        port=result.port
    )

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
admin_state = {}

def setup_database():
    db = db_connect()
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pdfs (
            id SERIAL PRIMARY KEY,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            file_id TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS delete_queue (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NULL,
            message_id BIGINT NOT NULL,
            delete_at BIGINT NOT NULL
        )
    """)
    db.commit()
    cur.close()
    db.close()

def is_admin(user_id):
    return user_id in ADMIN_IDS

def add_category(name):
    db = db_connect()
    cur = db.cursor()
    cur.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
    db.commit()
    cur.close()
    db.close()

def get_categories():
    db = db_connect()
    cur = db.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY id")
    result = cur.fetchall()
    cur.close()
    db.close()
    return result

def delete_category(category_id):
    db = db_connect()
    cur = db.cursor()
    cur.execute("DELETE FROM pdfs WHERE category_id = %s", (category_id,))
    cur.execute("DELETE FROM categories WHERE id = %s", (category_id,))
    db.commit()
    cur.close()
    db.close()

def add_pdf(category_id, name, file_id):
    db = db_connect()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO pdfs (category_id, name, file_id)
        VALUES (%s, %s, %s)
    """, (category_id, name, file_id))
    db.commit()
    cur.close()
    db.close()

def get_pdfs(category_id):
    db = db_connect()
    cur = db.cursor()
    cur.execute("""
        SELECT id, name FROM pdfs
        WHERE category_id = %s
        ORDER BY id
    """, (category_id,))
    result = cur.fetchall()
    cur.close()
    db.close()
    return result

def get_pdf(pdf_id):
    db = db_connect()
    cur = db.cursor()
    cur.execute("""
        SELECT id, category_id, name, file_id FROM pdfs
        WHERE id = %s
    """, (pdf_id,))
    result = cur.fetchone()
    cur.close()
    db.close()
    return result

def delete_pdf(pdf_id):
    db = db_connect()
    cur = db.cursor()
    cur.execute("DELETE FROM pdfs WHERE id = %s", (pdf_id,))
    db.commit()
    cur.close()
    db.close()

def save_delete_message(chat_id, message_id):
    delete_at = int(time.time()) + DELETE_AFTER
    db = db_connect()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO delete_queue (chat_id, message_id, delete_at)
        VALUES (%s, %s, %s)
    """, (chat_id, message_id, delete_at))
    db.commit()
    cur.close()
    db.close()

def show_home(chat_id, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    categories = get_categories()

    for category_id, name in categories:
        markup.add(
            types.InlineKeyboardButton(
                "📚 " + name, callback_data="cat_" + str(category_id)
            )
        )

    text = (
        "☰ <b>Welcome to NEETWARRIORTEAM</b> ✨\n\n"
        "Welcome to <b>NEETWARRIORTEAM</b>! ❤️\n\n"
        "Tap the button below to access the <b>Study Material</b>. 📚\n\n"
        "⚠️ <b>Important:</b> Please save/download the required PDFs, as all PDF messages will be <b>automatically deleted after 3 hours</b>. ⏳"
    )

    if message_id is None:
        bot.send_message(chat_id, text, reply_markup=markup)
    else:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)

@bot.message_handler(commands=["start"])
def start(message):
    show_home(message.chat.id)

def show_admin_panel(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Add Category", callback_data="add_category")
    )
    markup.add(
        types.InlineKeyboardButton(
            "📂 Manage Categories", callback_data="manage_categories"
        )
    )

    bot.send_message(
        chat_id,
        "🔐 <b>NEETWARRIORTEAM ADMIN PANEL</b>\n\nChoose an action below:",
        reply_markup=markup,
    )

@bot.message_handler(commands=["admin"])
def admin_cmd(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ You are not authorized.")
        return
    show_admin_panel(message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data

    if data == "home":
        show_home(chat_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("cat_"):
        cat_id = int(data.split("_")[1])
        pdfs = get_pdfs(cat_id)

        markup = types.InlineKeyboardMarkup(row_width=1)
        for pdf_id, name in pdfs:
            markup.add(
                types.InlineKeyboardButton(
                    "📄 " + name, callback_data="pdf_" + str(pdf_id)
                )
            )

        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="home"))

        text = (
            "📚 <b>Select a Chapter / Material</b>\n\n"
            "Choose a PDF from below to view/download."
        )

        bot.edit_message_text(
            text, chat_id, call.message.message_id, reply_markup=markup
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("pdf_"):
        pdf_id = int(data.split("_")[1])
        pdf = get_pdf(pdf_id)

        if pdf:
            file_id = pdf[3]
            name = pdf[2]

            msg = bot.send_document(
                chat_id,
                file_id,
                caption=(
                    f"📄 <b>{name}</b>\n\n"
                    "⚠️ <i>This file will automatically delete in 3 hours.</i>"
                ),
            )
            save_delete_message(chat_id, msg.message_id)
            bot.answer_callback_query(call.id, text="Sent!")
        else:
            bot.answer_callback_query(call.id, text="PDF not found.")
        return

    if not is_admin(user_id):
        bot.answer_callback_query(call.id, text="Unauthorized action.")
        return

    if data == "admin_panel":
        admin_state.pop(user_id, None)
        show_admin_panel(chat_id)
        bot.answer_callback_query(call.id)
        return

    if data == "add_category":
        admin_state[user_id] = {"action": "wait_cat_name"}
        bot.send_message(
            chat_id,
            "📌 Send me the name for the new Category:",
            reply_markup=types.ForceReply(),
        )
        bot.answer_callback_query(call.id)
        return

    if data == "manage_categories":
        categories = get_categories()
        markup = types.InlineKeyboardMarkup(row_width=1)

        for cat_id, name in categories:
            markup.add(
                types.InlineKeyboardButton(
                    "⚙️ " + name, callback_data="mcat_" + str(cat_id)
                )
            )

        markup.add(
            types.InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")
        )
        bot.send_message(
            chat_id, "📂 Select a category to manage:", reply_markup=markup
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("mcat_"):
        cat_id = int(data.split("_")[1])
        markup = types.InlineKeyboardMarkup(row_width=1)

        markup.add(
            types.InlineKeyboardButton(
                "➕ Add PDF", callback_data="addpdf_" + str(cat_id)
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "📄 Manage PDFs", callback_data="mpdfs_" + str(cat_id)
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "❌ Delete Category", callback_data="delcat_" + str(cat_id)
            )
        )
        markup.add(
            types.InlineKeyboardButton("🔙 Back", callback_data="manage_categories")
        )

        bot.send_message(chat_id, "⚙️ Category Management:", reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("addpdf_"):
        cat_id = int(data.split("_")[1])
        admin_state[user_id] = {"action": "wait_pdf_name", "cat_id": cat_id}
        bot.send_message(
            chat_id,
            "📌 Send me the display title for this PDF:",
            reply_markup=types.ForceReply(),
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("mpdfs_"):
        cat_id = int(data.split("_")[1])
        pdfs = get_pdfs(cat_id)

        markup = types.InlineKeyboardMarkup(row_width=1)
        for pdf_id, name in pdfs:
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Delete " + name, callback_data="delpdf_" + str(pdf_id)
                )
            )

        markup.add(
            types.InlineKeyboardButton("🔙 Back", callback_data="mcat_" + str(cat_id))
        )
        bot.send_message(
            chat_id, "📄 Select a PDF to delete:", reply_markup=markup
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("delcat_"):
        cat_id = int(data.split("_")[1])
        delete_category(cat_id)
        bot.send_message(chat_id, "✅ Category and its PDFs deleted!")
        show_admin_panel(chat_id)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("delpdf_"):
        pdf_id = int(data.split("_")[1])
        delete_pdf(pdf_id)
        bot.send_message(chat_id, "✅ PDF deleted successfully!")
        show_admin_panel(chat_id)
        bot.answer_callback_query(call.id)
        return

@bot.message_handler(
    content_types=["text", "document"],
    func=lambda msg: msg.from_user.id in admin_state,
)
def handle_admin_input(message):
    user_id = message.from_user.id
    state = admin_state.get(user_id)

    if not state:
        return

    action = state.get("action")

    if action == "wait_cat_name":
        if message.text:
            add_category(message.text.strip())
            bot.reply_to(
                message, f"✅ Category '<b>{message.text.strip()}</b>' added!"
            )
            admin_state.pop(user_id, None)
            show_admin_panel(message.chat.id)
        else:
            bot.reply_to(message, "❌ Please send a text name.")

    elif action == "wait_pdf_name":
        if message.text:
            admin_state[user_id] = {
                "action": "wait_pdf_file",
                "cat_id": state["cat_id"],
                "pdf_name": message.text.strip(),
            }
            bot.reply_to(
                message,
                f"✅ Title saved as '<b>{message.text.strip()}</b>'. Now send/forward the PDF document:",
            )
        else:
            bot.reply_to(message, "❌ Please send a valid text title.")

    elif action == "wait_pdf_file":
        if message.document:
            file_id = message.document.file_id
            cat_id = state["cat_id"]
            pdf_name = state["pdf_name"]

            add_pdf(cat_id, pdf_name, file_id)
            bot.reply_to(
                message,
                f"🎉 PDF '<b>{pdf_name}</b>' uploaded and saved successfully!",
            )
            admin_state.pop(user_id, None)
            show_admin_panel(message.chat.id)
        else:
            bot.reply_to(
                message, "❌ That was not a document! Please send/forward a PDF file."
            )

def auto_deleter():
    while True:
        try:
            now = int(time.time())
            db = db_connect()
            cur = db.cursor()
            cur.execute(
                "SELECT id, chat_id, message_id FROM delete_queue WHERE delete_at <= %s",
                (now,),
            )
            rows = cur.fetchall()

            for row_id, chat_id, message_id in rows:
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception as e:
                    pass
                cur.execute("DELETE FROM delete_queue WHERE id = %s", (row_id,))
                db.commit()

            cur.close()
            db.close()
        except Exception as e:
            pass
        time.sleep(30)

if __name__ == "__main__":
    setup_database()

    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=auto_deleter, daemon=True).start()

    bot.infinity_polling(skip_pending=True)
