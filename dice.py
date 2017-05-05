from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from random import randint


def roll_dice(bot, update):
    keyboard = [[InlineKeyboardButton(text="D6", callback_data='6'),
                 InlineKeyboardButton(text="D10", callback_data='10')],
                [InlineKeyboardButton(text="D20", callback_data='20'),
                 InlineKeyboardButton(text="D100", callback_data='100')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def dice_twenty(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=randint(1, 20))


def button(bot, update):
    query = update.callback_query
    reply = "Rolling one D{0}... Got {1}."
    bot.editMessageText(text=reply.format(query.data, randint(1, int(query.data))),
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id)
