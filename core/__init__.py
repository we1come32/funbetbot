import os
import asyncio
import time

import aiogram
import loguru
from aiogram import Dispatcher

import utils.setup_django
from . import telegram


def run():
    loop = asyncio.get_event_loop()
    executor = aiogram.executor.Executor(
        dispatcher=telegram.dp,
        skip_updates=[],
        loop=asyncio.get_event_loop(),
    )
    executor.start_polling()
