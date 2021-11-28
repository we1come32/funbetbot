import os
import abc
import functools
import time
from typing import Union

from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


class Browser:
    _webDriver: Union[webdriver.Chrome, webdriver.Firefox]
    _opened: bool = False

    def __init__(self):
        debug = bool(os.environ.get('DEBUG', True))
        logger.debug(f"Значение параметра DEBUG: {debug}")
        if debug:
            logger.debug("Запуск страницы браузера FireFox")
            self._webDriver = webdriver.Firefox()
        else:
            logger.debug("Установка параметров запуска Google Chrome")

            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--window-size=1420,1080')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')

            logger.debug("Запуск страницы браузера Google Chrome")
            self._webDriver = webdriver.Chrome(chrome_options=chrome_options)

        self._opened = True

    @functools.wraps(webdriver.Firefox.get)
    def get(self, url: str) -> None:
        self._webDriver.get(url)

    @functools.wraps(webdriver.Firefox.find_elements)
    def find_elements(self, by=By.ID, value=None) -> list[WebElement]:
        return self._webDriver.find_elements(by=by, value=value)

    @functools.wraps(webdriver.Firefox.find_element)
    def find_element(self, by=By.ID, value=None) -> WebElement:
        return self._webDriver.find_element(by=by, value=value)

    @functools.wraps(webdriver.Firefox.execute_script)
    def execute_script(self, script: str, *args):
        return self._webDriver.execute_script(script=script, *args)

    @functools.wraps(webdriver.Firefox.execute_async_script )
    def execute_async_script(self, script: str, *args):
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
        self._c += 1

    @abc.abstractmethod
    def parse_categories_list(self) -> dict[str, str]:
        """
        Метод позволит спарсить список видов спорта, по которым принимаются ставки
        :return: dict[str, str] - словарь, ключем является название вида спорта, а значением - ссылка на парсинг
          турниров по этому виду спорта
        """
        pass

    @abc.abstractmethod
    def parse_pari(self, url: str) -> dict:
        """
        Меод позволит спарсить коэффициенты на ставки у букмекера
        :param url: str, ссылка на событие у букмекера
        :return: dict, информация о ставках в данный момент времени
        """

    @abc.abstractmethod
    def parse_tournaments(self, url: str) -> dict:
        """
        This method need to parse any project to get information about tournaments, events and pari on all this events
        :return: dict - data of games and tournaments with pari and links
        """
        pass

    def parse(self) -> dict:
        data = {}
        categoryList = self.parse_categories_list()
        for categoryName, categoryUrl in categoryList.items():
            if categoryName.lower() in self._allow_categories:
                tournaments = self.parse_tournaments(categoryUrl)
                logger.info(f"По виду спорта {categoryName!r} найдено {len(tournaments)} турниров: "
                            f"{', '.join(_ for _ in tournaments.keys())}")
                data[categoryName] = tournaments
        return data

    def __del__(self):
        self._c -= 1
        if self._c == 0:
            self._browser.close()
