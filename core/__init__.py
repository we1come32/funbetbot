import os
import asyncio
import time

import aiogram
import loguru

import utils.setup_django
from . import telegram


async def check_categories():
    from modules.parser.parimatch import PariMatchLoader
    pm = PariMatchLoader(debug=True)
    while True:
        start_time = time.time()
        categories = await pm.parse_categories_list()
        for categoryName, categoryHref in categories.items():
            await asyncio.sleep(4)
            if categoryName.lower() in pm.allow_categories:
                result = await pm.parse_tournaments(categoryHref)
                print(categoryName, result)
            else:
                loguru.logger.debug(f"Категория {categoryName} пропущена")
        t = 300 + start_time - time.time()
        loguru.logger.debug(f"Жду {t}c.")
        await asyncio.sleep(t)


def setup():
    loop = asyncio.get_event_loop()
    loop.create_task(check_categories())


def run():
    loop = asyncio.get_event_loop()
    aiogram.executor.start_polling(telegram.dp, loop=loop)
