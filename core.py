import asyncio
import json

import loguru
import aiogram
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.helper import Helper, HelperMode, ListItem
from pprint import pprint
from aiogram.types import Message, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import filters

from utils.decorators import FixParameterTypes, Timer, SpecialTypesOfUsers

import config
from modules import database


class States(Helper):
    mode = HelperMode.snake_case

    MENU = ListItem()
    TYPES = ListItem()
    GAMES = ListItem()
    TOURNAMENT = ListItem()
    MAPS = ListItem()
    SIDE = ListItem()


loop = asyncio.get_event_loop()

bot = aiogram.Bot(token=config.ACCESS_TOKEN, loop=loop)

dp = aiogram.Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

menuKeyboard = InlineKeyboardMarkup(row_width=2)
menuKeyboard.add(InlineKeyboardButton(text='Баланс', callback_data="profile.balance"))
menuKeyboard.add(InlineKeyboardButton(text='Сделать ставку', callback_data="bet.set"))
menuKeyboard.add(InlineKeyboardButton(text='Рейтинг', callback_data="rating"))
menuKeyboard.add(InlineKeyboardButton(text='Настройки', callback_data="profile.settings"))


@dp.message_handler(commands=['start'])
@Timer()
@FixParameterTypes(Message)
@SpecialTypesOfUsers(user=True)
async def start_function(msg: Message):
    pprint(json.loads(msg.as_json()))
    await msg.answer('Привет, как жизнь друк?')


@dp.message_handler(commands=['menu', 'меню'], state='*')
@Timer()
@FixParameterTypes(Message)
@SpecialTypesOfUsers(user=True)
async def menu(msg: Message):
    global menuKeyboard
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state('menu')
    await msg.answer('Жду вашей ставки', reply_markup=menuKeyboard)


@dp.callback_query_handler(text="profile.balance")
async def send_random_value(call: types.CallbackQuery):
    global menuKeyboard
    await call.message.edit_text(text='Баланс: 1', reply_markup=menuKeyboard)


@dp.message_handler(commands=['get_id'])
async def get_id(msg: Message):
    await msg.answer("Your id: {user_id}".format(user_id=msg.from_user.id))


@dp.message_handler(filters.Text(equals=['сделать ставку'], ignore_case=True), state=0)
async def get_bet(msg: Message):
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state('types')
    kb = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(KeyboardButton('Баланс'))
    await msg.answer("А ок ща")


def run():
    database.setup()
    aiogram.executor.start_polling(dp)
