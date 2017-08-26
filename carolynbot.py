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
import messages
import inlinekeyboard
import eventhandler
import constants
from chatterbot import ChatBot

sVersion = "1.10c"

conversation = []
chatbot = ChatBot('Carolyn',
                  #storage_adapter='chatterbot.storage.MongoDatabaseAdapter',
                  logic_adapters=['chatterbot.logic.BestMatch'],
                  silence_performance_warning=True,
                  database='chatterbot-database')


def text(bot, update):
    messages.text(bot, update, chatbot, conversation)


def echo(bot, update, args):
    text = ' '.join(args)
    sql = "SELECT chatId From Messages ORDER BY id DESC LIMIT 1;"
    conn = sqlite3.connect(constants.db)
    c = conn.cursor()
    row = c.execute(sql).fetchone()
    c.close()
    conn.close()
    bot.sendMessage(chat_id=row[0], text=text)


def status(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=answer.getStatus())


def helpy(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=answer.getHelpy())


def move(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=random.choice(answer.getMove()))


def snarky(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=answer.getSnarky())


def list_commands(bot, update):
    reply = """
    Hey honey. Here are some commands you may be willing to give a shot:
    /stats [total]
    /naughty
    /nsfw
    /d20
    /dice
    /status
    /help
    /left

    Your Carolyn,
    xoxoxoxo
    """
    bot.sendMessage(chat_id=update.message.chat_id, text=reply)


def version(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Version "+sVersion)


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    # Create the Updater and pass it your bot's token.
    updater = Updater(credentials.get_token())
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('stats', messages.stats, pass_args=True))
    dispatcher.add_handler(CommandHandler('event', eventhandler.add, pass_args=True))
    dispatcher.add_handler(CommandHandler('naughty', snarky))
    dispatcher.add_handler(CommandHandler('nsfw', snarky))
    dispatcher.add_handler(CommandHandler('d20', dice.dice_twenty))
    dispatcher.add_handler(CommandHandler('dice', dice.roll_dice))
    dispatcher.add_handler(CallbackQueryHandler(inlinekeyboard.button))
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
    dispatcher.add_handler(MessageHandler(Filters.photo, messages.picture))
    dispatcher.add_handler(MessageHandler(Filters.audio, messages.audio))
    dispatcher.add_handler(MessageHandler(Filters.document, messages.document))
    dispatcher.add_handler(MessageHandler(Filters.location, messages.location))
    dispatcher.add_handler(MessageHandler(Filters.sticker, messages.sticker))
    dispatcher.add_handler(MessageHandler(Filters.video, messages.video))
    dispatcher.add_handler(MessageHandler(Filters.voice, messages.voice))

    # Start the Bot
    print("Starting the bot...")
    updater.start_polling()
    # to stop the bot if necessary: idle
    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == "__main__":
    setup.create_database(constants.db)
    # setup.train_chatbot(constants.db, chatbot)
    main()
