import json


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
