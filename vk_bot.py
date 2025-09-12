import random
import re
import redis
import vk_api

from dataclasses import dataclass
from environs import Env
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll

from additional_functions import save_user_progress


@dataclass
class QuizContext:
    database: any
    quiz_title: str
    question: str
    correct_answer: str
    user_id: str


def build_quiz_context(database, event, current_key: int = 1) -> QuizContext:
    quiz_title = database.keys('quiz:*')[0]

    correct_answer = database.hget(quiz_title, f'answer {current_key}').split('\n')[-1]
    correct_answer = re.sub(r'\(.*?\)', '', correct_answer)
    correct_answer = correct_answer.split('.')[0].strip().lower()

    return QuizContext(
        database=database,
        quiz_title=quiz_title,
        question=database.hget(quiz_title, f'question {current_key}'),
        correct_answer=correct_answer,
        user_id=f'vk:{event.user_id}',
    )


def send_message(vk, event, text, keyboard):
    return vk.messages.send(
		user_id=event.user_id,
		message=text,
		keyboard=keyboard.get_keyboard(),
		random_id=random.randint(1, 10000)
	)


def get_question(database, event, current_key):
    data = build_quiz_context(database, event, current_key)

    return data.question


if __name__ == '__main__':
    env = Env()
    env.read_env()

    database = redis.Redis(
		host=env.str('DATABASE_HOST'),
		port=env.int('DATABASE_PORT'),
		password=env.str('DATABASE_PASS'),
		decode_responses=True,
	)

    vk_token = env.str('VK_TOKEN')
    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('Счёт', color=VkKeyboardColor.POSITIVE)

    longpoll = VkLongPoll(vk_session)
    current_key = 0
    have_question = False
    wrong_answer = False

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            context_data = build_quiz_context(database, event, current_key=1 if current_key == 0 else current_key)

            if event.text == 'Новый вопрос':
                try:
                    current_key += 1
                    question = get_question(database, event, current_key)
                    send_message(vk, event, question, keyboard)
                    have_question = True
                    wrong_answer = False
                except AttributeError:
                    current_key = 0
                    send_message(
	                    vk,
	                    event,
	                    'Викторина закончилась, нажав на "Новый вопрос", вы начнёте сначала!',
	                    keyboard,
                    )
            elif event.text == context_data.correct_answer:
                send_message(
	                vk,
	                event,
	                'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».',
	                keyboard
                )
                save_user_progress(
	                context_data.user_id,
	                context_data.quiz_title,
	                context_data.question,
	                event.text,
	                True,
	                database,
                )
            elif event.text == 'да' and wrong_answer:
                question = get_question(database, event, current_key)
                send_message(vk, event, question, keyboard)
                wrong_answer = False
            elif event.text == 'нет' and wrong_answer:
                save_user_progress(
	                context_data.user_id,
	                context_data.quiz_title,
	                context_data.question,
	                event.text,
	                False,
	                database,
                )
                send_message(vk, event, 'Нажми на "новый вопрос", чтобы продолжить!', keyboard)
                wrong_answer = False
                have_question = False
            elif event.text == 'Сдаться':
                current_key += 1
                send_message(vk, event, f'Ответ: \n\n{context_data.correct_answer}', keyboard)
                question = get_question(database, event, current_key)
                send_message(vk, event, question, keyboard)
            elif event.text and have_question:
                send_message(vk, event, 'Неправильно… Попробуешь ещё раз? Напиши "да" или "нет"', keyboard)
                wrong_answer = True
            else:
                send_message(vk, event, 'Нажми "новый вопрос", чтобы продолжить!', keyboard)
