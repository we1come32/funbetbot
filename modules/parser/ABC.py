import abc
import asyncio
import functools
import time
from typing import Union

from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


class Browser:
    _webDriver: webdriver.Firefox
    _opened: bool

    def __init__(self):
        logger.debug("Запуск страницы браузера")
        self._webDriver = webdriver.Firefox()
        self._opened = True
        pass

    @functools.wraps(webdriver.Firefox.get)
    async def get(self, url: str) -> None:
        self._webDriver.get(url)

    @functools.wraps(webdriver.Firefox.find_elements)
    async def find_elements(self, by=By.ID, value=None) -> list[WebElement]:
        return self._webDriver.find_elements(by=by, value=value)

    @functools.wraps(webdriver.Firefox.find_element)
    async def find_element(self, by=By.ID, value=None) -> WebElement:
        return self._webDriver.find_element(by=by, value=value)

    @functools.wraps(webdriver.Firefox.execute_script)
    async def execute_script(self, script: str, *args):
        return self._webDriver.execute_script(script=script, *args)

    @functools.wraps(webdriver.Firefox.execute_async_script )
    async def execute_async_script(self, script: str, *args):
        return self._webDriver.execute_async_script(script=script, *args)

    def is_opened(self) -> bool:
        return self._opened

    def close(self) -> None:
        if self._opened:
            self._webDriver.close()
            self._opened = False

    def __del__(self):
        self.close()


class ABCParseLoader:
    _instance = None
    _update_time: float = 600
    _last_update_time: float
    _last_update_work_time: float
    _loading: bool = False
    _data: dict
    _browser: Browser = None
    _browser_locked: bool
    _allow_categories: list[str]
    _base_url: str
    _c = 0

    def __new__(cls, *args, debug=False, **kwargs):
        if not cls._instance:
            cls._last_update_work_time = time.time()
            cls._browser = Browser()
            cls.data = {}
            cls._c = 0
            cls._instance = super(ABCParseLoader, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, debug=False):
        logger.debug(f"Инициализация парсера {self._base_url}")
        self._browser_locked = False
        if debug is False:
            self.check_update()
        self._c += 1

    @abc.abstractmethod
    async def parse_categories_list(self) -> dict[str, str]:
        """
        Метод позволит спарсить список видов спорта, по которым принимаются ставки
        :return: dict[str, str] - словарь, ключем является название вида спорта, а значением - ссылка на парсинг
          турниров по этому виду спорта
        """
        pass

    @abc.abstractmethod
    async def parse_pari(self, url: str) -> dict:
        """
        Меод позволит спарсить коэффициенты на ставки у букмекера
        :param url: str, ссылка на событие у букмекера
        :return: dict, информация о ставках в данный момент времени
        """

    @abc.abstractmethod
    async def parse_tournaments(self, url: str) -> dict:
        """
        This method need to parse any project to get information about tournaments, events and pari on all this events
        :return: dict - data of games and tournaments with pari and links
        """
        pass

    async def parse(self) -> dict:
        data = {}
        categoryList = await self.parse_categories_list()
        for categoryName, categoryUrl in categoryList.items():
            if categoryName.lower() in self._allow_categories:
                tournaments = await self.parse_tournaments(categoryUrl)
                logger.info(f"По виду спорта {categoryName!r} найдено {len(tournaments)} турниров: "
                            f"{', '.join(_ for _ in tournaments.keys())}")
                data[categoryName] = tournaments
        return data

    async def update_data(self):
        if self._loading is False:
            self._loading = True
            start_time = time.time()
            result = await self.parse()
            self._last_update_work_time = time.time() - start_time
            self._loading = False
            # Нужно парсить данные из переменной result и сравнивать их с существующими в базе данных
            pass

    def check_update(self):
        if time.time() > (self._last_update_time + self._update_time - self._last_update_work_time):
            if not self._loading:
                loop = asyncio.get_event_loop()
                loop.create_task(self.update_data())

    async def get_category(self, name: str) -> Union[dict[str, dict], None]:
        """
        Get category information
        :param name: Name of category
        :return: if a category already exists return dictionary with data about this category, tournaments
          in this category, games on all this tournaments and pari on all games in this category
          or None
        """
        # Сначала мы попробуем запустить процедуру обновления данных
        self.check_update()
        # Когда попытались запустить, возвращаем данные с прошлого парсинга
        return self._data.get(name, None)

    async def get_tournament(self, category: str, tournament: str) -> Union[dict[int, dict], None]:
        """
        Get tournament information
        :param category: Name of category
        :param tournament: Name of tournament
        :return: if a tournament already exists in this category return dictionary with data about this tournament,
          games on all this tournament and pari on all games in this tournament
          or None
        """
        if (category := await self.get_category(category)) is None:
            return category
        return category.get(tournament, None)

    async def get_event(self, category: str, tournament: str, event: int) -> Union[dict, None]:
        """
        Get event information
        :param category: Name of category
        :param tournament: Name of tournament
        :param event: EventID - ID of event in BotDataBase
        :return: if a event already exists in this tournament return dictionary with data about this event or None
        """
        if (tournament := await self.get_tournament(category=category, tournament=tournament)) is None:
            return tournament
        return tournament.get(event, None)

    def __del__(self):
        self._c -= 1
        if self._c == 0:
            self._browser.close()
