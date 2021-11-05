import asyncio
import time

import loguru
from selenium.webdriver.common.by import By
from pprint import pprint

from .ABC import ABCParseLoader

logger = loguru.logger


class PariMatchLoader(ABCParseLoader):
    """
    Парсер сервиса PariMatch, собирает данные с PariMatch читывая все тайминги загрузки данных
    """
    _base_url = 'https://www.parimatch.ru/ru/'
    _update_time: float = 600
    _last_update_time: float
    _last_update_work_time: float
    _allow_categories: list[str] = [
        # 'футбол',
        'киберспорт',
    ]

    @logger.catch
    async def parse_pari(self, url: str) -> dict:
        """
        Меод позволит спарсить коэффициенты на ставки у букмекера
        :param url: str, ссылка на событие у букмекера
        :return: dict, информация о ставках в данный момент времени
        """
        # Ожидание окончания блокировки браузера
        while self._browser_locked:
            continue
        # Ставим блокировку
        self._browser_locked = True

        # Переходим на страницу матча
        await self._browser.get(url)
        while len(await self._browser.find_elements(By.CLASS_NAME, '_1XZKhqLNFXAPXD6Xd6ZH8U')) > 2:
            continue
        # Ждём загрузку странички
        await asyncio.sleep(10)
        # input("Жмакни сюка по Enter: ")
        if len(event := (await self._browser.find_elements(By.CLASS_NAME, '_2NQKPrPGvuGOnShyXYTla8'))) > 0:
            # Матч всё ещё идет
            result = {'status': 'ok', 'pari': {
                item.find_element(By.CLASS_NAME, '_3EDVkDYUVqPDxEU_A8ZfAY').text: float(
                    item.find_element(By.TAG_NAME, 'span').text)
                for item in event[0].find_element(
                    By.CLASS_NAME, '_1QfZsk-ZjPpQv22dKDJ4f5'
                ).find_elements(By.CLASS_NAME, '_1_ZGmoK5sTgjPZ6bQDpAmK')
            }}
        else:
            # Матч завершился
            result = {'status': 'ended'}
        self._browser_locked = False
        return result

    @logger.catch
    async def parse_tournaments(self, url: str) -> dict:
        """
        This method need to parse any project to get information about tournaments, events and pari on all this events
        :return: dict - data of games and tournaments with pari and links
        """
        def get_data_about_event(event):
            # Получаем название турнира вместе с его игрой
            name = event.find_element(By.TAG_NAME, 'span').text
            # Выдергиваем название игры из 'name'
            gameName = name.split('.')[0]
            # Теперь проверяем на существование такой игры
            if game := gamesData.get(gameName, None) is None:
                gamesData[gameName] = game = {}
            # Получаем название турнира
            tournamentName = name[len(gameName) + 2:]
            # Проверяем на повторение турнира чтобы дважды инфу не добавлять в данные об играх
            if (game := gamesData.get(gameName, None)).get(tournamentName, None) is not None:
                return None
            game[tournamentName] = tournament = []
            # Получаем список событий в этом турнире
            parimatchGames = event.find_elements(By.CLASS_NAME, 'styles_wrapper__BfdYz')
            logger.debug(f"Tournament {tournamentName!r} in game {gameName!r} has {len(parimatchGames)} events")
            # Проходим по каждому событию
            for parimatchGameObject in parimatchGames:
                parimatchGameInfo = {}
                gameInfo = parimatchGameObject.find_elements(By.CLASS_NAME, 'styles_wrapper__389ZC')
                if len(gameInfo) != 1:
                    continue
                gameInfo = gameInfo[0]
                pari = parimatchGameObject.find_element(By.CLASS_NAME, 'styles_markets-wrapper__2dylh')
                parimatchGameInfo['date'] = gameInfo.find_element(By.TAG_NAME, 'span').text
                parimatchGameInfo['commands'] = [
                    _.find_element(By.TAG_NAME, 'span').text
                    for _ in gameInfo.find_elements(By.CLASS_NAME, 'styles_wrapper__W25NH')
                ]
                parimatchGameInfo['href'] = parimatchGameObject.get_attribute('href')
                if len(parimatchGameInfo['commands']) != 2:
                    continue
                parimatchGameInfo['pari'] = [
                    float(_.find_element(By.TAG_NAME, 'span').text)
                    for _ in pari.find_element(
                        By.CLASS_NAME, 'styles_market-wrapper__2ehw1'
                    ).find_elements(
                        By.CLASS_NAME, 'styles_wrapper__1hqDP'
                    )
                ]
                tournament.append(parimatchGameInfo)

        while self._browser_locked:
            continue
        self._browser_locked = True
        await self._browser.get(url)
        # Ждем загрузки страницы, рекомендуемое время загрузки от 15 до 20 секунд
        while True:
            table = await self._browser.find_elements(By.CLASS_NAME, 'j0HqfLSChMzGBHXhVeFBN')
            time.sleep(1)
            if len(table):
                time.sleep(4)
                break

        # Нам все турниры ни к чему, выбираем самые популярные
        # Нашел блок с самыми популярными
        popularBlock = await self._browser.find_element(By.CLASS_NAME, '_3dBbVyIrol6CIhTjjLNzqw')
        popularBlock.find_element(
            By.TAG_NAME, 'div'  # Нашел все блоки
        ).find_element(
            By.CLASS_NAME, '_3xu_5giI9DkQFWFLlzxujC'  # Нашел кнопки
        ).click()
        logger.debug("Активировал фильтр только популярных турниров")

        # Создаем информацию по ивентам в этой игре
        gamesData = {}
        className = '_2ZZzUiMH7QsOr52RGD_non'
        if len(await self._browser.find_elements(By.CLASS_NAME, 'ReactVirtualized__Grid__innerScrollContainer')):
            logger.debug("Соревнований слишком много, включаю механизм скролла")
            delta = 126
            old_offsetTop = -126
            c = 0
            while True:
                for event in await self._browser.find_elements(By.CLASS_NAME, className):
                    get_data_about_event(event)
                value = await self._browser.execute_script(
                    'return document.getElementsByClassName(\'ReactVirtualized__List\')[0].scrollTop;'
                )
                if value != old_offsetTop:
                    c += 1
                    await self._browser.execute_script(
                        f'document.getElementsByClassName(\'ReactVirtualized__List\')[0].scroll(0, {4 * delta * c});'
                    )
                    time.sleep(4)
                    old_offsetTop = value
                else:
                    break
            logger.debug("Скролл остановлен")
        else:
            for event in await self._browser.find_elements(By.CLASS_NAME, className):
                get_data_about_event(event)
        # Сохраняем информацию о турнирах в data
        self._browser_locked = False
        return gamesData

    @logger.catch
    async def parse_categories_list(self) -> dict[str, str]:
        """
        Метод позволит спарсить список видов спорта, по которым принимаются ставки
        :return: dict[str, str] - словарь, ключем является название вида спорта, а значением - ссылка на парсинг
          турниров по этому виду спорта
        """

        while self._browser_locked:
            continue
        self._browser_locked = True
        # Загрузка главной страницы
        logger.debug(f'Приступаю к загрузке страницы {self._base_url!r}')
        await self._browser.get(self._base_url.encode('ascii', 'ignore').decode('unicode_escape'))
        while True:
            a = await self._browser.find_elements(By.CLASS_NAME, '_1XZKhqLNFXAPXD6Xd6ZH8U')
            if len(a) > 2:
                break
        logger.info(f'Страница {self._base_url!r} загружена')

        # Поиск списка категорий с сылками на них
        logger.debug(f'Приступаю к поиску видов спорта')
        data = {}
        for element in a[2:]:
            href = element.get_attribute('href')
            name = element.find_elements(By.TAG_NAME, 'span')[-1].text
            # Фильтрация Live-ставок, нам они не нужны
            if href.endswith('/live'):
                # Убираем суффикс '/live'
                href = href[:-5]
            # Сохраняем названия категорий с их ссылками
            data[name] = href
        # Принтим словарь названий категорий и его ссылок
        logger.info(f"Найдено {len(data.keys())} видов спорта, среди них: {', '.join(str(key) for key in data.keys())}")
        self._browser_locked = False
        return data
