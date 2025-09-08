import random
import vk_api

from environs import Env
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll


if __name__ == '__main__':
	env = Env()
	env.read_env()

	vk_token = env.str('VK_TOKEN')
	vk_session = vk_api.VkApi(token=vk_token)
	vk = vk_session.get_api()
	keyboard = VkKeyboard(one_time=True)

	keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
	keyboard.add_button('Сдаться', color=VkKeyboardColor.POSITIVE)
	keyboard.add_line()

	keyboard.add_button('Счёт', color=VkKeyboardColor.POSITIVE)

	longpoll = VkLongPoll(vk_session)

	for event in longpoll.listen():
		if event.type == VkEventType.MESSAGE_NEW and event.to_me:
			vk.messages.send(
				user_id=event.user_id,
				message=event.text,
				keyboard=keyboard.get_keyboard(),
				random_id=random.randint(1, 10000)
			)
