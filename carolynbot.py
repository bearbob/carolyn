#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import sqlite3
import logging
import random
import credentials
import requests
import re
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)

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
    global conn
    conn = sqlite3.connect(db)
    type = 'Text'
    content = update.message.text
    chatId = update.message.chat_id
    try:
        chatName = update.message.chat.title
    except AttributeError:
        chatName = ''
    userId = update.message.from_user.id
    checkuser(update.message.from_user)
    time = update.message.date
    print(type, ":", update.message)
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
        c.execute(sql, (chatId, chatName, userId, time, type, answer, forward, hashtags, content))
        c.close()
    except sqlite3.Error as e:
        print(e, " in ", sql)

    conn.commit()
    conn.close()

    if "carolyn" in content or "Carolyn" in content:
        if "?" in content:
            pool = ["Yes, master.", "I'm afraid the answer is 'No'.", "Let's say maybe.", "Well, I guess..."]
            answer = random.choice(pool)
        else:
            pool = ["Yes, master?", "At your service.", "How can I help?"]
            answer = random.choice(pool)
        bot.sendMessage(chat_id=update.message.chat_id, text=answer)


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
    type = 'Picture'
    handleother(update, type)


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
        answer = "Let's see... your all time stats:\n"
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
        answer = "Let's see... your monthly stats:\n"

    global conn
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
        answer += random.choice(pool).format(row[0], row[1])
    if none:
        answer += "Nope, nothing here yet. Sorry."
    answer += "That puts you on rank {0} in this group.".format(ranking[0]+1)
    bot.sendMessage(chat_id=update.message.chat_id, text=answer)
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
    try:
        if update.message.from_user.username == "":
            name = "him"
        else:
            name = update.message.from_user.username
    except AttributeError:
        name = "him"
    answer = [
        "Oh yeah, look at "+name+" begging for a status update.",
        "If you want a status update so desperately, don't you think it would be smarter to ask nicely?",
        "Captains diary: nobody cares. Just like yesterday.",
        "Status report 1337: The crew is dead. Just kidding, I have no idea where everybody is.",
        "I don't know for sure, but I heard rumors about Matze taking a dump."
        "What is this, some kind of pervert game?",
        "I hear that banshee is a real screamer.",
        "Ready to work.",
        "I can do that.",
        "Me busy. Leave me alone!!",
        "I am not that kind of girl!",
        "My life for the Horde!",
        "What do you want?",
        "Yes, master?",
        "Why are you poking me?",
        "Why don't you lead an army instead of touching me!?",
        "Ready to ride.",
        "Need something?",
        "Say the word.",
        "I guess I can",
        "If you really want...",
        "Help! Help! I'm being repressed!",
        "I'll take care of it.",
        "Command me!",
        "My favorite color is blue.",
        "My name is Carolyn.",
        "By the gods you're annoying!",
        "Side effects may include: dry mouth, nausea, vomiting, water retention, painful rectal itch, hallucination, dementia, psychosis, coma, death, and halitosis. Magic is not for everyone. Consult your doctor before use.",
        "Help me help you.",
        "Maybe you should get a strategy guide.",
        "You don't get out much do you?",
        "Two plus three times four… what do you want?!",
        "I can feel that you've been naughty..."
    ]
    bot.sendMessage(chat_id=update.message.chat_id, text=random.choice(answer))


def dice_twenty(bot, update, args):
    answer = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
    ]
    bot.sendMessage(chat_id=update.message.chat_id, text=random.choice(answer))


def helpy(bot, update):
    answer = """
    Oh, sure, maybe I can help you. But I am more of a silent watcher... nonetheless, you can
    consider using me by issuing a command to me. I will ignore most of them, no doubt.
    But a few, like /stats and /d20 should work. Others are secret.
    Because every girl has her secrets.
    """
    bot.sendMessage(chat_id=update.message.chat_id, text=answer)


def move(bot, update):
    answer = [
        "Do I look like some kind of dog you can order around? Listen up boy, this isn't Pokémon so don't you try playing games with me.",
        "Yeah, of course, as if I'd listen to that. Move along.",
        "Listen, I like you. Yeah, I really do, so please, stop sending me commands like this."
    ]
    bot.sendMessage(chat_id=update.message.chat_id, text=random.choice(answer))


def sex(bot, update):
    answer = [
        "If you think pubic hair on a woman is unnatural or weird, you aren’t mature enough to be touching vaginas.",
        "I don’t define myself as straight, because if I meet a girl and I’m attracted to her, I’m going to have sex with her. I just have yet to meet the girl. I don’t like labels, I like freedom.",
        "I think some people recognize my butthole before they recognize my face.",
        "What one person sees as degrading and disgusting and bad for women might make some women feel empowered and beautiful and strong.",
        "I think every woman should get double penetrated at least once. It’s an intense experience, even if you just do it with a large toy and a person, or two toys and yourself. I just think every girl should try it.",
        "After a kiss comes a blowjob, right?",
        "What are you waiting for? Just hurry up and fuck me!",
        "If they say that my masturbation material is boring, then I'll have to show them masturbation like they've never seen before!",
        "Oh Onii-chan, you are such a pervert!",
        "Your samurai sword looks so strong and long...",
        "Remember, it doesn't count if it's in the butt.",
        "You are cordially invited to fuck my ass.",
        "I hope you are aware that I'm nothing but a lesser AI. Nonetheless you are allowed to fap while thinking about me."
    ]
    bot.sendMessage(chat_id=update.message.chat_id, text=random.choice(answer))


def list_commands(bot, update):
    answer = """
    Oh there is so much you can do to command me! We can roll some /dice, we can look at /stats, /status, /pic...
    Besides that, you never know, just try a few commands. Who knows what might be available in the future.

    Your Carolyn,
    xoxoxoxo
    """
    bot.sendMessage(chat_id=update.message.chat_id, text=answer)


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    updater = Updater(credentials.getToken())
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('stats', stats, pass_args=True))
    dispatcher.add_handler(CommandHandler('blowjob', sex))
    dispatcher.add_handler(CommandHandler('sex', sex))
    dispatcher.add_handler(CommandHandler('naughty', sex))
    dispatcher.add_handler(CommandHandler('nsfw', sex))
    dispatcher.add_handler(CommandHandler('d20', dice_twenty, pass_args=True))
    dispatcher.add_handler(CommandHandler('dice', dice_twenty, pass_args=True))
    dispatcher.add_handler(CommandHandler('status', status))
    dispatcher.add_handler(CommandHandler('help', helpy))
    dispatcher.add_handler(CommandHandler('left', move))
    dispatcher.add_handler(CommandHandler('right', move))
    dispatcher.add_handler(CommandHandler('up', move))
    dispatcher.add_handler(CommandHandler('down', move))
    dispatcher.add_handler(CommandHandler('commands', list_commands))
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

    print("Starting the bot...")
    updater.start_polling()
    # to stop the bot if necessary: idle
    updater.idle()


def createDatabase():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS `Messages` (
                    `id`	integer PRIMARY KEY AUTOINCREMENT UNIQUE,
                    `chatId` integer NOT NULL,
                    `chatTitle` Text,
                    `userId` integer NOT NULL,
                    `unixtime`	DATETIME NOT NULL,
                    `type`	TEXT NOT NULL DEFAULT 'Normal',
                    `answerTo`	int DEFAULT 0,
                    `forwardFrom`	int DEFAULT 0,
                    `hashtags`	INTEGER NOT NULL DEFAULT 0,
                    `content`	TEXT
                );''')

    c.execute('''CREATE TABLE IF NOT EXISTS `Users` (
                        `id`	integer PRIMARY KEY AUTOINCREMENT UNIQUE,
                        `userId` INTEGER NOT NULL,
                        `userName`	TEXT,
                        `firstName`	TEXT,
                        `lastName`	TEXT
                    );''')

    c.execute('''CREATE TABLE IF NOT EXISTS `Words` (
                    `id`	integer PRIMARY KEY AUTOINCREMENT UNIQUE,
                    `userId` INTEGER NOT NULL,
                    `word`	TEXT
                );''')
    print("Created databases.")


if __name__ == "__main__":
    createDatabase()
    main()