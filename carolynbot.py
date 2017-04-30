#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import sqlite3
import dice
import logging
import random
import credentials
import answer
import setup

# set some global vars
db = "log.db"


def checkuser(user):
    id = user.id
    first = user.first_name
    last = user.last_name
    name = user.username
    sql = "INSERT INTO Users(userId, userName, firstName, lastName) SELECT {0}, '{1}', '{2}', '{3}'  WHERE NOT EXISTS("
    sql += "SELECT 1 FROM Users WHERE userId = {0})"
    query = sql.format(id, name, first, last)
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute(query)
        c.close()
        conn.close()
    except sqlite3.Error as e:
        print(e, " in ", query)


def wordprocess(text, userId):
    hashtags = 0
    if len(text) < 1:
        return hashtags
    words = text.split()
    for word in words:
        if word.startswith('#'):
            hashtags += 1
        # add word to database after formatting
        nw = word.lower()
        for char in [',', '.', '!', '"', '?', ' ', '“', '/']:
            nw = nw.replace(char, '')
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('INSERT INTO Words (userId, word) VALUES (?, ?)', (userId, nw.lower()))
        c.close()
        conn.close()

    return hashtags


def text(bot, update):
    conn = sqlite3.connect(db)
    typus = 'Text'
    content = update.message.text
    chatId = update.message.chat_id
    try:
        chatName = update.message.chat.title
    except AttributeError:
        chatName = ''
    userId = update.message.from_user.id
    checkuser(update.message.from_user)
    time = update.message.date
    print(typus, ":", update.message)
    try:
        ans = update.message.reply_to_message.from_user.id
        checkuser(update.message.reply_to_message.from_user)
    except AttributeError:
        ans = 0
    try:
        forward = update.message.forward_from.id
        checkuser(update.message.forward_from)
    except AttributeError:
        forward = 0

    # process the words and count the hashtags
    hashtags = wordprocess(content, userId)

    sql = "INSERT INTO Messages(chatId, chatTitle, userId, unixtime, type, answerTo, forwardFrom, hashtags, content) "
    sql += "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
    try:
        c = conn.cursor()
        c.execute(sql, (chatId, chatName, userId, time, typus, ans, forward, hashtags, content))
        c.close()
    except sqlite3.Error as e:
        print(e, " in ", sql)

    conn.commit()
    conn.close()

    if "carolyn" in content or "Carolyn" in content:
        if "?" in content:
            ans = random.choice(answer.getAnswer())
        else:
            pool = [
                "Yes, master?",
                "At your service.",
                "How can I help?",
                "Is there something you wish to know?",
                "Speak.",
                "Yes?",
                "Why are you disturbing me?",
                "Leave me alone.",
                "What bothers you?"
                    ]
            ans = random.choice(pool)
        bot.sendMessage(chat_id=update.message.chat_id, text=ans)


def handleother(update, typ):
    global conn
    conn = sqlite3.connect(db)
    content = update.message.caption
    content += update.message.text
    chatId = update.message.chat_id
    try:
        chatName = update.message.chat.title
    except AttributeError:
        chatName = ''
    userId = update.message.from_user.id
    checkuser(update.message.from_user)
    time = update.message.date
    print(typ, ":", update.message)
    try:
        answer = update.message.reply_to_message.from_user.id
        checkuser(update.message.reply_to_message.from_user)
    except AttributeError:
        answer = 0
    try:
        forward = update.message.forward_from.id
        checkuser(update.message.forward_from)
    except AttributeError:
        forward = 0

    # process the words and count the hashtags
    hashtags = wordprocess(content, userId)

    sql = "INSERT INTO Messages(chatId, chatTitle, userId, unixtime, type, answerTo, forwardFrom, hashtags, content) "
    sql += "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
    try:
        c = conn.cursor()
        c.execute(sql, (chatId, chatName, userId, time, typ, answer, forward, hashtags, content))
        c.close()
    except sqlite3.Error as e:
        print(e, " in ", sql)

    conn.commit()
    conn.close()


def picture(bot, update):
    typus = 'Picture'
    handleother(update, typus)


def audio(bot, update):
    typus = 'Audio'
    handleother(update, typus)


def document(bot, update):
    try:
        if update.message.document.file_name.endswith(".mp4"):
            if update.message.document.file_name == 'giphy.mp4':
                typus = 'GIF'
            else:
                typus = 'Video'
    except AttributeError:
        typus = 'Document'
    handleother(update, typus)


def location(bot, update):
    typus = 'Location'
    handleother(update, typus)


def sticker(bot, update):
    typus = 'Sticker'
    handleother(update, typus)


def video(bot, update):
    typus = 'Video'
    handleother(update, typus)


def voice(bot, update):
    typus = 'Voice'
    handleother(update, typus)


def stats(bot, update, args):
    print(args)
    monthPool = True
    if "all" in args or "total" in args:
        monthPool = False
        sql = """SELECT COUNT(*), type FROM Messages
                WHERE userId = {0} GROUP BY type
                """.format(update.message.from_user.id)
        rank = """
                    SELECT COUNT()
                    FROM (
                        SELECT COUNT() as c1, userId as u1
                        FROM Messages
                        WHERE chatId = {0}
                        AND userId = {1}) p1,
                        (
                        SELECT COUNT() as c2, userId as u2
                        FROM Messages
                        WHERE chatId = {0}
                        GROUP BY u2) p2
                    WHERE c2 > c1
                """.format(update.message.chat_id, update.message.from_user.id)
        reply = "Let's see... your all time stats:\n"
    else:
        # simple command, return the short overview for this user in this chat
        sql = """SELECT COUNT(*), type FROM Messages
        WHERE unixtime BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime')
        AND userId = {0} AND chatId = {1} GROUP BY type
        """.format(update.message.from_user.id, update.message.chat_id)
        rank = """
            SELECT COUNT()
            FROM (
                SELECT COUNT() as c1, userId as u1
                FROM Messages
                WHERE chatId = {0}
                AND unixtime BETWEEN datetime('now', 'start of month')
                AND datetime('now', 'localtime')
                AND userId = {1}) p1,
                (
                SELECT COUNT() as c2, userId as u2
                FROM Messages
                WHERE chatId = {0}
                AND unixtime BETWEEN datetime('now', 'start of month')
                AND datetime('now', 'localtime')
                GROUP BY u2) p2
            WHERE c2 > c1
        """.format(update.message.chat_id, update.message.from_user.id)
        reply = "Let's see... your monthly stats:\n"

    conn = sqlite3.connect(db)
    c = conn.cursor()
    data = c.execute(sql).fetchall()
    c.close()
    c = conn.cursor()
    ranking = c.execute(rank).fetchone()
    c.close()
    conn.close()
    pool = [
        "According to my logs you've send {0} {1}s.\n",
        "Oh my, look at this: {0} {1}s. Not so bad.\n",
        "Sending {0} {1}s is not exactly what i expected, but, oh well.\n",
        "Aaaand here we've gooot... {0} {1}s.\n",
        "{0} {1}s. What do you expect me to do, throw you a party?!\n",
        "What do we have here... {0} {1}s.\n",
        "You have send this many {1}s: {0}. It's ok.\n",
        "This one's interesting: {0} {1}s.\n",
        "In local news: you've send {0} {1}s.\n",
        "Aiming for the top? {0} {1}s won't be enough.\n",
        "{0} {1}s sure is something to be proud of.\n",
        "So far you have send {0} {1}s, but I'm sure you can do better.\n",
        "What do you and Batman have in common? No idea, but you've send {0} {1}s so far.\n",
        "Oho, {0} {1}s. Make that a few more and it might improve our relationship.\n",
        "{0} {1}s is nice, but dick pics is what the girl really wanna see.\n",
        "Sending {1}s is not a contest. Nah, just kidding. You have {0}.\n",
        "{0} {1}s, but so much more love...\n",
        "Take {1} and multiply by {0}.\n",
        "{0} {1}s? A judge would understand.\n",
        "Oh I've told you about the girl you've send those {1}s to, right? Her score is {0}. RUN!\n"
    ]
    if monthPool:
        pool.append("You have send {0} {1}s this month.\n")
        pool.append("You have send {0} {1}s within the last days.\n")
    else:
        pool.append("You have send a total of {0} {1}s.\n")
    none = True
    for row in data:
        none = False
        reply += random.choice(pool).format(row[0], row[1])
    if none:
        reply += "Nope, nothing here yet. Sorry."
        reply += "That puts you on rank {0} in this group.".format(ranking[0]+1)
    bot.sendMessage(chat_id=update.message.chat_id, text=reply)
    return


def echo(bot, update, args):
    text = ' '.join(args)
    sql = "SELECT chatId From Messages ORDER BY id DESC LIMIT 1;"
    conn = sqlite3.connect(db)
    c = conn.cursor()
    row = c.execute(sql).fetchone()
    c.close()
    conn.close()
    bot.sendMessage(chat_id=row[0], text=text)


def status(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=random.choice(answer.getStatus()))


def dice_twenty(bot, update):
    reply = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
    ]
    bot.sendMessage(chat_id=update.message.chat_id, text=random.choice(reply))


def helpy(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=answer.getHelpy())


def move(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=random.choice(answer.getMove()))


def sex(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=answer.getSex())


def list_commands(bot, update):
    reply = """
    Oh there is so much you can do to command me! We can roll some /dice, we can look at /stats, /status, /pic...
Besides that, you never know, just try a few commands. Who knows what might be available in the future.

    Your Carolyn,
    xoxoxoxo
    """
    bot.sendMessage(chat_id=update.message.chat_id, text=reply)


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    # Create the Updater and pass it your bot's token.
    updater = Updater(credentials.get_token())
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('stats', stats, pass_args=True))
    dispatcher.add_handler(CommandHandler('blowjob', sex))
    dispatcher.add_handler(CommandHandler('sex', sex))
    dispatcher.add_handler(CommandHandler('naughty', sex))
    dispatcher.add_handler(CommandHandler('nsfw', sex))
    dispatcher.add_handler(CommandHandler('d20', dice_twenty))
    dispatcher.add_handler(CommandHandler('dice', dice.roll_dice))
    updater.dispatcher.add_handler(CallbackQueryHandler(dice.button))
    dispatcher.add_handler(CommandHandler('status', status))
    dispatcher.add_handler(CommandHandler('help', helpy))
    dispatcher.add_handler(CommandHandler('left', move))
    dispatcher.add_handler(CommandHandler('right', move))
    dispatcher.add_handler(CommandHandler('up', move))
    dispatcher.add_handler(CommandHandler('down', move))

    dispatcher.add_handler(CommandHandler('commands', list_commands))
    dispatcher.add_handler(CommandHandler('command', list_commands))

    dispatcher.add_handler(CommandHandler('echo', echo, pass_args=True))

    dispatcher.add_handler(MessageHandler(Filters.command, status))

    dispatcher.add_handler(MessageHandler(Filters.text, text))
    dispatcher.add_handler(MessageHandler(Filters.photo, picture))
    dispatcher.add_handler(MessageHandler(Filters.audio, audio))
    dispatcher.add_handler(MessageHandler(Filters.document, document))
    dispatcher.add_handler(MessageHandler(Filters.location, location))
    dispatcher.add_handler(MessageHandler(Filters.sticker, sticker))
    dispatcher.add_handler(MessageHandler(Filters.video, video))
    dispatcher.add_handler(MessageHandler(Filters.voice, voice))

    # Start the Bot
    print("Starting the bot...")
    updater.start_polling()
    # to stop the bot if necessary: idle
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == "__main__":
    setup.create_database(db)
    main()
