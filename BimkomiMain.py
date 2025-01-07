from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Contact, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import pywhatkit

API_TOKEN = "7722019620:AAEYueraVyfFRFQMuY5DBFlNJcVpIwD_iPM"  # הכנס כאן את הטוקן שלך

users_data = {}

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
    users_data[user_id] = {"step": "borrow_started"}  # התחלת תהליך חדש
    await update.message.reply_text(
        "✨ מעולה! בחרת באפשרות 'השאלת פריט'. בואו נתחיל! 📸 צלם תמונה של הפריט שברצונך להשאיל."
    )

# פונקציה שמטפלת בקבלת תמונה
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if users_data.get(user_id, {}).get("step") == "borrow_started":
        users_data[user_id]["photo"] = update.message.photo[-1].file_id
        users_data[user_id]["step"] = "photo_received"
        await update.message.reply_text("👏 תמונה התקבלה! עכשיו שלח לנו תיאור קצר של הפריט.")
    else:
        await update.message.reply_text("⚠️ יש להתחיל את התהליך על ידי לחיצה על 'השאלת פריט'.")

# פונקציה שמטפלת בתיאור טקסט
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if users_data.get(user_id, {}).get("step") == "photo_received":
        users_data[user_id]["description"] = update.message.text
        users_data[user_id]["step"] = "description_received"
        await request_phone(update, context)
    else:
        await update.message.reply_text("⚠️ אנא ודא ששלחת תמונה של הפריט לפני תיאור.")

# פונקציה שמבקשת מספר טלפון
async def request_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton("📱 שתף מספר טלפון", request_contact=True)]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "📞 אנא שתף את מספר הטלפון של איש הקשר לו אתה משאיל את הפריט:", 
        reply_markup=markup
    )

# פונקציה שמטפלת במספר טלפון
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    contact = update.message.contact
    if contact and contact.phone_number:
        phone_number = contact.phone_number
        if phone_number.startswith("05"):
            phone_number = "+972" + phone_number[1:]
        users_data[user_id]["contact_phone"] = phone_number
        users_data[user_id]["step"] = "phone_received"

        # בקשת תדירות התזכורות
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
    else:
        await update.message.reply_text("⚠️ לא התקבל מספר טלפון. נסה שוב.")

# פונקציה שמטפלת בבחירת תדירות תזכורות
async def handle_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id in users_data:
        users_data[user_id]["frequency"] = query.data
        contact_phone = users_data[user_id].get("contact_phone")
        description = users_data[user_id].get("description")
        message = (
            f"📢 תזכורת נעימה עבורך!\n\n"
            f"🔹 פריט: {description}\n"
            f"👤 איש קשר: {contact_phone}"
        )

        if query.data == "now":
            try:
                pywhatkit.sendwhatmsg_instantly(contact_phone, message)
                await query.edit_message_text("🚀 הודעת התזכורת נשלחה בהצלחה!")
            except Exception as e:
                await query.edit_message_text(f"⚠️ שגיאה בשליחת ההודעה: {str(e)}")
        else:
            await query.edit_message_text("📥 הבחירה נשמרה! נשלח תזכורות בהתאם לתדירות.")
    else:
        await query.edit_message_text("⚠️ לא נמצאו נתונים. אנא נסה שוב.")

# הוספת פונקציות הבוט למסגרת האפליקציה
application = Application.builder().token(API_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
application.add_handler(CallbackQueryHandler(handle_frequency))

application.run_polling()
