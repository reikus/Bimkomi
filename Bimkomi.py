from datetime import datetime, timedelta
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Contact, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import sqlite3
import pywhatkit
#
# Telegram API Token
API_TOKEN = "7722019620:AAEYueraVyfFRFQMuY5DBFlNJcVpIwD_iPM"

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# SQLite database setup
def init_db():
    try:
        conn = sqlite3.connect("borrow_reminders.db")
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_description TEXT NOT NULL,
            borrow_date TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            frequency TEXT NOT NULL
        )''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    db_path = r"C:\Users\Administrator\source\repos\Bimkomi\borrow_reminders.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        item_description TEXT NOT NULL,
        borrow_date TEXT NOT NULL,
        contact_phone TEXT NOT NULL,
        frequency TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

# Add item to the database
def add_item(user_id, item_description, borrow_date, contact_phone, frequency):
    conn = sqlite3.connect("borrow_reminders.db")
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO items (user_id, item_description, borrow_date, contact_phone, frequency)
                      VALUES (?, ?, ?, ?, ?)''', (user_id, item_description, borrow_date, contact_phone, frequency))
    conn.commit()
    conn.close()

# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton("📚 השאלת פריט")],
        [KeyboardButton("🔍 פרט הוחזר")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "😀 ברוכים הבאים לבוט שלנו! בחרו את האפשרות המתאימה לכם:", 
        reply_markup=markup
    )

async def handle_borrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    context.user_data[user_id] = {"step": "borrow_started"}
    await update.message.reply_text(
        "✨ מעולה! בחרת באפשרות 'השאלת פריט'.\n"
        "בואו נתחיל! 📸 צלם תמונה של הפריט שברצונך להשאיל."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in context.user_data and context.user_data[user_id].get("step") == "borrow_started":
        context.user_data[user_id]["photo"] = update.message.photo[-1].file_id
        context.user_data[user_id]["step"] = "photo_received"
        await update.message.reply_text(
            "👏 תמונה התקבלה! עכשיו שלח לנו תיאור קצר של הפריט. 🖊️"
        )
    else:
        await update.message.reply_text(
            "⚠️ יש להתחיל את התהליך על ידי לחיצה על 'השאלת פריט'."
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    step = context.user_data.get(user_id, {}).get("step")
    if step == "photo_received":
        context.user_data[user_id]["item_description"] = update.message.text
        today_date = datetime.now().strftime("%d/%m/%Y")
        context.user_data[user_id]["borrow_date"] = today_date

        keyboard = [
            [InlineKeyboardButton("📅 אחת לשבוע", callback_data="weekly")],
            [InlineKeyboardButton("📆 אחת לשבועיים", callback_data="biweekly")],
            [InlineKeyboardButton("🗓️ אחת לחודש", callback_data="monthly")],
            [InlineKeyboardButton("🚀 עכשיו", callback_data="now")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "✔️ התיאור נשמר בהצלחה! \n\n"
            "עכשיו נוכל להמשיך לשלב הבא 😊\n"
            "⏰ באיזו תדירות תרצה שנשלח תזכורות?", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "⚠️ יש להתחיל את התהליך על ידי לחיצה על 'השאלת פריט'."
        )

# Update handle_frequency function
async def handle_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        callback_data = update.callback_query.data
        user_id = update.callback_query.from_user.id

        context.user_data[user_id]["frequency"] = callback_data

        frequency_map = {
            "weekly": "אחת לשבוע",
            "biweekly": "אחת לשבועיים",
            "monthly": "אחת לחודש",
            "now": "עכשיו"
        }
        selected_frequency = frequency_map.get(callback_data, "לא נבחרה תדירות")
        await update.callback_query.answer("✔️ התדירות נשמרה בהצלחה!")
        
        reminder_message = (
            f"שלום\n\n"
            f"רצינו להזכיר לך להחזיר את הפריט '{context.user_data[user_id]['item_description']}' "
            f"שהושאל בתאריך {context.user_data[user_id]['borrow_date']}.\n"
            f"נשמח לעזור בכל שאלה!\n\n"
            f"צוות במקומי"
        )
        
        # Send frequency selection confirmation with reminder message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "✔️ התדירות נשמרה בהצלחה! \n"
                f"נבחרה תדירות: {selected_frequency}.\n\n"
                "ההודעה שתשלח לאיש הקשר:\n" 
                f"{reminder_message}\n\n"
                "אנא הוסף איש קשר לצ'ט כדי שנוכל לשלוח לו את תזכורות ההחזרה.\n\n"      
            )
        )
        
        # Proceed to next step
        context.user_data[user_id]["step"] = "awaiting_contact"


# Update handle_contact function
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if context.user_data[user_id].get("step") == "awaiting_contact":
        contact = update.message.contact
        if contact and contact.phone_number:
            phone_number = contact.phone_number
            if phone_number.startswith("05"):
                phone_number = "+972" + phone_number[1:]

            item_description = context.user_data[user_id]["item_description"]
            borrow_date = context.user_data[user_id]["borrow_date"]
            frequency = context.user_data[user_id]["frequency"]

            add_item(user_id, item_description, borrow_date, phone_number, frequency)

            reminder_message = (
                f"שלום\n\n"
                f"רצינו להזכיר לך להחזיר את הפריט '{item_description}' "
                f"שהושאל בתאריך {borrow_date}.\n"
                f"נשמח לעזור בכל שאלה!\n\n"
                f"צוות במקומי"
            )
                        # Notify user that the contact has been added and reminder will be sent
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "✔️ איש הקשר נשמר בהצלחה!\n"
                    "ההודעה תישלח לאיש הקשר בהתאם לתדירות שנבחרה.\n"
                    f"נשלח תזכורת ל-{phone_number} בעת הצורך."
                )
            )
            
            # Send WhatsApp reminder
            await send_whatsapp_reminder(context, update.effective_chat.id, phone_number, reminder_message)

            # Update step after the contact handling
            context.user_data[user_id]["step"] = "completed"




async def send_whatsapp_reminder(context: ContextTypes.DEFAULT_TYPE, chat_id: int, phone_number: str, reminder_message: str) -> None:
    success = send_whatsapp_message(phone_number, reminder_message, delay_minutes=1)
    if success:
        await context.bot.send_message(
            chat_id=chat_id,
            text="✔️ הודעת תזכורת נשלחה בהצלחה דרך WhatsApp."
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ הייתה בעיה בשליחת הודעת התזכורת דרך WhatsApp. נסה שוב מאוחר יותר."
        )

def send_whatsapp_message(phone_number: str, message: str, delay_minutes: int = 1) -> bool:
    now = datetime.now()
    send_time = now + timedelta(minutes=delay_minutes)
    hour, minute = send_time.hour, send_time.minute
    try:
        pywhatkit.sendwhatmsg(phone_number, message, hour, minute)
        logger.info(f"WhatsApp message sent to {phone_number} at {hour}:{minute}.")
        return True
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message to {phone_number}: {e}")
        return False

# Initialize the database
init_db()

# Set up the bot
application = Application.builder().token(API_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📚 השאלת פריט$"), handle_borrow))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
application.add_handler(CallbackQueryHandler(handle_frequency))
application


# Start the bot
if __name__ == "__main__":
    logger.info("Bot is starting...")
    application.run_polling()
