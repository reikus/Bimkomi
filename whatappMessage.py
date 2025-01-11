from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Contact, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import webbrowser
import pywhatkit

API_TOKEN = "7722019620:AAEYueraVyfFRFQMuY5DBFlNJcVpIwD_iPM"

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
    if user_id not in users_data:
        users_data[user_id] = {}
    await update.message.reply_text(
        "✨ מעולה! בחרת באפשרות 'השאלת פריט'. בואו נתחיל!"
    )
    await update.message.reply_text(
        "📸 צלם תמונה של הפריט שברצונך להשאיל והמשך בתהליך. 😊"
    )

# פונקציה שמטפלת בקבלת תמונה
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    users_data[user_id] = {"photo": update.message.photo[-1].file_id}  # שמירת התמונה
    await update.message.reply_text(
        "👏 תמונה התקבלה! עכשיו שלח לנו תיאור קצר של הפריט. 🖊️"
    )

# פונקציה שמטפלת בטקסט תיאור הפריט
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in users_data and "photo" in users_data[user_id]:
        users_data[user_id]["description"] = update.message.text

        # תפריט תדירות תזכורות
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
        await update.message.reply_text(
            "📸 אנא ודא ששלחת תמונה של הפריט לפני התיאור."
        )

# פונקציה שמטפלת בבחירת תדירות התזכורות
async def handle_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id in users_data:
        users_data[user_id]["frequency"] = query.data
        
        if query.data == "now":
            contact_phone = users_data[user_id].get("contact_phone", "לא צוין")
            description = users_data[user_id].get("description", "לא צוין")
            borrow_date = users_data[user_id].get("borrow_date", "לא צוין")

            message = (
                f"📢 תזכורת נעימה עבורך!\n\n"
                f"🔹 פריט: {description}\n"
                f"📅 תאריך השאלה: {borrow_date}\n"
                f"👤 השאלת ממך: {contact_phone}"
            )

            try:
                pywhatkit.sendwhatmsg_instantly(contact_phone, message)
                await query.edit_message_text(
                    "🚀 הודעת התזכורת נשלחה בהצלחה! תודה על השימוש בבוט שלנו."
                )
            except Exception as e:
                await query.edit_message_text(
                    f"⚠️ שגיאה בשליחת ההודעה: {str(e)}"
                )
        else:
            await query.edit_message_text(
                "📥 הבחירה נשמרה! נשלח תזכורות בהתאם לתדירות שבחרת."
            )
    else:
        await query.edit_message_text(
            "⚠️ אנא נסה שנית. לא נמצאו נתונים."
        )

# הוספת פונקציות הבוט למסגרת האפליקציה
application = Application.builder().token(API_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
application.add_handler(CallbackQueryHandler(handle_frequency))

application.run_polling()
