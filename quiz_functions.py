def get_questions_answers(file):
	with open(file, 'r', encoding='KOI8-R') as data_set:
		file_content = data_set.read()

	quiz_text = file_content.split('\n\n')
	quiz_questions_answers = {}
	num = 1

	for string in quiz_text:
		if 'Вопрос' in string:
			quiz_questions_answers[f'question {num}'] = string

		if 'Ответ' in string:
			quiz_questions_answers[f'answer {num}'] = string
			num += 1

	return quiz_questions_answers