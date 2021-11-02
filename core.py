import aiogram

import config

_bot = aiogram.Bot(token=config.token)

ds = aiogram.Dispatcher(_bot)


def run():
    aiogram.executor.start_polling(ds)
