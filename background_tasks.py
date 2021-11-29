import datetime
import asyncio
import time

import loguru
import pytz
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.exceptions import RetryAfter
from django.utils import timezone
from pprint import pprint

import utils.setup_django
from data.models import *
from modules.parser.parimatch import PariMatchLoader
from modules.parser import sports_ru
from core.telegram.bot import bot


def get_date(data: list) -> datetime.datetime:
    event_date: datetime.date | None = None
    if data[0] == 'Завтра':
        event_date = timezone.now()
        event_date = datetime.date.today() + datetime.timedelta(days=1)
    elif data[0] == 'Сегодня':
        event_date = datetime.date.today()
    else:
        day, month = map(str, data[0].split())
        day = int(day)
        year = datetime.date.today().year
        months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
        month = months.index(month) + 1
        if (datetime.date.today().month != month) and (month == 1):
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
            exit(0)


allow_categories = set_cache_keys({
    'киберспорт': {
        'counter-strike': 'https://cyber.sports.ru/cs/match/{year}-{month:0>2}-{day:0>2}/',
        'dota 2': 'https://cyber.sports.ru/dota2/match/{year}-{month:0>2}-{day:0>2}/',
    },
    'футбол': 'https://www.sports.ru/football/match/{year}-{month:0>2}-{day:0>2}/',
    'хоккей': 'https://www.sports.ru/hockey/match/{year}-{month:0>2}-{day:0>2}/',
})


def check_categories() -> None:
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
                        eventModel = Event.objects.get_or_create(
                            name=' vs '.join(event['commands']),
                            date=event_date,
                            tournament=tournamentModel,
                            parimatch_link=event['href']
                        )
                        if eventModel.teams.all().count() == 0:
                            for team, teamBet, flag in zip(
                                    teams,
                                    [event['pari'][0], event['pari'][-1]],
                                    [True, False]
                            ):
                                TeamEvent.objects.create(team=team, first=flag,
                                                         event=eventModel, bet=teamBet)


def check_events() -> None:
    global allow_categories
    try:
        while True:
            events = Event.objects.filter(sports_ru_link='', not_supported=False).order_by('start_time')
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
                    for game in tournamentGames:
                        if game['date'] == '—':
                            continue
                        game.update(tournament=tournamentName)
                        teams = []
                        flag = False
                        for team in game['teams']:
                            _ = TeamName.objects.filter(name=team)
                            if len(_):
                                if len(_ := _.filter(verified=True)):
                                    teams.append(_[0])
                                else:
                                    flag = True
                            else:
                                question = models.Q(name__contains=team.split()[0])
                                flag = True
                                for _ in team.split()[1:]:
                                    question = question | models.Q(name__contains=_)
                                _teams = TeamName.objects.filter(question)
                                if len(_teams):
                                    for _ in _teams:
                                        kb = InlineKeyboardMarkup(inline_keyboard=[
                                            [
                                                InlineKeyboardButton(text="✅", callback_data="moderation.confirm"),
                                                InlineKeyboardButton(text="❌", callback_data="moderation.deny"),
                                            ]
                                        ])
                                        message: Message = message_send(
                                            chat_id=621629634,
                                            text="<b>Модерация</b>\n\n"
                                                 "<u>Возможно</u> команда "
                                                 f"<i>{_.team.names.get(primary=True).name!r}</i> "
                                                 f"имеет ещё одно название: <i>{team!r}</i>\n"
                                                 f"<a href=\"{game['url']}\">Ссылка на модерируемое событие</a>\n\n"
                                                 "Системе нужна помощь. Проверьте, пожалуйста, "
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
                        if flag:
                            continue
                        _ = Event.objects.filter(
                            models.Q(teams__team=teams[0].team),
                            models.Q(teams__team=teams[1].team),
                            start_time__gte=datetime.datetime(
                                day=event.start_time.day,
                                month=event.start_time.month,
                                year=event.start_time.year,
                            ).replace(tzinfo=pytz.utc),
                            start_time__lte=(datetime.datetime(
                                day=event.start_time.day,
                                month=event.start_time.month,
                                year=event.start_time.year,
                            ) + datetime.timedelta(days=1)).replace(tzinfo=pytz.utc)
                        )
                        if len(set(_)) == 1:
                            editEvent: Event = _[0]
                            editEvent.sports_ru_link = game['url']
                            editEvent.save()
                        else:
                            for __ in _:
                                __.not_supported = True
                                __.save()
                else:
                    event.not_supported = True
                    event.save()
                break
    except IndexError:
        pass


if __name__ == "__main__":
    pm = PariMatchLoader(debug=True)
    while True:
        start_time = time.time()
        check_events()
        check_categories()
        t = 300 + start_time - time.time()
        loguru.logger.debug(f"Жду {max(t, 1200)}c.")
        time.sleep(max(300 + start_time - time.time(), 1200))
