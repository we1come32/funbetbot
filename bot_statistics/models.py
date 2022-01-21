from datetime import timedelta, datetime

from aiogram import types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from data.models import TGUser
from utils import message_send


class TGProfileStatistic(models.Model):
    user = models.OneToOneField(TGUser, on_delete=models.CASCADE, related_name='statistic')
    activity = models.BooleanField(default=True)
    last_activity = models.DateField(default=timezone.now)


class Activity(models.Model):
    date = models.DateField(default=timezone.now, verbose_name='Дата', unique=True)
    telegram = models.IntegerField(default=0, verbose_name='Telegram')

    @classmethod
    def update(cls):
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
                     # "Как раз есть интересные события для тебя"
                     "",
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
