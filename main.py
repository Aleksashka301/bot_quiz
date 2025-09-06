import json
import re
import redis

from environs import Env
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


NEW_QUESTION, COMPLETE, SCORE = range(3)


def start(update: Update, context: CallbackContext):
    keyboard = [
        ['Новый вопрос', 'Завершить'],
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
    button = update.message.text
    database = context.bot_data.get('database')
    quiz_title = database.keys('quiz:*')[0]
    question_key = 'question 1'
    answer_key = 'answer 1'

    if button == 'Новый вопрос':
        question = database.hget(quiz_title, question_key)
        update.message.reply_text(question)

        context.user_data['waiting_answer'] = True
        context.user_data['current_question'] = question_key
        context.user_data.pop('retry', None)
        return

    if context.user_data.get('waiting_answer'):
        user_answer = (update.message.text or '').strip().lower()
        correct_answer = database.hget(quiz_title, answer_key).split('\n')[-1]
        correct_answer = re.sub(r'\(.*?\)', '', correct_answer)
        correct_answer = correct_answer.split('.')[0].strip().lower()
        user_id = update.effective_user.id

        if user_answer == correct_answer:
            update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».')
            save_user_progress(user_id, quiz_title, question_key, user_answer, True, database)

            context.user_data.pop('waiting_answer', None)
            context.user_data.pop('current_question', None)
            context.user_data.pop('retry', None)
        else:
            update.message.reply_text('Неправильно… Попробуешь ещё раз?')
            context.user_data['retry'] = True
            context.user_data.pop('waiting_answer', None)

        save_user_progress(user_id, quiz_title, question_key, user_answer, user_answer == correct_answer, database)
        return

    if context.user_data.get('retry'):
        if button == 'да':
            question = database.hget(quiz_title, question_key)
            update.message.reply_text(question)
            context.user_data['waiting_answer'] = True
            context.user_data.pop('retry', None)
            return
        elif button == 'нет':
            update.message.reply_text('Ок, нажми «Новый вопрос», чтобы продолжить.')
            context.user_data.pop('retry', None)
            return
        else:
            update.message.reply_text('Пожалуйста, ответь "да" или "нет".')
            return

    if button == 'Сдаться':
        update.message.reply_text('Сдаться')

    elif button == 'Мой счёт':
        update.message.reply_text('Счёт')

    else:
        update.message.reply_text('Нажми «Новый вопрос», чтобы начать или продолжить.')


def save_user_progress(user_id, quiz_title, question, user_answer, is_correct: bool, database):
    existing_data = database.get(f'user:{user_id}')

    if existing_data:
        user_data = json.loads(existing_data)
    else:
        user_data = {}

    if quiz_title not in user_data:
        user_data[quiz_title] = {'score': 0}

    user_data[quiz_title][question] = user_answer

    if is_correct:
        user_data[quiz_title]['score'] += 1

    database.set(f'user:{user_id}', json.dumps(user_data))


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

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['database'] = database

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, question_handler))
    # database.flushdb()

    updater.start_polling()
    updater.idle()
