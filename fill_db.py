import redis
import argparse
from environs import Env


def get_questions_answers(file):
	with open(f'quiz_questions/{file}', 'r', encoding='KOI8-R') as data_set:
		file_content = data_set.read()

	quiz_text = file_content.split('\n\n')
	quiz_questions_answers = {}
	quiz_questions_answers['quiz_title'] = quiz_text[0].split('\n')[-1]
	num = 1

	for string in quiz_text:
		lines = string.strip().splitlines()

		if lines and 'Вопрос' in lines[0]:
			header = lines[0].strip()
			body = ' '.join(line.strip() for line in lines[1:])
			quiz_questions_answers[f'question {num}'] = f'{header}\n\n{body}'

		elif lines and 'Ответ' in lines[0]:
			header = lines[0].strip()
			body = ' '.join(line.strip() for line in lines[1:])

			quiz_questions_answers[f'answer {num}'] = f'{header}\n\n{body}'
			num += 1

	return quiz_questions_answers


def creating_database(quiz, base):
	quiz_title = quiz.pop('quiz_title')
	base.hset(f'quiz:{quiz_title}', mapping=quiz)


if __name__ == '__main__':
	env = Env()
	env.read_env()

	parser = argparse.ArgumentParser(description='Указание файла с вопросами и ответами для викторины')
	parser.add_argument('file', help='Файл для загрузки')
	args = parser.parse_args()

	database = redis.Redis(
		host=env.str('DATABASE_HOST'),
		port=env.int('DATABASE_PORT'),
		password=env.str('DATABASE_PASS'),
		decode_responses=True,
	)

	quiz = get_questions_answers(args.file)
	creating_database(quiz, database)
