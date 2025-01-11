import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Contact, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

API_TOKEN = "7722019620:AAEYueraVyfFRFQMuY5DBFlNJcVpIwD_iPM"
item_description = "הספר 'הארי פוטר'" 
borrow_date = "01/01/2025" 
minutes_delay = 1
# קובץ JSON לשמירת נתוני משתמשים
USERS_DATA_FILE = "users_data.json"

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# קריאת נתונים מקובץ JSON
def load_users_data():
    try:
        with open(USERS_DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# שמירת נתונים לקובץ JSON
def save_users_data():
    with open(USERS_DATA_FILE, "w") as file:
        json.dump(users_data, file)

# נתוני משתמשים
users_data = load_users_data()

# פונקציה שמטפלת בפקודת /start
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

# פונקציה שמטפלת בלחיצה על "השאלת פריט"
async def handle_borrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in users_data and "step" in users_data[user_id]:
        await update.message.reply_text(
            "⚠️ נראה שהתהליך הקודם הופסק. מתחילים מחדש."
        )
        logger.info(f"User {user_id} started a new borrowing process.")
    users_data[user_id] = {"step": "borrow_started"}
    save_users_data()
    await update.message.reply_text(
    "✨ מעולה! בחרת באפשרות 'השאלת פריט'.\n"
    "בואו נתחיל! 📸 צלם תמונה של הפריט שברצונך להשאיל."
)

# פונקציה שמטפלת בקבלת תמונה
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in users_data and users_data[user_id].get("step") == "borrow_started":
        users_data[user_id]["photo"] = update.message.photo[-1].file_id
        users_data[user_id]["step"] = "photo_received"
        save_users_data()
        logger.info(f"User {user_id} uploaded a photo.")
        await update.message.reply_text(
            "👏 תמונה התקבלה! עכשיו שלח לנו תיאור קצר של הפריט. 🖊️"
        )
    else:
        await update.message.reply_text(
            "⚠️ יש להתחיל את התהליך על ידי לחיצה על 'השאלת פריט'."
        )

# פונקציה שמטפלת בטקסט תיאור הפריט
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    step = users_data.get(user_id, {}).get("step")
    if step == "photo_received":
        users_data[user_id]["description"] = update.message.text
        save_users_data()
        logger.info(f"User {user_id} added a description.")
        keyboard = [
            [InlineKeyboardButton("📅 אחת לשבוע", callback_data="weekly")],
            [InlineKeyboardButton("📆 אחת לשבועיים", callback_data="biweekly")],
            [InlineKeyboardButton("🗓️ אחת לחודש", callback_data="monthly")],
            [InlineKeyboardButton("🚀 עכשיו", callback_data="now")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⏰ באיזו תדירות תרצה שנשלח תזכורות?", reply_markup=reply_markup
        )
    elif step == "borrow_started":
        await update.message.reply_text(
            "📸 אנא ודא ששלחת תמונה של הפריט לפני התיאור."
        )
    else:
        await update.message.reply_text(
            "⚠️ יש להתחיל את התהליך על ידי לחיצה על 'השאלת פריט'."
        )
      
# שלב 3 - תדירות שליחת ההודעה
async def handle_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if this is a callback query
    if update.callback_query:
        callback_data = update.callback_query.data
        user_id = update.callback_query.from_user.id

        if user_id in users_data:
            users_data[user_id]["frequency"] = callback_data
            save_users_data()

            # Notify user that the frequency has been saved
            await update.callback_query.answer("✔️ התדירות נשמרה בהצלחה!")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="✔️ כעת עליך להוסיף איש קשר לצ'ט."
            )
            
            # Update the step
            users_data[user_id]["step"] = "awaiting_contact"
            save_users_data()
        else:
            await update.callback_query.answer("⚠️ יש להתחיל את התהליך על ידי בחירת תדירות התזכורות.")
        return

    # Handle fallback for messages (if necessary)
    if update.message:
        await update.message.reply_text(
            "⚠️ לא התקבלה הודעה תקינה. נסה שוב מאוחר יותר."
        )

# שלב 4 - הוספת איש קשר לצ'ט
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # בדיקה אם יש מידע עבור המשתמש
    if user_id in users_data:
        user_data = users_data[user_id]

        # בדיקה אם המשתמש בשלב המתאים
        if user_data.get("step") == "awaiting_contact":
            contact = update.message.contact

            if contact and contact.phone_number:
                # שמירת מספר הטלפון
                users_data[user_id]["contact_phone"] = contact.phone_number
                users_data[user_id]["step"] = "contact_saved"
                save_users_data()
                logger.info(f"User {user_id} shared contact: {contact.phone_number}")

                # יצירת הודעת תזכורת
                reminder_message = (
                    f"שלום \n\n"
                    f"רק רצינו להזכיר לך על הפריט '{item_description}' "
                    f"שהושאל בתאריך {borrow_date}. "
                    f"בבקשה ודא שהפריט הוחזר בזמן שנקבע. "
                    f"אם עדיין לא, תוכל לתזמן תזכורת נוספת.\n\n"
                    f"נשמח לעזור בכל שאלה!\n"
                    f" צוות הבוט שלך"
                )

                # הודעה למשתמש שהמספר נשמר בהצלחה
                await update.message.reply_text("✔️ מספר הטלפון נשמר בהצלחה! נמשיך בתהליך התזכורות.")
                
                # המשך בתהליך התזכורת
                # שימוש בפונקציה המתאימה כדי להמשיך את התהליך (לדוגמה, handle_frequency)
                #await handle_frequency(update, context)

                # שליחת הודעה בוואטסאפ בפונקציה נפרדת
                await send_whatsapp_reminder(context, contact.phone_number, reminder_message)
                return
            else:
                await update.message.reply_text("⚠️ לא ניתן היה לזהות מספר טלפון. נסה שוב לשתף איש קשר.")
                return
        else:
            logger.warning(f"User {user_id} tried sharing contact but is not in awaiting_contact step.")
    
    # אם המשתמש לא נמצא במצב המתאים או אין מידע
    await update.message.reply_text("⚠️ יש להתחיל את התהליך על ידי בחירת תדירות התזכורות.")

# שלב 5 - שליחת הודעת התזכורת למספר של איש הקשר דרך ווצאפ ווב
async def send_whatsapp_reminder(context: ContextTypes.DEFAULT_TYPE, contact_phone: str, reminder_message: str) -> None:
    success = send_whatsapp_message(contact_phone, reminder_message, delay_minutes=minutes_delay)
    if success:
        await context.bot.send_message(
            chat_id=context.job.context,
            text="✔️ הודעת תזכורת נשלחה בהצלחה דרך WhatsApp."
        )
    else:
        await context.bot.send_message(
            chat_id=context.job.context,
            text="⚠️ הייתה בעיה בשליחת הודעת התזכורת דרך WhatsApp. נסה שוב מאוחר יותר."
        )

import pywhatkit
from datetime import datetime, timedelta

# פונקציה לשליחת הודעה בוואטסאפ
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



# הוספת פונקציות הבוט למסגרת האפליקציה
application = Application.builder().token(API_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📚 השאלת פריט$"), handle_borrow))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
application.add_handler(CallbackQueryHandler(handle_frequency))
application.add_handler(MessageHandler(filters.CONTACT, handle_contact))


# הפעלת הבוט
if __name__ == "__main__":
    logger.info("Bot is starting...")
    application.run_polling()
