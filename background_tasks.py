import asyncio
import datetime
import time

import loguru
import pytz
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.exceptions import RetryAfter
from django.utils import timezone

import config
import utils.setup_django
from data.models import *
from modules.parser.parimatch import PariMatchLoader
from modules.parser import sports_ru
from core.telegram.bot import bot


new_line = "\n"


def get_date(data: list) -> datetime.datetime:
    if data[0] == 'Завтра':
        event_date = timezone.now().date() + datetime.timedelta(days=1)
    elif data[0] == 'Сегодня':
        event_date = timezone.now().date()
    else:
        day, month = map(str, data[0].split())
        day = int(day)
        year = timezone.now().date().year
        months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
        month = months.index(month) + 1
        if (timezone.now().date().month != month) and (month == 1):
            year += 1
        event_date = datetime.date(year, month, day)
    event_time = map(int, data[1].split(':'))
    event_time = datetime.time(*event_time)
    return datetime.datetime(
        year=event_date.year,
        month=event_date.month,
        day=event_date.day,
        hour=event_time.hour,
        minute=event_time.minute
    ).replace(tzinfo=pytz.utc)


def set_cache_keys(data: dict) -> dict:
    if type(data) is not dict:
        return data
    data['keys'] = list(data.keys())
    for key, item in data.items():
        data[key] = set_cache_keys(item)
    return data


def message_send(**kwargs) -> Message:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()
    while True:
        try:
            return loop.run_until_complete(bot.send_message(**kwargs))
        except RetryAfter as e:
            timer = int(str(e).split('.')[1].split()[2])
            time.sleep(timer)


loguru.logger.add('File.log')
allow_categories = set_cache_keys({
    'киберспорт': {
        'counter-strike': 'https://cyber.sports.ru/cs/match/{year}-{month:0>2}-{day:0>2}/',
        'dota 2': 'https://cyber.sports.ru/dota2/match/{year}-{month:0>2}-{day:0>2}/',
    },
    'футбол': 'https://www.sports.ru/football/match/{year}-{month:0>2}-{day:0>2}/',
    'хоккей': 'https://www.sports.ru/hockey/match/{year}-{month:0>2}-{day:0>2}/',
})


def check_new_events() -> None:
    global allow_categories, pm
    categories = pm.parse_categories_list()
    for categoryName, categoryHref in categories.items():
        if categoryName.lower() in allow_categories['keys']:
            parse_link: str | None = None
            allow_category_data = allow_categories[categoryName.lower()]
            subcategories = pm.parse_tournaments(categoryHref)
            if type(allow_category_data) is str:
                parse_link = allow_category_data
            categoryModel = Category.objects.get_or_create(name=categoryName.lower())
            for subcategoryName, subcategoryData in subcategories.items():
                if type(allow_category_data) is dict:
                    if subcategoryName.lower() not in allow_category_data['keys']:
                        continue
                    parse_link = allow_category_data[subcategoryName.lower()]
                if parse_link is None:
                    continue
                subcategoryModel = SubCategory.objects.get_or_create(
                    name=subcategoryName.lower(),
                    category=categoryModel
                )
                for tournamentName, tournamentList in subcategoryData.items():
                    tournamentModel = Tournament.objects.get_or_create(
                        name=tournamentName,
                        subcategory=subcategoryModel
                    )
                    for event in tournamentList:
                        event_date = get_date(event['date'])
                        teams = []
                        for teamName in event['commands']:
                            if value := TeamName.objects.filter(name=teamName, verified=True):
                                teams.append(value[0].team)
                            else:
                                team = Team.objects.create()
                                TeamName.objects.create(name=teamName, team=team,
                                                        verified=True, primary=True)
                                teams.append(team)
                        if len(event['pari']) == 3:
                            if Team.objects.filter(names__name='Ничья').count():
                                draw = Team.objects.get(names__name='Ничья')
                            else:
                                draw = Team.objects.create()
                                TeamName.objects.create(team=draw, name='Ничья',
                                                        primary=True, verified=True, denied=False)
                            teams = [
                                teams[0],
                                draw,
                                teams[1]
                            ]
                        eventModel = Event.objects.get_or_create(
                            name=' vs '.join(event['commands']),
                            date=event_date,
                            tournament=tournamentModel,
                            parimatch_link=event['href']
                        )
                        if eventModel.teams.all().count() == 0:
                            for team, teamBet, flag in zip(
                                    teams,
                                    event['pari'],
                                    [True, *([False] * (len(event['pari']) - 1))]
                            ):
                                TeamEvent.objects.create(team=team, first=flag,
                                                         event=eventModel, bet=teamBet)


def moderate_sports_game(tournamentName: str, tournamentGames: list, event: Event) -> None:
    for game in tournamentGames:
        if game['date'] == '—':
            continue
        game.update(tournament=tournamentName)
        for team in game['teams']:
            _ = TeamName.objects.filter(name=team, verified=True,
                                        team__events__event__tournament=event.tournament)
            if len(_) == 0:
                banWords = ['esports', 'team', 'gaming', 'мхк', 'or', 'спартак', 'динамо', 'сити', 'арсенал',
                            'юнайтед', 'цска', 'реал', 'in', 'in', 'u-19', 'u-20', 'вест', 'локомотив',
                            'esport', 'of', ]
                _flag = True
                question: models.Q | None = None
                for _ in team.split():
                    if _.lower() not in banWords and len(_) > 1:
                        if _flag:
                            _flag = False
                            question = models.Q(name__contains=_)
                        else:
                            question = question | models.Q(name__contains=_)
                try:
                    _teams = TeamName.objects.filter(question, verified=True,
                                                     team__events__event__tournament=event.tournament)
                except TypeError:
                    continue
                _teams_keys = {}
                if len(_teams):
                    for _ in _teams:
                        if _teams_keys.get(_.team.pk, False):
                            continue
                        _teams_keys[_.team.pk] = True
                        if _.team.names.filter(name=team).count() == 0:
                            kb = InlineKeyboardMarkup(inline_keyboard=[
                                [
                                    InlineKeyboardButton(text="✅", callback_data="moderation.confirm"),
                                    InlineKeyboardButton(text="❌", callback_data="moderation.deny"),
                                ]
                            ])
                            message: Message = message_send(
                                chat_id=config.CHAT_ID,
                                text="<b>Модерация</b>\n\n"
                                     "<u>Возможно</u> команда "
                                     f"<i>{_.team.names.get(primary=True).name!r}</i> "
                                     f"имеет ещё одно название: <i>{team!r}</i>\n"
                                     f"<a href=\"{game['url']}\">Ссылка на модерируемое событие</a>\n\n"
                                     "Игры команды (с ссылками на PariMatch):\n"
                                     f"""{f'{new_line}'.join(
                                         f'{number+1}) <a href="{event.event.parimatch_link}">{event.event.name}</a>'
                                         for number, event in enumerate(_.team.events.all())
                                     )}"""
                                     "\n\nСистеме нужна помощь. Проверьте, пожалуйста, "
                                     "название команды собственноручно\n\nСпасибо",
                                reply_markup=kb,
                                disable_notification=True,
                                parse_mode=types.ParseMode.HTML
                            )
                            TeamModeration.objects.create(
                                name=TeamName.objects.create(
                                    name=team,
                                    team=_.team
                                ),
                                message_id=message.message_id
                            )
        teams = []
        for team in game['teams']:
            teamNames = TeamName.objects.filter(name=team, verified=True,
                                                team__events__event__tournament=event.tournament)
            for _ in teamNames:
                if _.team not in teams:
                    teams.append(_.team)
        if len(set(teams)) != 2:
            continue
        _ = teams[0].events.filter(event__teams__team=teams[1])
        if len(set(_)) == 1:
            editEvent: TeamEvent = _[0]
            if editEvent.event.sports_ru_link == '':
                message_send(
                    chat_id=config.CHANNEL_ID,
                    text="<b>Новое событие!</b>\n"
                         f"- Вид спорта: {editEvent.event.tournament.subcategory.category.name!r}\n"
                         f"- Подкатегория: {editEvent.event.tournament.subcategory.name!r}\n"
                         f"- Турнир: {editEvent.event.tournament.name!r}\n"
                         f"- Дата: {editEvent.event.start_time.strftime('%c')}\n\n"
                         "Коэффициенты:"
                         f"""  {''.join(
                             f"{new_line}  {_}" 
                             for _ in editEvent.event.teams.all()
                         )}""",
                    disable_notification=True,
                    parse_mode=types.ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text='Перейти к боту', url='https://t.me/virtualbetbot'),
                    ], [
                        InlineKeyboardButton(text='🔗 PariMatch', url=editEvent.event.parimatch_link),
                        InlineKeyboardButton(text='🔗 Sports.Ru', url=game['url']),
                    ]])
                )
                editEvent.event.sports_ru_link = game['url']
                editEvent.event.save()


def check_event_links() -> None:
    global allow_categories
    try:
        while True:
            events = Event.objects.filter(sports_ru_link='').order_by('start_time')
            if not events:
                break
            for event in events:
                if event.teams.filter(team__names__verified=False).count():
                    continue
                url: dict | str = allow_categories[event.tournament.subcategory.category.name]
                if type(url) is dict:
                    url: str = url[event.tournament.subcategory.name]
                data = sports_ru.parse(url.format(
                    day=event.start_time.day,
                    month=event.start_time.month,
                    year=event.start_time.year
                ))
                for tournamentName, tournamentGames in data.items():
                    moderate_sports_game(tournamentName, tournamentGames, event)
            break
    except IndexError:
        pass


def check_old_events() -> None:
    events = Event.objects.filter(~models.Q(sports_ru_link='') &
                                  models.Q(start_time__lte=timezone.now()),
                                  ended=False)
    for event in events:
        data = sports_ru.parse_event(event.sports_ru_link)
        data.update(url=event.sports_ru_link)
        if data['status'].lower().split()[0].startswith('заверш'):
            matchboard = data['matchboard']
            if matchboard[0] == matchboard[1]:
                win_team = event.teams.get(team__names__name='Ничья')
            elif matchboard[0] > matchboard[1]:
                win_team = event.teams.get(team__names__name=data['teams'][0])
            else:
                win_team = event.teams.get(team__names__name=data['teams'][1])
            event.win(win_team)
        else:
            print(data)


if __name__ == "__main__":
    pm = PariMatchLoader()
    while True:
        start_time = time.time()
        loguru.logger.debug(f"Начинается поиск новых событий")
        check_new_events()
        loguru.logger.debug(f"Поиск новых событий завершен. Приступаю к поиску связей событий с событиями на sports")
        check_event_links()
        loguru.logger.debug(f"Закончился поиск связей событий с событиями на sports. "
                            f"Начинается проверка на окончание событий")
        check_old_events()
        t = 300 + start_time - time.time()
        loguru.logger.debug(f"Проверка на окончание событий завершена. Жду {max(t, 300)}c. до следующего цикла")
        time.sleep(max(300 + start_time - time.time(), 300))
