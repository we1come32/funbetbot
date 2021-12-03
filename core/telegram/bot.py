import asyncio

from loguru import logger
import aiogram
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import config
from utils.decorators import RegisterMessageUser
from utils.logger import LoggerMiddleware

loop = asyncio.get_event_loop()

bot = aiogram.Bot(token=config.ACCESS_TOKEN, loop=loop)
logger.info("Бот авторизован")

dp = aiogram.Dispatcher(
    bot,
    storage=MemoryStorage(),
    run_tasks_by_default=True
)
dp.middleware.setup(LoggerMiddleware())
RegisterMessageUser.set_dispatcher(dp)
