from config import BOT_TOKEN
from for_db.db_data import CONNECTION
from for_db.db_queries import *
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from random import randint
import re


ATTEMPTS: int = 8  # Попытки доступные пользователю в одной игре


bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher()
users: dict = {}


def get_random_number() -> int:
    return randint(1, 100)


with CONNECTION:

    def execute_query(query: str, main_command: str) -> dict | None:
        with CONNECTION.cursor() as cursor:
            cursor.execute(query)
            if main_command.lower() == 'select':
                return cursor.fetchone()


    @dp.message(CommandStart())
    async def process_start_command(message: Message):

        user_id: int = message.from_user.id
        first_name: int = message.from_user.first_name
        username: str | None = message.from_user.username

        users[user_id]: dict = {
            'in_game': False,
            'secret_number': None,
            'attempts': None
        }
        
        if not execute_query(check_user_query % user_id, 'select'):
            execute_query(add_user_query % (user_id, username, 0, 0, 0), 'insert')
            await message.answer(f'Здравствуйте {first_name}! Я знаю, что вы новенький и предлагаю вам сыграть со мной в игру "Угадай число". Возможно, вы не знаете правила, так как вы новенький. Поэтому нажмите сюда, чтобы узнать правила /help. А если вы уже знаете правила, то готовы ли вы сыграть со мной в игру?')

        else:
            await message.answer(f'Здравствуйте {first_name}! Я вас помню, вы уже играли со мной в игру, поэтому правила вам объяснять не нужно. Ну чтож, сыграем в игру как в былые 90-е?')


    @dp.message(Command(commands=('help')))
    async def process_help_command(message: Message):
        await message.answer('"Угадай число" правила игры: 1) Вы соглашаетесь, либо отказываетесь. Допустим вы согласились, дальнейшие мои действия. 2) Я загадываю число от 1 до 100 включительно. 3) Вы отправляете мне в чат число и я говорю угадали ли вы или нет, а также я буду давать вам подсказки к разгадке числа. Ну чтож. Вы готовы сыграть со мной в игру?')


    @dp.message(Command(commands=('statistic')))
    async def process_stat_command(message: Message):

        user_id: int = message.from_user.id
        
        total_games, wins, total_score = tuple(execute_query(select_user_info_query % user_id, 'select').values())

        await message.answer(f"Статистика игрока {message.from_user.first_name}; username: {message.from_user.username}\n" \
                            f"Всего сыграно игр: {total_games}\n" \
                            f"Всего выиграно игр: {wins}\n" \
                            f"Всего заработано очков: {total_score}")
        

    @dp.message(Command(commands=('cancel')))
    async def process_stat_command(message: Message):
        
        user_id: int = message.from_user.id

        if users[user_id]['in_game']:
            users[user_id]['in_game']: bool = False
            await message.answer('Вы вышли из игры. Если захотите сыграть снова - напишите об этом')

        else:
            await message.answer('А мы и так с вами не играем. Может, сыграем?')


    @dp.message(lambda x: x.text.isdigit() and 1 <= int(x.text) <= 100)
    async def process_numbers_answer(message: Message):

        user_id: int = message.from_user.id
        mess_text: str = message.text

        if users[user_id]['in_game']:

            users[user_id]['attempts'] -= 1

            if int(mess_text) == users[user_id]['secret_number']:

                user_attempts: int = users[user_id]['attempts']
                number_attempts: int = ATTEMPTS - user_attempts
                remaining_attempts: int = user_attempts if user_attempts > 0 else 1
                score: int = remaining_attempts * 100
                right_word: str = 'попытку' if number_attempts == 1 else ('попытки', 'попыток')[number_attempts > 4]

                execute_query(update_user_info_query % (1, score, user_id), 'update')
                
                users[user_id]['in_game']: bool = False

                await message.answer(f'Поздравляееем!!!! Вы угадали число за {number_attempts} {right_word}, вы получаете {score} очков! Загаданное число было {mess_text}. Сыграем ещё раз?')

            else:

                user_secret_number: int = users[user_id]['secret_number']

                await message.answer(f"К сожалению, вы не угадали. Загаданное число {('больше', 'меньше')[int(mess_text) > user_secret_number]}")

                if users[user_id]['attempts'] == 0:

                    execute_query(update_user_info_query % (0, 0, user_id), 'update')

                    users[user_id]['in_game']: bool = False

                    await message.answer(f'К сожалению, у вас больше не осталось попыток. Вы проиграли. Загаданное число было {user_secret_number}. Попробуйте сыграть ещё раз, может повезёт!')

        else:
            await message.answer('Мы ещё не играем. Куда числа отправляете молодой. Хотите сыграть?')


    @dp.message(lambda x: x.text and re.search(r'в другой раз|по(том|зже)|не|no', x.text.lower()))
    async def process_negative_answer(message: Message):

        user_id: int = message.from_user.id
        
        if users[user_id]['in_game']:
            await message.answer('Мы же сейчас с вами играем, присылайте пожалуйста числа от 1 до 100')

        else:
            await message.answer('Жаль, если захотите поиграть - просто напишите об этом')


    @dp.message(lambda x: x.text and re.search(r'play|да|хочу|сыграем|го|можно|yes|go', x.text.lower()))
    async def process_positive_answer(message: Message):
        
        user_id: int = message.from_user.id

        if users[user_id]['in_game']:
            await message.answer('Пока мы играем в игру я могу реагировать только на числа от 1 до 100 и команды /cancel и /statistic')

        else:

            users[user_id]['in_game']: bool = True
            users[user_id]['secret_number']: int = get_random_number()
            users[user_id]['attempts']: int = ATTEMPTS

            await message.answer(F'Ура! Я загадал число от 1 до 100, попробуй отгадать! У тебя всего {ATTEMPTS} попыток')


    @dp.message()
    async def process_other_answers(message: Message):

        if users[message.from_user.id]['in_game']:
            await message.answer('Мы же с вами уже играем. Отправляйте, пожалуйста, числа от 1 до 100')

        else:
            await message.answer('Моя твоя не понимать! Давай просто сыграем в игру!!!')

    if __name__ == '__main__':
        dp.run_polling(bot)