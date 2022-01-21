import asyncio
import time

from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.exceptions import RetryAfter

from . import cache
from . import types


def message_send(**kwargs) -> Message:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()
    while True:
        try:
            return loop.run_until_complete(bot.send_message(**kwargs))
        except BotBlocked:
            pass
        except RetryAfter as e:
            timer = int(str(e).split('.')[1].split()[2])
            time.sleep(timer)
