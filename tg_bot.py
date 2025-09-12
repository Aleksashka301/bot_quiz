import re
import redis

from dataclasses import dataclass
from enum import Enum
from environs import Env
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, Filters, MessageHandler, Updater

from additional_functions import save_user_progress


@dataclass
class QuizContext:
    database: any
    quiz_title: str
    question: str
    correct_answer: str
    user_answer: str
    user_id: str


def get_quiz_context(update, context) -> QuizContext:
    database = context.bot_data['database']
    quiz_title = database.keys('quiz:*')[0]
    key = context.user_data.get('current_key', 1)

    correct_answer = database.hget(quiz_title, f'answer {key}').split('\n')[-1]
    correct_answer = re.sub(r'\(.*?\)', '', correct_answer)
    correct_answer = correct_answer.split('.')[0].strip().lower()

    return QuizContext(
        database=database,
        quiz_title=quiz_title,
        question=database.hget(quiz_title, f'question {key}'),
        correct_answer=correct_answer,
        user_answer=update.message.text.strip().lower(),
        user_id=f'tg:{update.effective_user.id}',
    )


def start(update: Update, context: CallbackContext):
    context.user_data['current_key'] = 0
    keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счёт'],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Добро пожаловать на викторину! Нажмите "Новый вопрос", чтобы начать или продолжить. '
             '"Сдаться", чтобы получить ответ на полученный вопрос. '
             '"Мой счёт", узнать свой счёт.',
        reply_markup=markup
    )


def send_question_user(update: Update, context: CallbackContext):
    if 'current_key' not in context.user_data:
        context.user_data['current_key'] = 1
    else:
        context.user_data['current_key'] += 1

    try:
        context_data = get_quiz_context(update, context)
        update.message.reply_text(context_data.question)
    except AttributeError:
        context.user_data['current_key'] = 0
        update.message.reply_text('Викторина закончилась, нажав на "Новый вопрос", вы начнёте сначала!')

    return StagesQuiz.ANSWER


def handle_answer(update: Update, context: CallbackContext):
    context_data = get_quiz_context(update, context)

    if context_data.user_answer == context_data.correct_answer:
        update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».')
        save_user_progress(
            context_data.user_id,
            context_data.quiz_title,
            context_data.question,
            context_data.user_answer,
            True,
            context_data.database
        )
    else:
        update.message.reply_text('Неправильно… Попробуешь ещё раз?')

        return StagesQuiz.WRONG_ANSWER


def handle_incorrect_answer(update: Update, context: CallbackContext):
    context_data = get_quiz_context(update, context)

    if context_data.user_answer == 'да':
        update.message.reply_text(context_data.question)

        return StagesQuiz.ANSWER

    elif context_data.user_answer == 'нет':
        save_user_progress(
            context_data.user_id,
            context_data.quiz_title,
            context_data.question,
            context_data.user_answer,
            False,
            context_data.database
        )
        update.message.reply_text('Нажми на "новый вопрос", чтобы продолжить!')

        return StagesQuiz.ANSWER

    else:
        update.message.reply_text('Напиши "да" или "нет".')

def surrender_handler(update: Update, context: CallbackContext):
    context_data = get_quiz_context(update, context)

    update.message.reply_text(f'Ответ:\n\n{context_data.correct_answer}')
    save_user_progress(
        context_data.user_id,
        context_data.quiz_title,
        context_data.question,
        '',
        False,
        context_data.database,
    )

    return send_question_user(update, context)


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
            MessageHandler(Filters.regex('^Новый вопрос$'), send_question_user),
        ],
        states={
            StagesQuiz.ANSWER: [
                MessageHandler(Filters.regex('^Новый вопрос$'), send_question_user),
                MessageHandler(Filters.regex('^Сдаться$'), surrender_handler),
                MessageHandler(Filters.text & ~Filters.command, handle_answer),
            ],
            StagesQuiz.WRONG_ANSWER: [
                MessageHandler(Filters.regex('^Новый вопрос$'), send_question_user),
                MessageHandler(Filters.regex('^Сдаться$'), surrender_handler),
                MessageHandler(Filters.text & ~Filters.command, handle_incorrect_answer)
            ],
        },
        fallbacks=[]
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()
