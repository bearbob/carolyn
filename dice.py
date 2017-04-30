from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from random import randint


def roll_dice(bot, update):
    keyboard = [[InlineKeyboardButton("D6", callback_data='6'),
                 InlineKeyboardButton("D10", callback_data='10')],

                [InlineKeyboardButton("D20", callback_data='20')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def button(bot, update):
    query = update.callback_query
    reply = "Rolling one D{0}... Got {1}."
    bot.editMessageText(text=reply.format(query.data, randint(1, int(query.data))),
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id)
