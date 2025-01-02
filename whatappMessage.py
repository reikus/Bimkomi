import telebot
import pywhatkit

API_TOKEN = "7722019620:AAEYueraVyfFRFQMuY5DBFlNJcVpIwD_iPM"

bot = telebot.TeleBot(API_TOKEN)

users_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "ברוך הבא לבוט! שלח לי את מספר הטלפון בפורמט: /send + מספר טלפון")

@bot.message_handler(commands=['send'])
def ask_for_contact(message):
    user_id = message.from_user.id
    phone_number = "+972508377456"
    users_data[user_id] = {'phone_number': phone_number}
    bot.reply_to(message, "שלח לי את ההודעה שתרצה לשלוח בווצאפ")

@bot.message_handler(func=lambda message: message.from_user.id in users_data)
def send_whatsapp_message(message):
    user_id = message.from_user.id
    whatsapp_message = message.text
    phone_number = users_data[user_id]['phone_number']

    try:
        pywhatkit.sendwhatmsg_instantly(phone_number, whatsapp_message)
        bot.reply_to(message, "ההודעה נשלחה בהצלחה!")
        del users_data[user_id]
    except Exception as e:
        bot.reply_to(message, f"שגיאה בשליחת ההודעה: {str(e)}")

bot.polling()
