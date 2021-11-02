import asyncio

import aiogram
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.helper import Helper, HelperMode, ListItem

import config


class TestStates(Helper):
    mode = HelperMode.snake_case

    MENU = ListItem()
    TYPES = ListItem()
    GAMES = ListItem()
    TOURNAMENT = ListItem()
    MAPS = ListItem()
    SIDE = ListItem()
    BALANCE = ListItem()


loop = asyncio.get_event_loop()

bot = aiogram.Bot(token=config.token, loop=loop)

dp = aiogram.Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


def run():
    aiogram.executor.start_polling(dp)
