import json

import loguru
from pprint import pprint
from aiogram import types
from aiogram.types import Message, ContentTypes, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher import filters

import utils.filters
from utils.decorators import FixParameterTypes, Timer, SpecialTypesOfUsers

from core import dp, run, bot, States


@dp.message_handler(commands=['start'])
@Timer()
@FixParameterTypes(Message)
@SpecialTypesOfUsers(user=True)
async def start_function(msg: Message):
    pprint(json.loads(msg.as_json()))
    await msg.answer('Привет, как жизнь друк?')


@dp.message_handler(commands='menu', state='*')
@Timer()
async def menu(msg: Message):
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state('menu')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(InlineKeyboardButton('Баланс'))
    kb.row(InlineKeyboardButton('Сделать ставку'))
    kb.row(InlineKeyboardButton('Рейтинг'))
    # kb.row(InlineKeyboardButton('Настройки'))
    await msg.answer('Жду вашей ставки', reply_markup=kb, reply=False)


@dp.message_handler(commands=['get_id'])
async def get_id(msg: Message):
    await msg.answer("Your id: {user_id}".format(user_id=msg.from_user.id))


@dp.message_handler(filters.Text(equals='сделать ставку', ignore_case=True), state=0)
async def get_bet(msg: Message):
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state('types')
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    categories = ['']
    kb.row(InlineKeyboardButton('Баланс'))
    await msg.answer()

if __name__ == "__main__":
    run()
