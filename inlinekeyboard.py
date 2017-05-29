from random import randint


def button(bot, update):
    query = update.callback_query
    if query.data.startswith("dice"):
        data = query.data[len("dice"):]
        reply = "Rolling one D{0}... Got {1}."
        bot.editMessageText(text=reply.format(data, randint(1, int(data))),
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id)
