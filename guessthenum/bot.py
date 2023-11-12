from config import BOT_TOKEN
from for_db.db_data import host, user, port, password, database
from emojize import winner_cup_emo, game_emo, score_emo, win_rate_emo, user_places_emo
from for_db.db_queries import *
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, KICKED, MEMBER
from aiogram.types import Message, ChatMemberUpdated
from random import randint
from aiomysql import Pool
import re, asyncio, aiomysql


ATTEMPTS: int = 8  # Попытки доступные пользователю в одной игре


bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher()
users: dict = {}


def get_random_number() -> int:
    return randint(1, 100)


async def execute_query(query: str, main_command: str) -> tuple | None:
    async with connection.cursor() as cursor:
        await cursor.execute(query)
        if main_command.lower() == 'select':
            return await cursor.fetchone()


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
        
    if not await execute_query(select_user_info_query % user_id, 'select'):
        await execute_query(add_user_query % (user_id, username, first_name, 0, 0, 0, 0, 'Active'), 'insert')
        await message.answer(f'Здравствуйте {first_name}! Я знаю, что вы новенький и предлагаю вам сыграть со мной в игру "Угадай число". Возможно, вы не знаете правила, так как вы новенький. Поэтому нажмите сюда, чтобы узнать правила /help. А если вы уже знаете правила, то готовы ли вы сыграть со мной в игру?')

    else:
        await message.answer(f'Здравствуйте {first_name}! Я вас помню, вы уже играли со мной в игру, поэтому правила вам объяснять не нужно. Ну чтож, сыграем в игру как в былые 90-е?')


@dp.message(Command(commands=('help')))
async def process_help_command(message: Message):
    await message.answer('"Угадай число" правила игры: 1) Вы соглашаетесь, либо отказываетесь. Допустим вы согласились, дальнейшие мои действия. 2) Я загадываю число от 1 до 100 включительно. 3) Вы отправляете мне в чат число и я говорю угадали ли вы или нет, а также я буду давать вам подсказки к разгадке числа. Ну чтож. Вы готовы сыграть со мной в игру?')


@dp.message(Command(commands=('statistic')))
async def process_stat_command(message: Message):

    user_id: int = message.from_user.id
        
    total_games, wins, total_score, win_rate = await execute_query(select_user_info_query % user_id, 'select')

    await message.answer(f"Статистика игрока {message.from_user.full_name}\n\n" \
                        f"{game_emo} Всего сыграно игр: {total_games} {game_emo}\n\n" \
                        f"{winner_cup_emo} Всего выиграно игр: {wins} {winner_cup_emo}\n\n" \
                        f"{score_emo} Всего заработано очков: {total_score} {score_emo}\n\n" \
                        f"{win_rate_emo} Процент побед: {win_rate} {win_rate_emo}")
    

@dp.message(Command(commands=('myplace')))
async def process_user_place_command(message: Message):
    user_place: int = int((await execute_query(select_user_place % message.from_user.id, 'select'))[0])
    await message.answer(f'{user_places_emo} Ваша позиция среди других пользователей: {user_place} {user_places_emo}')
        

@dp.message(Command(commands=('cancel')))
async def process_stat_command(message: Message):
        
    user_id: int = message.from_user.id

    if users[user_id]['in_game']:
        users[user_id]['in_game']: bool = False
        await message.answer('Вы вышли из игры. Если захотите сыграть снова - напишите об этом')

    else:
        await message.answer('А мы и так с вами не играем. Может, сыграем?')


@dp.message(F.text.isdigit(), lambda x: 1 <= int(x.text) <= 100)
async def process_numbers_answer(message: Message):

    user_id: int = message.from_user.id
    mess_text: str = message.text

    if users[user_id]['in_game']:

        users[user_id]['attempts'] -= 1

        if int(mess_text) == users[user_id]['secret_number']:

            total_games, wins, *_ = await execute_query(select_user_info_query % user_id, 'select')
            win_rate: str = str(int(round(((wins + 1) / (total_games + 1)) * 100)))

            user_attempts: int = users[user_id]['attempts']
            number_attempts: int = ATTEMPTS - user_attempts
            remaining_attempts: int = user_attempts if user_attempts > 0 else 1
            score: int = remaining_attempts * 100
            right_word: str = 'попытку' if number_attempts == 1 else ('попытки', 'попыток')[number_attempts > 4]

            await execute_query(update_user_info_query % (1, score, win_rate + '%', user_id), 'update')
                
            users[user_id]['in_game']: bool = False

            await message.answer(f'Поздравляееем!!!! Вы угадали число за {number_attempts} {right_word}, вы получаете {score} очков! Загаданное число было {mess_text}. Сыграем ещё раз?')

        else:

            user_secret_number: int = users[user_id]['secret_number']

            await message.answer(f"К сожалению, вы не угадали. Загаданное число {('больше', 'меньше')[int(mess_text) > user_secret_number]}")

            if users[user_id]['attempts'] == 0:

                total_games, wins, *_ = await execute_query(select_user_info_query % user_id, 'select')
                win_rate: str = str(int(round((wins / (total_games + 1)) * 100)))

                await execute_query(update_user_info_query % (0, 0, win_rate + '%', user_id), 'update')

                users[user_id]['in_game']: bool = False

                await message.answer(f'К сожалению, у вас больше не осталось попыток. Вы проиграли. Загаданное число было {user_secret_number}. Попробуйте сыграть ещё раз, может повезёт!')

    else:
        await message.answer('Мы ещё не играем. Куда числа отправляете молодой. Хотите сыграть?')


@dp.message(F.text, lambda x: re.search(r'в другой раз|по(том|зже)|не|no', x.text.lower()))
async def process_negative_answer(message: Message):

    user_id: int = message.from_user.id
        
    if users[user_id]['in_game']:
        await message.answer('Мы же сейчас с вами играем, присылайте пожалуйста числа от 1 до 100')

    else:
        await message.answer('Жаль, если захотите поиграть - просто напишите об этом')


@dp.message(Command(commands=('play')))
@dp.message(F.text, lambda x: re.search(r'да|хочу|сыграем|го|можно|yes|go', x.text.lower()))
async def process_positive_answer(message: Message):
        
    user_id: int = message.from_user.id

    if users[user_id]['in_game']:
        await message.answer('Пока мы играем в игру я могу реагировать только на числа от 1 до 100 и команды /cancel и /statistic')

    else:

        users[user_id]['in_game']: bool = True
        users[user_id]['secret_number']: int = get_random_number()
        users[user_id]['attempts']: int = ATTEMPTS

        await message.answer(F'Ура! Я загадал число от 1 до 100, попробуй отгадать! У тебя всего {ATTEMPTS} попыток')


@dp.message(F.text)
async def process_other_answers(message: Message):

    if users[message.from_user.id]['in_game']:
        await message.answer('Мы же с вами уже играем. Отправляйте, пожалуйста, числа от 1 до 100')

    else:
        await message.answer('Моя твоя не понимать! Давай просто сыграем в игру!!!')


@dp.my_chat_member(ChatMemberUpdatedFilter(KICKED))
async def process_user_blocked_bot(event: ChatMemberUpdated):
    await execute_query(rename_status_user_query % ('Inactive', event.from_user.id), 'update')


@dp.my_chat_member(ChatMemberUpdatedFilter(MEMBER))
async def process_user_unblocked_bot(event: ChatMemberUpdated):
    await execute_query(rename_status_user_query % ('Active', event.from_user.id), 'update')
    await event.answer('Я рад видеть тебя снова!')


async def main(loop) -> None:
    global connection

    pool: Pool = await aiomysql.create_pool(
        loop=loop,
        user=user,
        password=password,
        db=database,
        host=host,
        port=port,
        autocommit=True
        )

    async with pool.acquire() as connection:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    
    pool.close()
    await pool.wait_closed()


if __name__ == '__main__':
    asyncio.run(main(asyncio.get_event_loop()))