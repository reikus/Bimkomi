from datetime import datetime
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

# פ
# ונקציה שמטפלת בקבלת תמונה
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
        # Store the description as item_description
        users_data[user_id]["item_description"] = update.message.text

        # Default the borrow_date to today's date
        today_date = datetime.now().strftime("%d/%m/%Y")
        users_data[user_id]["borrow_date"] = today_date

        save_users_data()
        logger.info(f"User {user_id} added a description and borrow date.")
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

            # Mapping frequency to a nice readable format
            frequency_map = {
            "weekly": "אחת לשבוע",
            "biweekly": "אחת לשבועיים",
            "monthly": "אחת לחודש",
            "now": "עכשיו"
            }
                # Get the user-selected frequency
            selected_frequency = frequency_map.get(callback_data, "לא נבחרה תדירות")
            # Notify user that the frequency has been saved
            await update.callback_query.answer("✔️ התדירות נשמרה בהצלחה!")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
            text=(
                    "✔️ התדירות נשמרה בהצלחה! \n"
                    f"נבחרה תדירות: {selected_frequency}.\n\n"
                    "עכשיו נוכל להמשיך לשלב הבא 😊\n"
                    "אנא הוסף איש קשר לצ'ט כדי שנוכל לשלוח לו את תזכורות ההחזרה."
                )  
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

    # Check if there is user data
    if user_id in users_data:
        user_data = users_data[user_id]

        # Ensure the user is at the correct step
        if user_data.get("step") == "awaiting_contact":
            contact = update.message.contact

            if contact and contact.phone_number:
                # Normalize the phone number
                phone_number = contact.phone_number
                if phone_number.startswith("05"):
                    phone_number = "+972" + phone_number[1:]

                # Save the contact phone number
                users_data[user_id]["contact_phone"] = phone_number
                users_data[user_id]["step"] = "contact_saved"
                save_users_data()
                logger.info(f"User {user_id} shared contact: {phone_number}")

                # Retrieve item_description and borrow_date from user data
                item_description = user_data["item_description"]
                borrow_date = user_data["borrow_date"]

                # Create the reminder message
                reminder_message = (
                    f"שלום\n\n"
                    f"רצינו להזכיר לך להחזיר את הפריט '{item_description}' "
                    f"שהושאל בתאריך {borrow_date}.\n"
                    f"נשמח לעזור בכל שאלה!\n\n"
                    f"צוות במקומי"
                )

                # Notify the user that the phone number was saved successfully
                await update.message.reply_text("✔️ מספר הטלפון נשמר בהצלחה! בעוד מספר רגעים נאשר את שליחת ההודעה בהצלחה, תודה על סבלנותך.")

                # Send the WhatsApp reminder
                await send_whatsapp_reminder(context, update.effective_chat.id, phone_number, reminder_message)
                return
            else:
                await update.message.reply_text("⚠️ לא ניתן היה לזהות מספר טלפון. נסה שוב לשתף איש קשר.")
                return
        else:
            logger.warning(f"User {user_id} tried sharing contact but is not in awaiting_contact step.")
    
    # If the user is not in the correct step or there is no user data
    await update.message.reply_text("⚠️ יש להתחיל את התהליך על ידי בחירת תדירות התזכורות.")

# Send WhatsApp reminder function
async def send_whatsapp_reminder(context: ContextTypes.DEFAULT_TYPE, chat_id: int, phone_number: str, reminder_message: str) -> None:
    # This assumes send_whatsapp_message is defined elsewhere
    success = send_whatsapp_message(phone_number, reminder_message, delay_minutes=minutes_delay)
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
