import json

import loguru
from pprint import pprint
from aiogram import types
from aiogram.types import Message, ContentTypes, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher import filters
from utils.decorators import FixParameterTypes, Timer, SpecialTypesOfUsers

from core import dp, run, bot


@dp.message_handler(commands=['start'])
@Timer()
@FixParameterTypes(Message)
@SpecialTypesOfUsers(user=True)
async def start_function(msg: Message):
    pprint(json.loads(msg.as_json()))
    await msg.answer('Привет, как жизнь друк?')


@dp.message_handler(commands='menu')
@Timer()
async def menu(msg: Message):
    kb = ReplyKeyboardMarkup()
    kb.add(InlineKeyboardButton('Баланс', callback_data='balance'))
    await msg.answer('Жду вашей ставки', reply_markup=kb, reply=False)


@dp.callback_query_handler()
@Timer()
async def balance(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, '"А вот тебе и баланс')


@dp.message_handler(content_types=ContentTypes.TEXT)
@Timer()
@FixParameterTypes(Message)
async def function(msg: Message):
    loguru.logger.debug(f"Msg: {msg.text!r} from id{msg.chat.id}")
    await msg.answer("Hello", reply=False)


if __name__ == "__main__":
    run()
