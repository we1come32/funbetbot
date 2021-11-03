from typing import Any

from aiogram.dispatcher.filters import Filter
from aiogram import types


class FunctionFilter(Filter):
    _function: Any

    def __init__(self, function):
        self._function = function

    async def check(self, msg: types.Message) -> bool:
        return True
