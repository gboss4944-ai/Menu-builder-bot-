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

DATABASE_URL = "postgresql://postgres.sliizidimtqvpbotgmhk:qwer12334ty2179@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"

def db_connect():
    result = urlparse(DATABASE_URL)
    return psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
admin_state = {}

def db_connect():
    return psycopg2.connect(DATABASE_URL)

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
        markup.add(types.InlineKeyboardButton("📚 " + name, callback_data="cat_" + str(category_id)))

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
    markup.add(types.InlineKeyboardButton("➕ Add Category", callback_data="add_category"))
    markup.add(types.InlineKeyboardButton("📂 Manage Categories", callback_data="manage_categories"))

    bot.send_message(
        chat_id,
        "🔐 <b>NEETWARRIORTEAM ADMIN PANEL</b>\n\nChoose an option:",
        reply_markup=markup
    )

@bot.message_handler(commands=["admin"])
def admin(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ <b>Access Denied.</b>")
        return
    show_admin_panel(message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    user_id = call.from_user.id
    data = call.data

    if data.startswith("admin_") or data.startswith("add_") or data.startswith("manage_") or data.startswith("delete_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Not authorized.", show_alert=True)
            return

    if data.startswith("cat_"):
        category_id = int(data.split("_")[1])
        pdfs = get_pdfs(category_id)

        markup = types.InlineKeyboardMarkup(row_width=1)
        for pdf_id, name in pdfs:
            markup.add(types.InlineKeyboardButton("📄 " + name, callback_data="pdf_" + str(pdf_id)))

        if not pdfs:
            markup.add(types.InlineKeyboardButton("📭 No PDFs Available", callback_data="nothing"))

        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="home"))

        bot.edit_message_text(
            "📚 <b>Select the PDF you want:</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("pdf_"):
        pdf_id = int(data.split("_")[1])
        pdf = get_pdf(pdf_id)

        if not pdf:
            bot.answer_callback_query(call.id, "❌ PDF not found.", show_alert=True)
            return

        pdf_name = pdf[2]
        file_id = pdf[3]

        try:
            sent = bot.send_document(
                call.message.chat.id,
                file_id,
                caption=f"📄 <b>{pdf_name}</b>\n\n⏳ This message will be automatically deleted after 3 hours."
            )
            save_delete_message(call.message.chat.id, sent.message_id)
            bot.answer_callback_query(call.id, "📄 PDF sent!")
        except Exception as e:
            print("PDF SEND ERROR:", e)
            bot.answer_callback_query(call.id, "❌ Could not send PDF.", show_alert=True)
        return

    if data == "home":
        show_home(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if data == "add_category":
        admin_state[user_id] = {"state": "category"}
        bot.send_message(user_id, "➕ <b>Add Category</b>\n\nSend the category name.")
        bot.answer_callback_query(call.id)
        return

    if data == "manage_categories":
        categories = get_categories()
        markup = types.InlineKeyboardMarkup(row_width=1)

        for category_id, name in categories:
            markup.add(types.InlineKeyboardButton("📂 " + name, callback_data="manage_" + str(category_id)))

        markup.add(types.InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_home"))

        bot.edit_message_text(
            "📂 <b>Manage Categories</b>\n\nSelect a category:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
        return

    if data == "admin_home":
        show_admin_panel(user_id)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("manage_"):
        category_id = int(data.split("_")[1])
        category_name = "Category"
        for cid, name in get_categories():
            if cid == category_id:
                category_name = name
                break

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("➕ Add PDF", callback_data="addpdf_" + str(category_id)))
        markup.add(types.InlineKeyboardButton("📄 Manage PDFs", callback_data="viewpdf_" + str(category_id)))
        markup.add(types.InlineKeyboardButton("🗑 Delete Category", callback_data="delcat_" + str(category_id)))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="manage_categories"))

        bot.edit_message_text(
            f"📂 <b>{category_name}</b>\n\nChoose an option:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("addpdf_"):
        category_id = int(data.split("_")[1])
        admin_state[user_id] = {"state": "pdf", "category_id": category_id}
        bot.send_message(user_id, "➕ <b>Add PDF</b>\n\nSend the PDF now.\n\nThe original PDF filename will automatically become the button name.")
        bot.answer_callback_query(call.id)
        return

    if data.startswith("viewpdf_"):
        category_id = int(data.split("_")[1])
        pdfs = get_pdfs(category_id)

        markup = types.InlineKeyboardMarkup(row_width=1)
        for pdf_id, name in pdfs:
            markup.add(types.InlineKeyboardButton("🗑 " + name, callback_data="delpdf_" + str(pdf_id)))

        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="manage_" + str(category_id)))

        text = "📄 <b>No PDFs in this category.</b>" if not pdfs else "📄 <b>Manage PDFs</b>\n\nTap a PDF to delete it:"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("delpdf_"):
        pdf_id = int(data.split("_")[1])
        pdf = get_pdf(pdf_id)
        if not pdf:
            bot.answer_callback_query(call.id, "PDF not found.", show_alert=True)
            return

        category_id = pdf[1]
        delete_pdf(pdf_id)
        bot.answer_callback_query(call.id, "✅ PDF deleted.")

        pdfs = get_pdfs(category_id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        for pid, name in pdfs:
            markup.add(types.InlineKeyboardButton("🗑 " + name, callback_data="delpdf_" + str(pid)))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="manage_" + str(category_id)))

        bot.edit_message_text("📄 <b>Manage PDFs</b>", call.message.chat.id, call.message.message_id, reply_markup=markup)
        return

    if data.startswith("delcat_"):
        category_id = int(data.split("_")[1])
        delete_category(category_id)
        bot.answer_callback_query(call.id, "✅ Category deleted.")
        show_admin_panel(user_id)
        return

    if data == "nothing":
        bot.answer_callback_query(call.id, "Nothing available.")

@bot.message_handler(content_types=["text", "document"])
def admin_messages(message):
    user_id = message.from_user.id
    if not is_admin(user_id) or user_id not in admin_state:
        return

    state = admin_state[user_id]

    if state["state"] == "category":
        if message.content_type != "text":
            bot.reply_to(message, "❌ Send the category name as text.")
            return
        name = message.text.strip()
        if not name:
            bot.reply_to(message, "❌ Category name cannot be empty.")
            return

        add_category(name)
        del admin_state[user_id]
        bot.send_message(user_id, f"✅ <b>Category added!</b>\n\n📂 {name}")
        show_admin_panel(user_id)
        return

    if state["state"] == "pdf":
        if message.content_type != "document":
            bot.reply_to(message, "❌ Please send a PDF file.")
            return

        document = message.document
        filename = document.file_name or "Unnamed PDF"

        if not (document.mime_type == "application/pdf" or filename.lower().endswith(".pdf")):
            bot.reply_to(message, "❌ Only PDF files are allowed.")
            return

        add_pdf(state["category_id"], filename, document.file_id)
        del admin_state[user_id]
        bot.send_message(user_id, f"✅ <b>PDF added successfully!</b>\n\n📄 {filename}")
        show_admin_panel(user_id)
        return

def delete_worker():
    while True:
        now = int(time.time())
        try:
            db = db_connect()
            cur = db.cursor()
            cur.execute("SELECT chat_id, message_id FROM delete_queue WHERE delete_at <= %s", (now,))
            rows = cur.fetchall()

            for chat_id, message_id in rows:
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception as e:
                    print("Delete error:", e)
                cur.execute("DELETE FROM delete_queue WHERE chat_id = %s AND message_id = %s", (chat_id, message_id))
            db.commit()
            cur.close()
            db.close()
        except Exception as e:
            print("DB Worker Error:", e)

        time.sleep(30)

if __name__ == "__main__":
    setup_database()
    threading.Thread(target=delete_worker, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()
    print("NEETWARRIORTEAM BOT IS RUNNING WITH SUPABASE")
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
