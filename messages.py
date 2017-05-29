import sqlite3
import random
import constants


def checkuser(user):
    id = user.id
    first = user.first_name
    last = user.last_name
    name = user.username
    sql = "INSERT INTO Users(userId, userName, firstName, lastName) SELECT {0}, '{1}', '{2}', '{3}'  WHERE NOT EXISTS("
    sql += "SELECT 1 FROM Users WHERE userId = {0})"
    query = sql.format(id, name, first, last)
    try:
        conn = sqlite3.connect(constants.db)
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
        conn = sqlite3.connect(constants.db)
        c = conn.cursor()
        c.execute('INSERT INTO Words (userId, word) VALUES (?, ?)', (userId, nw.lower()))
        c.close()
        conn.close()

    return hashtags


def text(bot, update, chatbot, conversation):
    conn = sqlite3.connect(constants.db)
    typus = constants.text
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
    replyToBot = False
    try:
        ans = update.message.reply_to_message.from_user.id
        if ans == bot.id:
            replyToBot = True
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

    hay = content.lower()
    conversation.append(hay)
    if len(conversation) > 2:
        del (conversation[0])
        chatbot.train(conversation)
    # answer if the message contains the name, is a private chat or was a direct reply to the bot
    if "carolyn" in hay or "caro" in hay or chatId > 0 or replyToBot:
        hay = hay.replace("carolyn", "")
        hay = hay.replace("caro", "")
        statement = chatbot.get_response(hay)
        response = statement.text.lower()
        response = response.replace("carolyn", "")
        response = response.replace("caro", "")
        bot.sendMessage(chat_id=update.message.chat_id, text=response)


def handleother(update, typ):
    global conn
    conn = sqlite3.connect(constants.db)
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
    typus = constants.picture
    handleother(update, typus)


def audio(bot, update):
    typus = constants.audio
    handleother(update, typus)


def document(bot, update):
    try:
        if update.message.document.file_name.endswith(".mp4"):
            if update.message.document.file_name == 'giphy.mp4':
                typus = constants.gif
            else:
                typus = constants.video
    except AttributeError:
        typus = constants.document
    handleother(update, typus)


def location(bot, update):
    typus = constants.location
    handleother(update, typus)


def sticker(bot, update):
    typus = constants.sticker
    handleother(update, typus)


def video(bot, update):
    typus = constants.video
    handleother(update, typus)


def voice(bot, update):
    typus = constants.voice
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

    conn = sqlite3.connect(constants.db)
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
        "{0} {1}s? A judge would understand.\n"
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
