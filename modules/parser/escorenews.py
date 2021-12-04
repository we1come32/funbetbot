from datetime import datetime, timedelta

import loguru
import pytz
from bs4 import BeautifulSoup
import requests


def parse_event(url: str) -> dict[str, str]:
    loguru.logger.debug(f'Начинаю парсить страницу {url!r}')
    response = requests.get(url)
    html = response.text
    base_url = url.split('.com')[0] + '.com'
    soup = BeautifulSoup(html, features='html.parser')
    print(soup)
    event = soup.find('div', class_='teams-on-live')
    tmp = [_.text for _ in event.find_all('span')]
    teams = [event.find_all('span')[0].find('h2').text, event.find_all('span')[-1].find('h2').text]
    time = (datetime.strptime(tmp[1], "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)).replace(tzinfo=pytz.utc)
    tournament = soup.find(
        'main', class_='match-page'
    ).find('div', class_='header').find('div', class_='hh').find('h1').find('a').text
    status = event.find('b').text
    matchboard = list(map(int, tmp[2].split(':')))
    data = {'status': status, 'teams': teams, 'date': time,
            'matchboard': matchboard, 'url': url, 'tournament': tournament}
    loguru.logger.debug(f'Парсинг страницы {url!r} завершен.')
    return data


def parse(url: str) -> dict[str, list]:
    loguru.logger.debug(f'Начинаю парсить события со страницы {url!r}')
    eventData = {}
    for i in range(5):
        response = requests.get(url, params={'s1': i})
        base_url = url.split('.com')[0] + '.com'
        soup = BeautifulSoup(response.text, features='html.parser')
        events = soup.find('section', class_='matches').find_all('a', class_='article')
        for event in events:
            try:
                data = parse_event(base_url+event.attrs['href'])
            except:
                continue
            tournament = eventData.get(data['tournament'], list())
            tournament.append(data)
            eventData[data['tournament']] = tournament
        loguru.logger.debug(f'Парсинг страницы {url!r} завершен.')
    return eventData
