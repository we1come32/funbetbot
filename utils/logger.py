from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from loguru import logger
from loguru._logger import Logger


class LoggerMiddleware(BaseMiddleware):
    _logger: Logger

    def __init__(self):
        self._logger = logger.bind(module='LoggerMiddleware')
        super(LoggerMiddleware, self).__init__()

    async def debug(self, text: str) -> None:
        self._logger.debug(text)

    async def on_process_message(self, message: types.Message, data: dict) -> None:
        await self.debug(f"Message from user{message.from_user.id}: {message.as_json()}")
