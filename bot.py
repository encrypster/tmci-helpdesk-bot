import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# 🔑 BOT TOKEN
TOKEN = "8140774538:AAHiYw_wt_pOy9TJtDuj2A7ALnQ-3kvK_fk"
ADMINS = [7573063287]  # Admin Telegram ID-larini qo‘shing

# 📂 SQLite bazani yaratish
conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        status TEXT DEFAULT 'open',
        created_by TEXT NOT NULL
    )
""")
conn.commit()

# 🏁 /start - Botni ishga tushirish
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "👋 Assalomu alaykum! IT vazifalarni boshqarish botiga xush kelibsiz. 🚀\n"
        "🔹 Yangi vazifa qo‘shish: `/newtask Tavsif`\n"
        "🔹 Vazifalar ro‘yxati: `/tasks`\n"
        "🔹 O‘z vazifalaringizni ko‘rish: `/mytasks`\n"
        "🔹 Vazifani bajarildi deb belgilash: tugma orqali 🔘\n"
        "🔹 Vazifani o‘chirish: `/delete ID` (faqat adminlar)"
    )

# ➕ /newtask - Yangi vazifa qo‘shish
async def new_task(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("❌ Iltimos, vazifa tavsifini kiriting.")
        return

    task_desc = " ".join(context.args)
    created_by = update.message.from_user.username or update.message.from_user.first_name
    
    cursor.execute("INSERT INTO tasks (task, created_by) VALUES (?, ?)", (task_desc, created_by))
    conn.commit()

    await update.message.reply_text(f"✅ Vazifa qo‘shildi:\n📌 *{task_desc}*", parse_mode="Markdown")

# 📜 /tasks - Barcha vazifalarni ko‘rish
async def list_tasks(update: Update, context: CallbackContext):
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()

    if not tasks:
        await update.message.reply_text("📂 Hozircha hech qanday vazifa yo‘q.")
        return

    for task in tasks:
        task_id, task_desc, status, created_by = task
        status_emoji = "🟢 Ochiq" if status == "open" else "✅ Bajarildi"
        
        keyboard = [[InlineKeyboardButton("✅ Bajarildi", callback_data=f"done_{task_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🔹 *ID:* {task_id}\n📌 *Vazifa:* {task_desc}\n📌 *Holat:* {status_emoji}\n📌 *Kim yaratdi:* {created_by}",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

# 🔍 /mytasks - Foydalanuvchining o‘z vazifalari
async def my_tasks(update: Update, context: CallbackContext):
    username = update.message.from_user.username or update.message.from_user.first_name
    cursor.execute("SELECT * FROM tasks WHERE created_by = ?", (username,))
    tasks = cursor.fetchall()

    if not tasks:
        await update.message.reply_text("📂 Sizning vazifalaringiz yo‘q.")
        return

    message = f"📋 *{username} uchun vazifalar:*\n"
    for task in tasks:
        task_id, task_desc, status, _ = task
        status_emoji = "🟢 Ochiq" if status == "open" else "✅ Bajarildi"
        message += f"\n🔹 *ID:* {task_id}\n📌 *Vazifa:* {task_desc}\n📌 *Holat:* {status_emoji}\n"

    await update.message.reply_text(message, parse_mode="Markdown")

# ✅ Inline tugma bosilganda vazifani bajarilgan deb belgilash
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("done_"):
        task_id = int(query.data.split("_")[1])
        cursor.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,))
        conn.commit()
        await query.edit_message_text(f"✅ *Vazifa bajarildi!*", parse_mode="Markdown")

# ❌ /delete - Vazifani o‘chirish (faqat adminlar)
async def delete_task(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("🚫 Sizga bu amalni bajarishga ruxsat yo‘q!")
        return

    if not context.args:
        await update.message.reply_text("❌ Iltimos, o‘chiriladigan vazifaning ID sini kiriting. Masalan:\n`/delete 2`", parse_mode="Markdown")
        return

    try:
        task_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID noto‘g‘ri! Masalan:\n`/delete 2`", parse_mode="Markdown")
        return

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    await update.message.reply_text(f"🗑 *Vazifa o‘chirildi!*", parse_mode="Markdown")

# 🔄 Botni ishga tushirish
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newtask", new_task))
    app.add_handler(CommandHandler("tasks", list_tasks))
    app.add_handler(CommandHandler("mytasks", my_tasks))
    app.add_handler(CommandHandler("delete", delete_task))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
