import loguru
from bs4 import BeautifulSoup
import requests


def parse(url: str) -> dict[str, list]:
    response = requests.get(url)
    base_url = url.split('.ru')[0] + '.ru'
    soup = BeautifulSoup(response.text, features='html.parser')
    try:
        soup.find('div', class_='match-center').find('div', class_='tabs-container')
        better_flag = False
    except AttributeError:
        better_flag = True
    data = {}
    loguru.logger.debug(f"Начинаю парсить {url!r}")
    if better_flag:
        tournaments = soup.find_all('div', class_='desktop-teaser__section')
        for tournament in tournaments:
            try:
                tournamentName = tournament.find('a', class_='desktop-teaser__tournament').text[1:]
            except IndexError:
                continue
            matches = tournament.find('div', class_='delimited-match-list')\
                .find_all('div', class_='match-teaser')
            data[tournamentName] = []
            for match in matches:
                try:
                    link: str = match.find('a', class_='match-teaser__link').attrs.get('href')
                    if link.startswith('/'):
                        link = base_url + link
                except AttributeError:
                    link = ''
                status = match.find('div', class_='match-teaser__info').text
                teams = []
                for teamElement in match.find_all('div', class_='match-teaser__team'):
                    team: str = teamElement.text.replace('\n', '')
                    if team.startswith(' '):
                        team = team[1:]
                    if team.endswith(' '):
                        team = team[:-1]
                    teams.append(team)
                data[tournamentName].append({
                    'url': link,
                    'status': status.split('.')[1][1:-1],
                    'date': status.split('.')[0][1:],
                    'teams': teams,
                })
                if data[tournamentName][-1]['status'] == 'Завершен':
                    result = [
                        int(_.text)
                        for _ in match.find('div', class_='match-teaser__team-score').find_all('span')[::2]
                    ]
                    data[tournamentName][-1]['result'] = {
                        team[1:-1]: value
                        for team, value in zip(teams, result)
                    }
    else:
        tournaments = soup.find('div', class_='match-center').find('li', class_='panel')
        tournamentNames = tournaments.find_all('div', class_='light-gray-title')
        tournamentGames = tournaments.find_all('table', class_='matches-table')
        for tournamentNameElement, tournamentGamesTable in zip(tournamentNames, tournamentGames):
            try:
                tournamentName = tournamentNameElement.find('a').text
            except AttributeError:
                continue
            data[tournamentName] = []
            tournamentGamesInformation = tournamentGamesTable.find_all('tr')
            for gameElement in tournamentGamesInformation:
                elements = gameElement.find_all('td')
                link = elements[3].find('a').attrs.get('href')
                if link.startswith('/'):
                    link = base_url + link
                teams = []
                for teamElement in elements[2:5:2]:
                    team: str = teamElement.text.replace('\n', '')
                    if team.startswith(' '):
                        team = team[1:]
                    if team.endswith(' '):
                        team = team[:-1]
                    teams.append(team)
                data[tournamentName].append({
                    'url': link,
                    'status': elements[1].text,
                    'date': elements[0].text,
                    'teams': teams
                })
                if data[tournamentName][-1]['status'] == 'Завершен':
                    data[tournamentName][-1]['result'] = elements[3].text.replace('\n', ''),
                if len(elements[3].find_all('span')):
                    data[tournamentName][-1]['result'] = {
                        teams[0]: int(elements[3].find_all('span')[0].text),
                        teams[1]: int(elements[3].find_all('span')[1].text)
                    }
    return data


def parse_event(url: str) -> dict:
    loguru.logger.debug(f'Начинаю парсить страницу {url!r}')
    response = requests.get(url)
    html = response.text
    base_url = url.split('.ru')[0] + '.ru'
    soup = BeautifulSoup(html, features='html.parser')
    header = soup.find('head').find('title')
    if header.text == 'Страница не найдена':
        loguru.logger.debug(f"Page not found. Code: {response.status_code}")
        return {'status': 'error', 'error_code': 404}
    event = soup.find('div', class_='match-summary')
    try:
        if event is not None:
            teams = [
                _.find('span', class_='match-summary__team-name').text
                for _ in event.find_all('div', class_='match-summary__team')
            ]
            stateObject = event.find('div', class_='match-summary__state')
            stateStatus = stateObject.find('span', class_='match-summary__state-status').text
            data = {
                'status': stateStatus.capitalize(),
                'teams': teams,
            }
            if stateStatus.lower().split()[0].startswith('заверш'):
                data.update(matchboard=[int(_.text) for _ in stateObject.find_all('span', class_='matchboard__card-game')])
        else:
            event = soup.find('div', class_='two-commands')
            teams = [
                _.find('span', itemprop='name').text
                for _ in event.find_all('div', class_='command')
            ]
            stateObject = event.find('div', class_='game-info')
            stateStatus = stateObject.find('div', class_='js-match-status').text
            data = {
                'status': stateStatus.capitalize(),
                'teams': teams,
            }
            if stateStatus.lower().split()[0].startswith('заверш'):
                data.update(matchboard=list(map(int, stateObject.find('div', class_='js-match-score').text.split(" : "))))
        loguru.logger.debug(f'Парсинг страницы {url!r} завершен. Возвращено: {data!r}')
        return data
    except BaseException:
        return {'status': 'error', 'error_code': 404}
