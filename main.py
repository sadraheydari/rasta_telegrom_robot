from utils import keyboards, patterns, constants, states

import logging
import json
import requests
import re

from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext as Context
from telegram import (InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (
    Updater, CommandHandler, MessageHandler,
    Filters, ConversationHandler, CallbackQueryHandler
)


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update: Update, context: Context):
    update.message.reply_text(
        """سلام! به ربات نمره ‌دهی رستا خوش‌آمدید...
        برای شروع لازمه اطلاعات کاربری مربوط به سایت رو وارد کنید.
        در هر لحظه از اگر به مشکلی برخورد کردید با دستور /cancel ربات رو خاموش کنید و دوباره از اول کار رو شروع کنید
        """,
        reply_markup= keyboards.login_panel()
    )
    return states.LOGIN


def login(update: Update, context: Context):
    query = update.callback_query
    query.edit_message_text(text= "Loging in...")
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Username:"
    )
    return states.GET_USERNAME


def get_username(update: Update, context: Context):
    username = update.message.text
    context.user_data['username'] = username
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Password:"
    )
    return states.GET_PASSWORD


def get_password(update: Update, context: Context):
    context.user_data['password'] = update.message.text.lower()
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Connecting to server..."
    )
    username, password = context.user_data['username'], context.user_data['password']
    r = requests.post(
        url= constants.SERVER_URL + "authenticate",
        json= {"username": username, "password": password}
    )
    code = r.status_code
    if code == 200:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Connected successfully."
        )
        context.user_data['token'] = r.json()['token']
                
        update.message.reply_text(
            """
            کدوم کارگاه؟
            """,
            reply_markup=keyboards.field_selection()
        )
        return states.SELECT_FIELD
    elif code == 401:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Wrong Username or Password. Use /start command to try again."
        )
        return states.END
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Can't connect to server! try again using /start command."
        )
        return states.END


def send_connection_error_msg(update: Update, context: Context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="ارتباط با سرور دچار خطا شده است. لطفا ربات را با دستور /cancel خاموش و دوباره روشن کنید."
    )
    return states.END


def handle_expired_token(update: Update, context: Context, func):
    username, password = context.user_data['username'], context.user_data['password']
    r = requests.post(
        url= constants.SERVER_URL + "authenticate",
        json= {"username": username, "password": password}
    )
    if r.status_code != 200:
        return send_connection_error_msg(update, context)
    context.user_data['token'] = r.json()['token']

    return func(update, context)


def get_field(update: Update, context: Context):
    query = update.callback_query
    query.answer()
    
    if query.data == "exit":
        query.edit_message_text(
            text = "یا موفقیت خارج شدید. برای ورود مجدد از دکمه زیر استفاده کنید.",
            reply_markup = keyboards.login_panel()
        )
        return states.LOGIN
        
    token = context.user_data["token"]
    r = requests.get(
        url= f"https://game.rastaiha.ir/api/institute/answers/{query.data}",
        headers= {'Authorization' : 'Bearer ' + token, 'Content-Type': 'application/json'}
    )
    code = r.status_code
    if code == 401:
        return handle_expired_token(update, constants, get_field)
    if code!= 200:
        return send_connection_error_msg(update, context)

    query.edit_message_text(text= f"{len(r.json())} پاسخ در انتظار تصحیح")
    if len(r.json()) == 0:
        context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = "ادامه",
            reply_markup = keyboards.countinue_keyboard()
        )
        return states.SCORE_Q
    
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="لیست پاسخ‌ها",
        reply_markup= keyboards.answer_list(r.json())
    )
    return states.SELECT_Q


def get_q(update: Update, context: Context):
    query = update.callback_query
    query.answer()
    q_id = query.data
    token = context.user_data['token']
    r = requests.get(
        url = constants.SERVER_URL + "api/institute/" + q_id,
        headers= {'Authorization' : 'Bearer ' + token, 'Content-Type': 'application/json'}
    )
    if r.status_code == 401:
        return handle_expired_token(update, context, get_q)
    if r.status_code != 200:
        return send_connection_error_msg(update, context)

    fileName = r.json()['fileName']
    link = constants.SERVER_URL + "file/download/answer/" + fileName
    
    query.edit_message_text(
        text = link
    )
    
    if patterns.is_pdf(fileName):
        context.bot.send_document(
            chat_id = update.effective_chat.id,
            document = link,
            reply_markup = keyboards.score(q_id)
        )
    elif patterns.is_img(fileName):
        context.bot.send_photo(
            chat_id = update.effective_chat.id,
            photo = link,
            reply_markup = keyboards.score(fileName)
        )
    else:
        query.edit_message_text(
            text = link,
            reply_markup = keyboards.score(fileName)
        )

    return states.SCORE_Q


def score(update: Update, context: Context):
    query = update.callback_query
    query.answer()
    
    if query.data == "continue":
        query.edit_message_text(
            text = """
            کدوم کارگاه؟
            """,
            reply_markup=keyboards.field_selection()
        )
        return states.SELECT_FIELD
    
    result, q_id = bool(query.data[0]), query.data[2:]
    r = requests.post(
        url= constants.SERVER_URL + "api/institute/mark/" + q_id,
        headers= {'Authorization' : 'Bearer ' + context.user_data['token'], 'Content-Type': 'application/json'},
        json = {"mark": result}
    )
    code = r.status_code
    if code == 401:
        return handle_expired_token(update, context, score)
    if code != 200:
        return send_connection_error_msg(update, context)

    query.edit_message_text("نمره با موفقیت ثبت شد.")
    context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = """
        کدوم کارگاه؟
        """,
        reply_markup=keyboards.field_selection()
    )
    return states.SELECT_FIELD


def cancel(update: Update, context: Context):
    context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = "ربات با موفقیت خاموش شد. برای را‌اندازی مجدد از دستور /start استفاده کنید."
    )
    return states.END



def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(constants.BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            states.LOGIN: [CallbackQueryHandler(login), CommandHandler('cancel', cancel)],

            states.GET_USERNAME: [MessageHandler(Filters.text & ~Filters.command, get_username), CommandHandler('cancel', cancel)],

            states.GET_PASSWORD: [MessageHandler(Filters.text & ~Filters.command, get_password), CommandHandler('cancel', cancel)],
            
            states.SELECT_FIELD: [CallbackQueryHandler(get_field), CommandHandler('cancel', cancel)],
            
            states.SELECT_Q: [CallbackQueryHandler(get_q), CommandHandler('cancel', cancel)],
            
            states.SCORE_Q: [CallbackQueryHandler(score), CommandHandler('cancel', cancel)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == "__main__":
    main()