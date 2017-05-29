import sqlite3
import constants
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def add(bot, update, args):
    # start a new event. args contains the event name, next check which groups are eligable
    # select all known group chats the user is a member of
    select_groups = "SELECT chatId, chatTitle FROM Messages WHERE userId = {0} AND chatId < 0 GROUP BY chatId;"
    query = select_groups.format(update.message.from_user.id)
    buttons = []
    try:
        conn = sqlite3.connect(constants.db)
        c = conn.cursor()
        data = c.execute(query).fetchall()

        for row in data:
            cb = 'chat' + str(row[0])
            buttons.append(InlineKeyboardButton(text=row[1], callback_data=cb))
        c.close()
        conn.close()
    except sqlite3.Error as e:
        print(e, " in ", query)

    if len(buttons) < 1:
        ans = "No groups available. Please add me to a group first."
        bot.sendMessage(chat_id=update.message.chat_id, text=ans)
        return
    keyboard = [buttons]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose a chat:', reply_markup=reply_markup)
