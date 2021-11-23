import datetime

from django.db import models


class TGUser(models.Model):
    id = models.IntegerField(primary_key=True, unique=True)
    status = models.IntegerField(default=True)
    balance = models.IntegerField(default=1000)
    language = models.CharField(max_length=2, default='en')
    tg_language = models.CharField(max_length=2, default='en')


class Category(models.Model):
    name = models.TextField(default='')


class SubCategory(models.Model):
    name = models.TextField(default='')
    category = models.ForeignKey(Category,
                                 on_delete=models.CASCADE,
                                 related_name='subcategories')


class Tournament(models.Model):
    name = models.TextField(default='')
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name='tournaments'
    )


class Event(models.Model):
    name = models.TextField(default='')
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='events'
    )


class Team(models.Model):
    name = models.TextField(default='')
    value = models.FloatField(default=1.0)
    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                              related_name='teams')
    start_time = models.DateTimeField(default=datetime.datetime.now)


class Bet(models.Model):
    value = models.FloatField(default=1.0)
    user = models.ForeignKey(TGUser, on_delete=models.CASCADE,
                             related_name='bets')
    team = models.ForeignKey(Team, on_delete=models.CASCADE,
                             related_name='bets')
    is_active = models.BooleanField(default=True)
