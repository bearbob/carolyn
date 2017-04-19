import sqlite3

def create_database(db):
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