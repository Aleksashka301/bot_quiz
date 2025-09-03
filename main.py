from environs import Env
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater

from quiz_functions import get_questions_answers


def start(update: Update, context: CallbackContext):
	context.bot.send_message(chat_id=update.effective_chat.id, text='Hi, i am bot!')

def echo(update: Update, context: CallbackContext):
	context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


if __name__ == '__main__':
	env = Env()
	env.read_env()

	telegram_token = env.str('TELEGRAM_TOKEN')
	file_path = 'quiz_questions/1vs1200.txt'

	updater = Updater(token=telegram_token)
	dispatcher = updater.dispatcher

	start_handler = CommandHandler('start', start)
	echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)

	dispatcher.add_handler(start_handler)
	dispatcher.add_handler(echo_handler)

	updater.start_polling()
