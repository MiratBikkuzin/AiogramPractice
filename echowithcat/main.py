from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from config import BOT_TOKEN
import requests


bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher()


@dp.message(Command(commands=['start', 'help']))
async def process_start_message(message: Message):
    await message.answer(f"Hello {message.from_user.first_name}! Send me a message with the word cat at Russian or English languages, but if you don't send, you will see something else")


@dp.message(F.photo)
async def send_echo_photo(message: Message):
    await message.answer_photo(message.photo[0].file_id)


@dp.message(F.voice)
async def send_echo_voice(message: Message):
    await message.answer_voice(message.voice.file_id)


@dp.message()
async def send_echo_or_cat(message: Message):
    
    try:

        low_message: str = message.text.lower()

        if 'cat' in low_message or 'кот' in low_message or 'кошк' in low_message:
            api: list[dict] = requests.get('https://api.thecatapi.com/v1/images/search').json()
            await message.answer_photo(api[0].get('url'))

        else:
            await message.send_copy(message.chat.id)

    except Exception:
        await message.answer("This update doesn't supported, sorry man!")


if __name__ == '__main__':
    dp.run_polling(bot)