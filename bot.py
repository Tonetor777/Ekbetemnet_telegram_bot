from dotenv import load_dotenv
load_dotenv() 
import sqlite3
import telebot
from telebot import types
from config import TELEGRAM_BOT_TOKEN, ADMIN_PASSWORD
from database import init_db, add_question, get_unanswered_questions, get_all_questions, update_answer, add_admin, is_admin
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Initialize the database
init_db()

# Global variables
current_admin = None

# User Menu
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    ask_button = types.KeyboardButton('✏️ Ask Question')
    browse_button = types.KeyboardButton('📋 Browse Questions')
    markup.add(ask_button, browse_button)
    bot.send_message(message.chat.id, "Welcome! Use the buttons below to interact.", reply_markup=markup)

# Ask a Question
@bot.message_handler(func=lambda message: message.text == '✏️ Ask Question')
def ask_question(message):
    bot.send_message(message.chat.id, "Please type your question:")
    bot.register_next_step_handler(message, handle_question)

def handle_question(message):
    question = message.text
    add_question(message.from_user.id, question)
    bot.send_message(message.chat.id, "Your question has been submitted anonymously. You will be notified when it is answered.")

# Browse Previous Questions
@bot.message_handler(func=lambda message: message.text == '📋 Browse Questions')
def browse_questions(message):
    conn = sqlite3.connect("data/bot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT question, answer FROM questions WHERE user_id = ?', (message.from_user.id,))
    questions = cursor.fetchall()
    conn.close()

    if not questions:
        bot.send_message(message.chat.id, "You have no previous questions.")
        return

    response = "Your previous questions:\n\n"
    for q, a in questions:
        response += f"Question: {q}\nAnswer: {a if a else 'Not answered yet'}\n\n"

    bot.send_message(message.chat.id, response)

# Admin Login
@bot.message_handler(commands=['login'])
def login(message):
    if current_admin:
        bot.send_message(message.chat.id, "You are already logged in as an admin.")
        return

    bot.send_message(message.chat.id, "Enter the admin password:")
    bot.register_next_step_handler(message, handle_login)

def handle_login(message):
    global current_admin
    if message.text == ADMIN_PASSWORD:
        current_admin = message.from_user.username
        bot.send_message(message.chat.id, f"Logged in as admin: {current_admin}")
        admin_menu(message)
    else:
        bot.send_message(message.chat.id, "Incorrect password. Please try again.")

# Admin Menu
def admin_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    unanswered_button = types.KeyboardButton('✉️ Unanswered Questions')
    all_button = types.KeyboardButton('📚 All Questions')
    add_button = types.KeyboardButton('👥 Add Admin')
    logout_button = types.KeyboardButton('⬛️ Logout')
    markup.add(unanswered_button, all_button, add_button, logout_button)
    bot.send_message(message.chat.id, "Admin menu:", reply_markup=markup)

# Unanswered Questions
@bot.message_handler(func=lambda message: message.text == '✉️ Unanswered Questions')
def unanswered_questions(message):
    if not current_admin:
        bot.send_message(message.chat.id, "You must log in as an admin first.")
        return

    questions = get_unanswered_questions()
    if not questions:
        bot.send_message(message.chat.id, "No unanswered questions.")
        return

    for q in questions:
        question_id, _, question, _, timestamp = q
        markup = InlineKeyboardMarkup()
        answer_button = InlineKeyboardButton("✅ Answer", callback_data=f"answer_{question_id}")
        markup.add(answer_button)
        bot.send_message(
            message.chat.id,
            f"Question ID: {question_id}\nQuestion: {question}\nTime: {timestamp}",
            reply_markup=markup
        )
# All Questions
@bot.message_handler(func=lambda message: message.text == '📚 All Questions')
def all_questions(message):
    if not current_admin:
        bot.send_message(message.chat.id, "You must log in as an admin first.")
        return

    questions = get_all_questions()
    if not questions:
        bot.send_message(message.chat.id, "No questions available.")
        return

    response = "All questions:\n\n"
    for q in questions:
        response += f"ID: {q[0]}\nQuestion: {q[2]}\nAnswer: {q[3] if q[3] else 'Not answered'}\nTime: {q[4]}\n\n"

    bot.send_message(message.chat.id, response)

# Add Admin
@bot.message_handler(func=lambda message: message.text == '👥 Add Admin')
def add_admin_command(message):
    if not current_admin:
        bot.send_message(message.chat.id, "You must log in as an admin first.")
        return

    bot.send_message(message.chat.id, "Enter the username of the new admin:")
    bot.register_next_step_handler(message, handle_add_admin)

def handle_add_admin(message):
    username = message.text.strip()  # Remove leading/trailing whitespace
    if username.startswith("@"):
        username = username[1:]  # Remove the '@' symbol if present

    if not username.isalnum():  # Ensure the username contains only alphanumeric characters
        bot.send_message(message.chat.id, "Invalid username. Please enter a valid Telegram username.")
        return

    add_admin(username)  # Save the normalized username to the database
    bot.send_message(message.chat.id, f"Admin '{username}' added successfully.")
# Logout
@bot.message_handler(func=lambda message: message.text == '⬛️ Logout')
def logout(message):
    global current_admin
    current_admin = None
    bot.send_message(message.chat.id, "You have been logged out.")

# Answer a Question
@bot.message_handler(func=lambda message: current_admin and message.text.startswith("/answer_"))
def answer_question(message):
    question_id = int(message.text.split("_")[1])
    bot.send_message(message.chat.id, "Enter the answer:")
    bot.register_next_step_handler(message, lambda msg: handle_answer(msg, question_id))

def handle_answer(message, question_id):
    answer = message.text
    update_answer(question_id, answer)

    # Notify the user who asked the question
    conn = sqlite3.connect("data/bot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM questions WHERE id = ?', (question_id,))
    user_id = cursor.fetchone()[0]
    conn.close()

    bot.send_message(user_id, f"Your question has been answered:\n\n{answer}")

    bot.send_message(message.chat.id, "Answer submitted successfully.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def handle_answer_callback(call):
    if not current_admin:
        bot.answer_callback_query(call.id, "You must log in as an admin first.")
        return

    question_id = int(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "Please enter the answer below:")
    bot.send_message(call.message.chat.id, "Enter your answer:")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda msg: handle_answer(msg, question_id))
# Start the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.polling()