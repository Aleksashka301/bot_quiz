# BOT QUIZ

 Проект содержит двух ботов, для телеграмма и вк. Каждый из ботов предлагает пройти викторину с вопросами. За каждый
правильный ответ начисляется один бал, за не правильный, бал не добавляется... Данный проект использует базу данных 
`Redis`.
Ссылки на ботов [telegram](https://web.telegram.org/k/?swfix=1#@Aleksashka301_Bot), [vk](https://vk.com/club231509983)

Пример бота в телеграмме

![screenshot tekegram](img/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-09-10%20203203.png)


Пример бота в вк

![screenshot vk](img/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-09-10%20204522.png)

## Запуск проекта

### Загрузить репозиторий
```python
git clone https://github.com/Aleksashka301/bot_quiz
```
### Виртуальное окружение
 Перейдите в папку проекта
```python
cd bot_quiz
```
 Установите виртуальное окружение, версия `python` не должна быть выше 3.12
```python
python -m venv myvenv
```
 Активируйте виртуальное окружение

 windows
```python
myvenv\Scripts\activate
```
 linux
```python
source myvenv/bin/activate
```
### Зависимости
 Установите необходимые для работы скриптов, библиотеки
```python
pip install -r requirements.txt
```
### Переменные окружения
 В корне проекта нужно создать файл `.env`. В этом файле создать переменные:
 - `TELEGRAM_TOKEN` токен для работы `telegram` бота. Можно получить у [BotFather](https://web.telegram.org/k/?swfix=1#@BotFather)
 - `VK_TOKEN` api ключ для управления сообществом в `vk`
 - `DATABASE_HOST` Host базы данных на redis-е
 - `DATABASE_PASS` Пароль от базы данных. Можно узнать в личном кабинете 
 - `DATABASE_PORT` Порт базы данных

Все данные о базе данных можно узнать в лично кабинете [Redis](https://cloud.redis.io/?code=QJ-G91UeqM5SXQswMm5-NrGhc0Z1GI4uk2E0gFtpEcY&state=rS8TLqIzvCBw3sCcdKTUX7SWsCv63o0hbVwPpeCzHSsXuM6n9Es3QEYKiAY2A1H6#/)

### База данных
 Перед запуском ботов необходимо установить базу данных и загрузить туда викторину. Аргумент для загрузки викторины не
обязателен, по умолчанию загрузится викторина из файла `1vs1200.txt`. Для загрузки викторины из другого файла необходимо
указать название файла в формате `txt`, который находится в папке `quiz_questions` и запустить команду...
```python
python fill_db.py --file file_name.txt
```

### Запуск
Запуск телеграмм бота
```python
python tg_bot.py
```
Запуск vk бота
```python
python vk_bot.py
```
