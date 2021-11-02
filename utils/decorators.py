import functools
import time

import loguru
from aiogram.types import Message

from .cache import Cache


class Register_User:
    _fun: None
    _cache: Cache

    def __init__(self, function):
        self._fun = function
        self._cache = Cache('user_state')

    def __call__(self, msg: Message):
        return self._fun(user=msg.chat.id, chat=msg.chat, message=msg)


class FixParameterTypes:
    args: tuple[type]
    kwargs: dict[str, type]

    def __init__(self, *args: type, **kwargs: type):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, function):

        @functools.wraps(function)
        async def fixed_function(*args, **kwargs):
            # Проверка аргументов
            assert len(args) == len(self.args)
            for arg1, arg2 in zip(args, self.args):
                assert type(arg1) == arg2
            # Проверка параметров
            assert len(self.kwargs) == len(kwargs)
            for key, value in kwargs.values():
                assert self.kwargs.get(key) is not None
                assert self.kwargs.get(key) == value
            # Проверка завершена
            return await function(*args)

        return fixed_function


class Timer:

    def __init__(self):
        pass

    def __call__(self, function):
        @functools.wraps(function)
        async def timer(*args, **kwargs):
            st = time.time()
            result = await function(*args, **kwargs)
            t = time.time()
            loguru.logger.debug(f"Work time {function.__name__!r} = {st-t}c.")
        return timer


class SpecialTypesOfUsers:
    _user: bool
    _bot: bool
    _chat: bool

    def __init__(self, user: bool = False, bot: bool = False, chat: bool = False):
        self._user = user
        self._bot = bot
        self._chat = chat

    def __call__(self, function):

        @functools.wraps(function)
        async def func(msg: Message):
            if self._chat is False and msg.chat.type == 'group':
                return False
            if self._bot is False and msg.via_bot:
                return False
            if self._user is False and msg.chat.type == 'private':
                return False
            return await function(msg)

        return func
