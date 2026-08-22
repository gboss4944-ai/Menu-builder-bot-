import telebot
import sqlite3
import threading
import time
import os
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

# SQLite Database Connection
DB_FILE = "database.db"

def db_connect():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
admin_state = {}

def setup_database():
    db = db_connect()
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pdfs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            file_id TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS delete_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            delete_time REAL NOT NULL
        )
    """)
    db.commit()
    db.close()

setup_database()

# Start Flask server in a separate thread
threading.Thread(target=run_flask, daemon=True).start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Menu Builder Bot is up and running smoothly.")

if __name__ == '__main__':
    bot.infinity_polling()
