# database.py

import sqlite3
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table for storing questions and answers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT NOT NULL,
            answer TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table for storing admin usernames
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            username TEXT PRIMARY KEY
        )
    ''')

    conn.commit()
    conn.close()

def add_question(user_id, question):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO questions (user_id, question) VALUES (?, ?)', (user_id, question))
    conn.commit()
    conn.close()

def get_unanswered_questions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM questions WHERE answer IS NULL ORDER BY timestamp')
    return cursor.fetchall()

def get_all_questions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM questions ORDER BY timestamp DESC')
    return cursor.fetchall()

def update_answer(question_id, answer):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE questions SET answer = ? WHERE id = ?', (answer, question_id))
    conn.commit()
    conn.close()

def add_admin(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO admins (username) VALUES (?)', (username,))
    conn.commit()
    conn.close()

def is_admin(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM admins WHERE username = ?', (username,))
    return cursor.fetchone() is not None