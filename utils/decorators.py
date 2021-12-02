import functools
import time

import loguru
from aiogram import Dispatcher
from aiogram.types import Message
from django.db import IntegrityError

from .cache import Cache
from data.models import TGUser


class RegisterMessageUser:
    _fun: None
    _cache: Cache
    _dp: Dispatcher

    @classmethod
    def set_dispatcher(cls, dp: Dispatcher):
        cls._dp = dp
        return True

    def __init__(self, function):
        self._fun = function
        self._cache = Cache('user_state')

    async def __call__(self, msg: Message, **kwargs):
        try:
            user = TGUser.objects.get(id=msg.from_user.id)
            try:
                if msg.from_user.username != '':
                    user.name = msg.from_user.username
                    user.save()
            except IntegrityError as e:
                if user.name != '':
                    user.name = ''
                    user.save()
        except TGUser.DoesNotExist:
            await msg.answer('Произошла какая-то ошибка, зарегистрируйтесь заново: /start')
            return None
        result = await self._fun(
            msg=msg,
            user=user,
            **kwargs,
        )
        return result


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

