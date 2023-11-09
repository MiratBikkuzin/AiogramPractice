from imports import *


ATTEMPTS: int = 8  # Попытки доступные пользователю в одной игре


bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher()
users: dict = {}


with CONNECTION:

    def execute_query(query: str, main_command: str) -> tuple[dict] | None:
        with CONNECTION.cursor() as cursor:
            cursor.execute(query)
            if main_command.lower() == 'select':
                return cursor.fetchall()


    def get_random_number() -> int:
        return randint(1, 100)


    @dp.message(CommandStart())
    async def process_start_command(message: Message):

        user_id: int = message.from_user.id
        username: str | None = message.from_user.username
        
        if not execute_query(check_user_query % user_id, 'select'):
            execute_query(add_user_query % (user_id, username, 0, 0), 'insert')

        users[user_id]: dict = {
            'in_game': False,
            'secret_number': None,
            'attempts': None
        }

        await message.answer('Здравствуйте уважаемый! Предлагаю вам сыграть со мной в игру "Угадай число". Прочитайте подробные правила нажав сюда /help. А если вы уже знаете правила, то готовы ли вы сыграть со мной в игру "Да/Нет"')


    @dp.message(Command(commands=('help')))
    async def process_help_command(message: Message):
        await message.answer('"Угадай число" правила игры: 1) Вы соглашаетесь, либо отказываетесь. Допустим вы согласились, дальнейшие мои действия. 2) Я загадываю число от 1 до 100 включительно. 3) Вы отправляете мне в чат число и я говорю угадали ли вы или нет, а также я буду давать вам подсказки к разгадке числа. Ну чтож. Вы готовы сыграть со мной в игру?')


    @dp.message(Command(commands=('statistic')))
    async def process_stat_command(message: Message):

        user_id: int = message.from_user.id
        
        total_games, wins = tuple(execute_query(select_user_info_query % user_id, 'select')[0].values())

        await message.answer(f"Статистика игрока {message.from_user.first_name}; username: {message.from_user.username}\n" \
                            f"Всего сыграно игр: {total_games}\n" \
                            f"Всего выиграно игр: {wins}")
        

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

            if int(mess_text) == users[user_id]['secret_number']:

                execute_query(update_user_info_query % (1, user_id), 'update')
                
                users[user_id]['in_game']: bool = False

                await message.answer(f'Поздравляееем!!!! Вы угадали число!!! Загаданное число было {mess_text}')

            else:

                user_secret_number: int = users[user_id]['secret_number']
                users[user_id]['attempts'] -= 1

                await message.answer(f"К сожалению, вы не угадали. Загаданное число {('больше', 'меньше')[int(mess_text) > user_secret_number]}")

                if users[user_id]['attempts'] == 0:

                    execute_query(update_user_info_query % (0, user_id), 'update')

                    users[user_id]['in_game']: bool = False

                    await message.answer(f'К сожалению, у вас больше не осталось попыток. Вы проиграли. Загаданное число было {user_secret_number}. Попробуйте сыграть ещё раз, может повезёт!')

        else:
            await message.answer('Мы ещё не играем. Куда числа отправляете молодой. Хотите сыграть?')


    @dp.message(lambda x: isinstance(x.text, str) and re.search(r'в другой раз|потом|не|позже|nope|no', x.text.lower()))
    async def process_negative_answer(message: Message):

        user_id: int = message.from_user.id
        
        if users[user_id]['in_game']:
            await message.answer('Мы же сейчас с вами играем, присылайте пожалуйста числа от 1 до 100')

        else:
            await message.answer('Жаль, если захотите поиграть - просто напишите об этом')


    @dp.message(lambda x: isinstance(x.text, str) and re.search(r'да|хочу|давай|сыграем|го|можно|yes|go', x.text.lower()))
    async def process_positive_answer(message: Message):
        
        user_id: int = message.from_user.id

        if users[user_id]['in_game']:
            await message.answer('Пока мы играем в игру я могу реагировать только на числа от 1 до 100 и команды /cancel и /statistic')

        else:

            users[user_id]['in_game']: bool = True
            users[user_id]['secret_number']: int = get_random_number()
            users[user_id]['attempts']: int = ATTEMPTS

            await message.answer('Ура! Я загадал число от 1 до 100, попробуй отгадать! У тебя всего 8 попыток')


    @dp.message()
    async def process_other_answers(message: Message):

        if users[message.from_user.id]['in_game']:
            await message.answer('Мы же с вами уже играем. Отправляйте, пожалуйста, числа от 1 до 100')

        else:
            await message.answer('Моя твоя не понимать! Давай просто сыграем в игру!!!')


    if __name__ == '__main__':
        dp.run_polling(bot)