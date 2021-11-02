from typing import Any

from .cache import Cache


class User:
    user_id: int
    _cache: Cache

    def __init__(self, user_id: int):
        cache = Cache(name='user_state')
        self.state = cache.get(user=user_id) or 0
        self.user_id = user_id

    def get_state(self):
        return self._cache.get(user=self.user_id) or 0

    def set_state(self, state: Any):
        return self._cache.set(user=self.user_id, state=state)
