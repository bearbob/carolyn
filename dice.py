from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from random import randint


def roll_dice(bot, update):
    keyboard = [[InlineKeyboardButton(text="D6", callback_data='dice6'),
                 InlineKeyboardButton(text="D10", callback_data='dice10')],
                [InlineKeyboardButton(text="D20", callback_data='dice20'),
                 InlineKeyboardButton(text="D100", callback_data='dice100')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def dice_twenty(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=randint(1, 20))
