import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import pywhatkit
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Contact
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

API_TOKEN = "7722019620:AAEYueraVyfFRFQMuY5DBFlNJcVpIwD_iPM"

bot = telebot.TeleBot(API_TOKEN)

users_data = {}

# הפונקציה שמטפלת בפקודת /start של טלגרם
def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("השאלת פריט"))
    markup.add(KeyboardButton("פריט הוחזר"))
    update.message.reply_text("בחר אחת מהאפשרויות:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "השאלת פריט")
def handle_borrow(message):
    bot.send_message(message.chat.id, "בחרת באפשרות 'השאלת פריט'.")
    bot.send_message(message.chat.id, "📸 צלם את הפריט שברצונך להשאיל והתחל את התהליך.")

# פונקציה שמטפלת בקבלת תמונה
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    global users_data
    users_data[user_id] = {"photo": update.message.photo[-1].file_id}  # שמירת התמונה
    await update.message.reply_text("📋 תודה! עכשיו בבקשה, כתוב תיאור קצר של הפריט שברצונך להשאיל.")

# פונקציה שמטפלת בתיאור הטקסט
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    global users_data
    if user_id in users_data and "photo" in users_data[user_id]:
        users_data[user_id]["description"] = update.message.text  # שמירת התיאור

        # שליחת תפריט לבחירת תדירות
        keyboard = [
            [InlineKeyboardButton("אחת לשבוע", callback_data="weekly")],
            [InlineKeyboardButton("אחת לשבועיים", callback_data="biweekly")],
            [InlineKeyboardButton("אחת לחודש", callback_data="monthly")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🕒 בחר את תדירות שליחת התזכורת (בשעה 20:00):", reply_markup=reply_markup)
    else:
        await update.message.reply_text("📸 קודם עליך לשלוח תמונה של הפריט. נסה שוב.")

# פונקציה שמטפלת בבחירת תדירות התזכורת
async def handle_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    global users_data

    if user_id in users_data:
        users_data[user_id]["frequency"] = query.data

        # בקשת איש קשר
        await query.edit_message_text("📱 אנא שלח את איש הקשר של מי שאתה משאיל לו את הפריט. לחץ על 'צרף איש קשר' בתחתית הצ'אט.")
    else:
        await query.edit_message_text("⚠️ לא נמצא מידע על הפריט שלך. אנא התחל את התהליך שוב.")

# פונקציה שמטפלת בקבלת איש קשר
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    global users_data

    if user_id in users_data and "frequency" in users_data[user_id]:
        contact: Contact = update.message.contact
        users_data[user_id]["contact"] = {
            "name": contact.first_name,
            "phone_number": contact.phone_number,
        }
        # החלפת קידומת מספר טלפון
        if contact.phone_number.startswith('0'):
            contact.phone_number = '+972' + contact.phone_number[1:]
        
         # הודעת סיכום
        reminder_message = (
            f"📌 *תזכורת להשאלת פריט:*\n"
            f"**פריט:** {users_data[user_id]['description']}\n"
            f"**תדירות תזכורת:** {users_data[user_id]['frequency']}\n"
            f"**איש קשר:** {contact.first_name} ({contact.phone_number})\n\n"
            f"🔔 *התזכורות ישלחו אליך בשעה 20:00 בהתאם לתדירות שנבחרה.*"
        )
        
        await update.message.reply_text(
            f"🎉 *תהליך ההשאלה הושלם בהצלחה!*\n\n"
            f"📄 *פרטי התהליך:*\n"
            f"**פריט:** {users_data[user_id]['description']}\n"
            f"**תדירות תזכורת:** {users_data[user_id]['frequency']}\n"
            f"**איש קשר:** {contact.first_name} ({contact.phone_number})\n\n"
            f"✉️ *תזכורת מעוצבת למשלוח:*\n"
            f"{reminder_message}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("⚠️ לא התקבלו כל הנתונים הנדרשים. אנא התחל את התהליך מחדש.")

@bot.message_handler(func=lambda message: message.text == "פריט הוחזר")
def handle_return(message):
    bot.send_message(message.chat.id, "בחרת באפשרות 'פריט הוחזר'.")
    # כאן תוכל להוסיף את הקוד הרלוונטי לטיפול בהחזרת פריט

def main():
    # יצירת אובייקט האפליקציה
    application = Application.builder().token(API_TOKEN).build()

    # הוספת המטפלים לפקודות
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(handle_frequency))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # התחלת הפולינג
    application.run_polling()

if __name__ == "__main__":
    main()
