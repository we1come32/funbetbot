import asyncio

import loguru
from aiogram import types
from aiogram.dispatcher import FSMContext, filters
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, Message, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import exceptions
from aiogram.utils.exceptions import InvalidQueryID

import config
from core.telegram import dp, bot
from data import models
from utils.decorators import RegisterMessageUser, FixParameterTypes
from .keyboards import *
from . import textHandlers, CallBackHandlers

loguru.logger.debug("Функции в Dispatcher зарегистрировано: "
                    f"Callback handlers - {len(dp.callback_query_handlers.handlers)}, "
                    f"Message handler - {len(dp.message_handlers.handlers)}")
