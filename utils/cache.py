import time
from typing import Any


class Cache:
    __cache__: dict[str, dict] = {}
    cache: dict[Any, dict]
    _default_value: Any
    default_expire_time = 120
    _name: str

    def __init__(self, name: str = 'default', expire_time: int = None):
        if (cache := self.__cache__.get(name, None)) is None:
            if expire_time is None:
                expire_time = self.default_expire_time
            cache = {'data': {}, 'expire_time': expire_time}
            cache['default_value'] = self._default_value = 0
            self.__cache__[name] = cache
        self.cache = cache['data']
        self._name = name

    def get(self, *, user: int = None) -> Any:
        if user is None:
            raise ValueError("Parameter 'user' cant be None")
        if not isinstance(user, int):
            raise ValueError("Parameter 'user' must be int")
        if state := self.cache.get(user, None):
            return state['state']
        return None

    def set(self, *, user=None, state=None) -> None:
        if user is None:
            raise ValueError("Parameter 'user' cant be None")
        if not isinstance(user, int):
            raise ValueError("Parameter 'user' must be int")
        if state is None:
            raise ValueError("Parameter 'state' cant be None")
        self.cache[user] = {
            'time': time.time(),
            'state': state
        }

    @classmethod
    def set_default(cls, cache: "Cache") -> bool:
        if isinstance(cache, cls):
            cls.__cache__['default'] = cache.cache
            return True
        return False

    @classmethod
    def get_default(cls) -> "Cache":
        return cls()

    @classmethod
    def set_default_expire_time(cls, value: int) -> None:
        cls.default_expire_time = value

    def set_default_value(self, value) -> None:
        self._default_value = value
        assert self._default_value == self.__cache__[self._name]['default_value']

