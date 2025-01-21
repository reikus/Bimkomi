from datetime import datetime, timedelta
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Contact, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import sqlite3
import pywhatkit
import os
from telegram import Bot



# Telegram API Token
API_TOKEN = os.getenv("7722019620:AAEYueraVyfFRFQMuY5DBFlNJcVpIwD_iPM")
bot = Bot(token=API_TOKEN)
bot.set_webhook(f"https://dashboard.heroku.com/apps/bimkomi/{API_TOKEN}")
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
            frequency TEXT NOT NULL,
            photo_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'borrowed'
        )''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

# Add item to the database
def add_item(user_id, item_description, borrow_date, contact_phone, frequency, photo_id):
    conn = sqlite3.connect("borrow_reminders.db")
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO items (user_id, item_description, borrow_date, contact_phone, frequency, photo_id, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', (user_id, item_description, borrow_date, contact_phone, frequency, photo_id, 'borrowed'))
    conn.commit()
    conn.close()

# Update item status (borrowed or returned)
def update_item_status(user_id, item_description, returned=False):
    conn = sqlite3.connect("borrow_reminders.db")
    cursor = conn.cursor()
    status = "returned" if returned else "borrowed"
    cursor.execute('''UPDATE items SET status = ? WHERE user_id = ? AND item_description = ?''', (status, user_id, item_description))
    conn.commit()
    conn.close()

# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton("📚 השאלת פריט")],
        [KeyboardButton("🔍 פריט הוחזר")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "😀 ברוכים הבאים לבוט שלנו! בחרו את האפשרות המתאימה לכם:", 
        reply_markup=markup
    )

async def handle_borrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    context.user_data[user_id] = {"step": "borrow_started"}
    
    # שלח הודעה עם טקסט ומקש
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

# Handle frequency selection
async def handle_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        callback_data = update.callback_query.data
        user_id = update.callback_query.from_user.id
        
        # בדוק אם המשתמש עבר את כל השלבים הדרושים לפני שמאחסן את המידע
        if user_id in context.user_data and "step" in context.user_data[user_id] and context.user_data[user_id]["step"] == "photo_received":
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
        else:
            # אם המשתמש לא עבר את השלבים הקודמים
            await update.callback_query.answer("⚠️ עליך להשלים את שלב התמונה והתיאור לפני קביעת תדירות.")

# Handle the contact info submission
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if context.user_data[user_id].get("step") == "awaiting_contact":
        contact = update.message.contact
        
        if contact and contact.phone_number:
            phone_number = contact.phone_number
            if phone_number.startswith("05"):
                phone_number = "+972" + phone_number[1:]
            # Send confirmation and reminder message
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=("✔️ איש הקשר נשמר בהצלחה!\n"
                      "ההודעה תישלח לאיש הקשר בהתאם לתדירות שבחרת.\n"
                      )
            )
            item_description = context.user_data[user_id]["item_description"]
            borrow_date = context.user_data[user_id]["borrow_date"]
            frequency = context.user_data[user_id]["frequency"]
            photo_id = context.user_data[user_id]["photo"]

            add_item(user_id, item_description
                     , borrow_date, phone_number, frequency, photo_id)
            print(f"Inserting into items: user_id={user_id}, item_description={item_description}, "
            f"borrow_date={borrow_date}, contact_phone={phone_number}, frequency={frequency}, photo_id={photo_id}")

            reminder_message = (
                f"שלום\n\n"
                f"רצינו להזכיר לך להחזיר את הפריט '{item_description}' "
                f"שהושאל בתאריך {borrow_date}.\n"
                f"נשמח לעזור בכל שאלה!\n\n"
                f"צוות במקומי"
            )
  
            # Send WhatsApp reminder
            await send_whatsapp_reminder(context, update.effective_chat.id, phone_number, reminder_message)

            # Update step after the contact handling
            context.user_data[user_id]["step"] = "completed"

# Handle item return (Upload item photo)
async def return_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    await update.message.reply_text(
            f"👀 "
            "אנא העלה את התמונה של הפריט שהחזרת."
        )
    context.user_data[user_id]["step"] = "return_started"
    photo_id, item_description = item
        
    
    # Search for borrowed items
    conn = sqlite3.connect("borrow_reminders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT photo_id, item_description FROM items WHERE user_id = ? AND status = 'borrowed'", (user_id,))
    item = cursor.fetchone()
    conn.close()

    if item:
        photo_id, item_description = item
        await update.message.reply_text(
            f"👀 הנה התמונה של הפריט '{item_description}' שהשאלת:\n"
            "אנא העלה את התמונה של הפריט שהחזרת."
        )
        await update.message.reply_photo(photo_id)
    else:
        await update.message.reply_text(
            "⚠️ לא הצלחנו למצוא את הפריט שהשאלת. ייתכן שלא שמרנו את התמונה. אנא שלח לנו את שם הפריט שהחזרת."
        )


# Handle the photo upload for item return
async def handle_photo_for_return(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if context.user_data[user_id].get("step") == "return_started":
        uploaded_photo_id = update.message.photo[-1].file_id

        # Compare uploaded photo with saved item photo
        conn = sqlite3.connect("borrow_reminders.db")
        cursor = conn.cursor()
        cursor.execute("SELECT item_description FROM items WHERE user_id = ? AND photo_id = ?", (user_id, uploaded_photo_id))
        item = cursor.fetchone()
        conn.close()

        if item:
            item_description = item[0]
            update_item_status(user_id, item_description, returned=True)

            await update.message.reply_text(
                f"✔️ הפריט '{item_description}' הוחזר בהצלחה!\n\n"
                "תודה על העדכון! תזכורות ההחזרה עבור פריט זה לא יישלחו יותר. אם יש פריטים אחרים להחזיר, "
                "תוכל לשלוח הודעה נוספת בכל עת."
            )
        
        else:
            await update.message.reply_text(
                "⚠️ לא הצלחנו לזהות את הפריט שהתמונה שלך תואמת אליו. אנא וודא שהעלית את התמונה הנכונה."
            )

# WhatsApp reminder
async def send_whatsapp_reminder(context, chat_id, phone_number, reminder_message):
    pywhatkit.sendwhatmsg_instantly(phone_number, reminder_message, 10, True)

# Main function to run the bot
def main():
    init_db()

    application = Application.builder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("📚 השאלת פריט"), handle_borrow))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    application.add_handler(CallbackQueryHandler(handle_frequency))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.Regex("🔍 פריט הוחזר"), return_item))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    application.run_polling()

if __name__ == "__main__":
    main()
