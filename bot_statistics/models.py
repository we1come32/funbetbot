from datetime import timedelta, datetime

from aiogram import types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from django.db import models
from django.db.models import QuerySet, Count
from django.utils import timezone

from data.models import TGUser, Bet, Category, Event
from utils import message_send


class TGProfileStatistic(models.Model):
    user = models.OneToOneField(TGUser, on_delete=models.CASCADE, related_name='statistic', verbose_name='Пользователь')
    activity = models.BooleanField(default=True, verbose_name='Активность')
    last_activity = models.DateField(default=timezone.now, verbose_name='Дата последней активности')

    def get_current_interesting_events(self, max_count: int = None) -> list[Event]:
        """
        Функция собирает статистику по предыдущим ставкам за 4 месяца и выдает список наиболее актуальных категорий,
        по которым необходимо рекомендовать ставки
        :return: Список поддерживаемых событий по интересующим пользователя событиям
        """
        if max_count is None:
            max_count = 10
        start_date = timezone.now()-timedelta(days=120)

        # Поиск категорий, в которых пользователь делал ставки за ближайшие 120 дней
        categories = Category.objects.filter(
            subcategories__tournaments__events__teams__bets__created_date__gte=start_date,
            user=self.user
        )
        categories_list = list(categories)

        # Ставки пользователя за ближайшие 120 дней
        bets: QuerySet[Bet] = self.user.user.bets.filter(created_date__gte=start_date)

        # Сбор статистики по категориям и событиям
        unique_categories_dict: dict[Category, dict] = {}
        for category in set(categories):
            unique_categories_dict[category] = {'count': categories_list.count(category),
                                                'bets': {'list': [], 'wins': 0, 'loses': 0, 'not_ended': 0}}
        for bet in bets:
            unique_categories_dict[bet.team.event.tournament.subcategory.category]['bets']['list'].append(bet)
            if bet.payed:
                if bet.winner:
                    unique_categories_dict[bet.team.event.tournament.subcategory.category]['bets']['wins'] += 1
                else:
                    unique_categories_dict[bet.team.event.tournament.subcategory.category]['bets']['loses'] += 1
            else:
                unique_categories_dict[bet.team.event.tournament.subcategory.category]['bets']['not_ended'] += 1
        unique_categories = list(set(categories))
        unique_categories.sort(key=lambda categoty: unique_categories_dict[category]['count'], reverse=True)
        count = max_count / min(3, len(unique_categories)) + 1
        interesting_events: list[Event] = []

        # Подборка событий
        c: int = 0
        for category in unique_categories[:3]:
            events: QuerySet[Event] = Event.objects.filter(~models.Q(sports_ru_link=''), ~models.Q(parimatch_link=''),
                                                         start_time__gte=timezone.now() + timedelta(hours=3),
                                                         tournament__subcategory__categoty=category, )
            for event in events[:count]:
                if c < max_count:
                    c += 1
                    interesting_events.append(event)
        return interesting_events


class Activity(models.Model):
    date = models.DateField(default=timezone.now, verbose_name='Дата', unique=True)
    telegram = models.IntegerField(default=0, verbose_name='Telegram')

    @classmethod
    def update(cls):
        """
        Обновление статистики активности пользователей у системы
        :return:
        """
        kb = InlineKeyboardMarkup(resize_keyboard=True, inline_keyboard=[[
            InlineKeyboardButton(text='💴 Сделать ставку', callback_data='commands.bet'),
        ], [
            InlineKeyboardButton(text='💴 Баланс', callback_data='commands.player.balance'),
            InlineKeyboardButton(text='🔥 Рейтинг', callback_data='commands.rating'),
        ]])
        users: QuerySet[TGProfileStatistic] = TGProfileStatistic.objects.filter(last_activity__lte=timezone.now() - timedelta(days=13, hours=20))
        for user in users:
            message_send(
                chat_id=user.user.user_id,
                text="Привет! От тебя давно не было активности. Может, сделаем ещё одну ставку? "
                     "Как раз есть интересные события для тебя",
                reply_markup=kb,
                disable_notification=True,
                parse_mode=types.ParseMode.HTML
            )
            user.activity = False
            user.save()
        try:
            cls.objects.get(date=timezone.now)
        except (cls.DoesNotExist):
            cls.objects.create(telegram=TGProfileStatistic.objects.filter(activity=True).count())
