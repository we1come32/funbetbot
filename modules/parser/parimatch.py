import asyncio
import time

import loguru
from selenium.webdriver.common.by import By
from pprint import pprint

from . import browser

DEBUG = True
logger = loguru.logger


@loguru.logger.catch()
def load():
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
        parimatchGames = event.find_elements(By.CLASS_NAME, '_2c98cYcZ15eCL3kXBibIh_')
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
            if len(parimatchGameInfo['commands']) != 2:
                continue
            parimatchGameInfo['pari'] = [
                float(_.find_element(By.TAG_NAME, 'span').text)
                for _ in pari.find_elements(By.CLASS_NAME, 'styles_wrapper__1hqDP')[:3]
            ]
            tournament.append(parimatchGameInfo)

    # Загрузка главной страницы
    url = 'https://www.parimatch.ru/ru/'
    logger.debug(f'Приступаю к загрузке страницы {url!r}')
    browser.get(url.encode('ascii', 'ignore').decode('unicode_escape'))
    while True:
        a = browser.find_elements(By.CLASS_NAME, '_1XZKhqLNFXAPXD6Xd6ZH8U')
        if len(a) > 2:
            break
    logger.info(f'Страница {url!r} загружена')

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
        data[name] = {'href': href}
    # Принтим словарь названий категорий и его ссылок
    logger.info(f"Найдено {len(data.keys())} видов спорта, среди них: {', '.join(str(key) for key in data.keys())}")

    # Теперь нам надо узнать соревнования у необходимых категорий
    logger.debug('Приступаю к поиску соревнований')
    allowed_to_parse = [
        'Футбол',
        'Киберспорт',
        'Баскетбол',
    ]
    logger.debug(f"Список нужных категорий: {', '.join(str(key) for key in allowed_to_parse)}")
    result_data = {}
    for key, value in data.items():
        # Фильтруем ненужные категории
        if key in allowed_to_parse:
            logger.debug(f"Присупаю к парсингу {key!r}...")
            href = value['href']
            # Переходим по ссылке, нам нужны все соревнования, а не только Live-ставки
            browser.get(href)
            # Ждем загрузки страницы, рекомендуемое время загрузки от 15 до 20 секунд
            while True:
                table = browser.find_elements(By.CLASS_NAME, 'j0HqfLSChMzGBHXhVeFBN')
                time.sleep(1)
                if len(table):
                    time.sleep(4)
                    break

            # Нам все турниры ни к чему, выбираем самые популярные
            browser.find_element(
                By.CLASS_NAME, '_3dBbVyIrol6CIhTjjLNzqw'  # Нашел блок с самыми популярными
            ).find_element(
                By.TAG_NAME, 'div'  # Нашел все блоки
            ).find_element(
                By.CLASS_NAME, '_3xu_5giI9DkQFWFLlzxujC'  # Нашел кнопки
            ).click()
            logger.debug("Активировал фильтр только популярных турниров")

            # Создаем информацию по ивентам в этой игре
            gamesData = {}
            className = '_2ZZzUiMH7QsOr52RGD_non'
            if len(browser.find_elements(By.CLASS_NAME, 'ReactVirtualized__Grid__innerScrollContainer')):
                logger.debug("Соревнований слишком много, включаю механизм скролла")
                delta = 126
                old_offsetTop = -126
                c = 0
                while True:
                    for event in browser.find_elements(By.CLASS_NAME, className):
                        get_data_about_event(event)
                    value = browser.execute_script(
                        'return document.getElementsByClassName(\'ReactVirtualized__List\')[0].scrollTop;'
                    )
                    if value != old_offsetTop:
                        c += 1
                        browser.execute_script(
                            f'document.getElementsByClassName(\'ReactVirtualized__List\')[0].scroll(0, {4 * delta * c});'
                        )
                        time.sleep(4)
                        old_offsetTop = value
                    else:
                        break
                logger.debug("Скролл остановлен")
            else:
                for event in browser.find_elements(By.CLASS_NAME, className):
                    get_data_about_event(event)

            logger.info(f"В категории {key!r} найдено {len(gamesData)} соревнований")
            time.sleep(5)
            # Сохраняем информацию о турнирах в data
            result_data[key] = gamesData
        else:
            logger.debug(f"Категории {key!r} нет в списке разрешенных категорий, продолжаю поиск")
    return result_data
