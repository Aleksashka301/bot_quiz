import json
import re
import redis

from enum import Enum
from environs import Env
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, Filters, MessageHandler, Updater

from response_handlers import save_user_progress


def start(update: Update, context: CallbackContext):
    keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счёт'],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Добро пожаловать на викторину! Нажмите "Новый вопрос", чтобы начать или продолжить. '
             '"Завершить", чтобы закончить викторину. '
             '"Мой счёт", узнать свой счёт.',
        reply_markup=markup
    )


def question_handler(update: Update, context: CallbackContext):
    database = context.bot_data['database']
    quiz_title = database.keys('quiz:*')[0]
    question_key = f'question {1}'

    correct_answer = database.hget(quiz_title, f'answer {1}').split('\n')[-1]
    correct_answer = re.sub(r'\(.*?\)', '', correct_answer)
    correct_answer = correct_answer.split('.')[0].strip().lower()
    context.user_data['correct_answer'] = correct_answer

    question = database.hget(quiz_title, question_key)
    update.message.reply_text(question)

    context.user_data['quiz_title'] = quiz_title
    context.user_data['question'] = question

    return StagesQuiz.ANSWER


def answer_handler(update: Update, context: CallbackContext):
    database = context.bot_data['database']
    quiz_title = context.user_data['quiz_title']
    correct_answer = context.user_data['correct_answer']

    user_id = update.effective_user.id
    question = context.user_data['question']
    context.user_data['user_answer'] = update.message.text.strip().lower()
    user_answer = context.user_data['user_answer']

    if user_answer == correct_answer:
        update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».')
        save_user_progress(user_id, quiz_title, question, user_answer, True, database)
    else:
        update.message.reply_text('Неправильно… Попробуешь ещё раз?')

        return StagesQuiz.WRONG_ANSWER


def wrong_answer_handler(update: Update, context: CallbackContext):
    database = context.bot_data['database']
    user_id = update.effective_user.id
    quiz_title = context.user_data['quiz_title']
    question = context.user_data['question']
    user_answer = context.user_data['user_answer']

    if update.message.text.strip().lower() == 'да':
        question_handler(update, context)
        return StagesQuiz.ANSWER
    elif update.message.text.strip().lower() == 'нет':
        save_user_progress(user_id, quiz_title, question, user_answer, False, database)
        update.message.reply_text('Нажми на "новый вопрос", чтобы продолжить!')
        return StagesQuiz.ANSWER
    else:
        update.message.reply_text('Напиши "да" или "нет".')

def complete_handler(update: Update, context: CallbackContext):
    database = context.bot_data['database']
    user_id = update.effective_user.id
    quiz_title = context.user_data['quiz_title']
    question = context.user_data['question']
    correct_answer = context.user_data['correct_answer']

    update.message.reply_text(correct_answer)
    save_user_progress(user_id, quiz_title, question, '', False, database)

    return question_handler(update, context)


if __name__ == '__main__':
    env = Env()
    env.read_env()
    telegram_token = env.str('TELEGRAM_TOKEN')

    database = redis.Redis(
        host=env.str('DATABASE_HOST'),
        port=env.int('DATABASE_PORT'),
        password=env.str('DATABASE_PASS'),
        decode_responses=True,
    )

    class StagesQuiz(Enum):
        ANSWER = 1
        WRONG_ANSWER = 2

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['database'] = database

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(Filters.regex('^Новый вопрос$'), question_handler),
        ],
        states={
            StagesQuiz.ANSWER: [
                MessageHandler(Filters.regex('^Новый вопрос$'), question_handler),
                MessageHandler(Filters.regex('^Сдаться$'), complete_handler),
                MessageHandler(Filters.text & ~Filters.command, answer_handler),
            ],
            StagesQuiz.WRONG_ANSWER: [
                MessageHandler(Filters.regex('^Новый вопрос$'), question_handler),
                MessageHandler(Filters.regex('^Сдаться$'), complete_handler),
                MessageHandler(Filters.text & ~Filters.command, wrong_answer_handler)
            ],
        },
        fallbacks=[]
    )

    dispatcher.add_handler(conv_handler)

    # database.flushdb()
    updater.start_polling()
    updater.idle()
