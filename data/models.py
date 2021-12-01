import datetime
from typing import Union

from django.db import models
from django.utils import timezone

from . import managers


class TGUser(models.Model):
    class Meta:
        verbose_name_plural = "Пользователи Telegram"

    id = models.IntegerField(primary_key=True, unique=True, verbose_name="ID")
    name = models.CharField(max_length=255, default='', verbose_name="Имя Telegram")
    status = models.BooleanField(default=True, verbose_name="Статус активности аккаунта")
    admin = models.BooleanField(default=False, verbose_name="Администратор")
    balance = models.BigIntegerField(default=1000, verbose_name="Баланс")
    language = models.CharField(max_length=2, default='en', verbose_name="Языковой пакет")
    tg_language = models.CharField(max_length=2, default='en',
                                   verbose_name="Языковой пакет в Telegram")

    def __str__(self):
        if self.name:
            return self.name
        return f"user{self.id}"


class Category(models.Model):
    class Meta:
        verbose_name_plural = "Категории видов спорта"

    name = models.TextField(default='', verbose_name="Название")
    objects = managers.CategoryManager()

    def __str__(self):
        return f"{self.name.capitalize()}"


class SubCategory(models.Model):
    class Meta:
        verbose_name_plural = "Подкатегории"

    name = models.TextField(default='', verbose_name="Название")
    category = models.ForeignKey(Category,
                                 on_delete=models.CASCADE,
                                 related_name='subcategories',
                                 verbose_name="Категория")
    objects = managers.CategoryManager()

    def __str__(self):
        return f"{self.category} -> {self.name.capitalize()}"


class Tournament(models.Model):
    class Meta:
        verbose_name_plural = "Турниры"

    name = models.TextField(default='', verbose_name="Название")
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name='tournaments',
        verbose_name="Подкатегория"
    )
    objects = managers.CategoryManager()

    def __str__(self):
        return f"{self.subcategory} -> {self.name}"


class Event(models.Model):
    class Meta:
        verbose_name_plural = "События"

    name = models.TextField(default='', verbose_name="Событие")
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name="Турнир"
    )
    parimatch_link = models.CharField(
        max_length=100,
        default='',
        verbose_name="Ссылка на PariMatch",
        blank=True
    )
    sports_ru_link = models.CharField(
        max_length=100,
        default='',
        verbose_name="Ссылка на Sports",
        blank=True
    )
    start_time = models.DateTimeField(
        default=datetime.datetime.utcnow,
        verbose_name="Время начала игры"
    )
    ended = models.BooleanField(
        default=False,
        verbose_name="Статус окончания события",
        blank=True
    )

    objects = managers.EventManager()

    def __str__(self):
        return f"{self.name} (pk={self.pk})"

    def win(self, team: "TeamEvent") -> bool:
        if self.ended:
            return False
        self.ended = True
        self.save()
        teams: list[Team] = self.teams.all()

        if team not in teams:
            return False
        for _team in teams:
            flag = _team.pk == team.pk
            bets: list[Bet] = _team.bets.filter(is_active=True, payed=False)
            for bet in bets:
                if flag:
                    bet.win()
                else:
                    bet.lose()
        return True


class Team(models.Model):
    class Meta:
        verbose_name_plural = 'Команда'

    objects = managers.DefaultManager()

    def get_name(self) -> str:
        return str(self.names.get(primary=True))

    def __str__(self):
        try:
            return self.get_name()
        except TeamName.DoesNotExist:
            return 'team'


class TeamName(models.Model):
    class Meta:
        verbose_name_plural = 'Названия команд'

    name = models.CharField(max_length=50, verbose_name='Имя')
    verified = models.BooleanField(default=False, verbose_name='Подтвержденный')
    denied = models.BooleanField(default=False, verbose_name='Отказанный')
    primary = models.BooleanField(default=False, verbose_name='Основной')
    team = models.ForeignKey(Team, on_delete=models.CASCADE,
                             related_name='names', verbose_name='Команда')

    objects = managers.DefaultManager()

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<TeamName: {self.team}/{self.name!r}>"


class TeamEvent(models.Model):
    class Meta:
        verbose_name_plural = "Стороны"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="events", verbose_name='Команда')
    first = models.BooleanField(default=True, verbose_name="Хозяин ли площадки?")
    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                              related_name='teams', verbose_name="Событие")
    bet = models.FloatField(default=1.0, verbose_name='Ставка')
    objects = managers.DefaultManager()

    def __str__(self):
        return f"{self.team} - {self.bet}"

    def create_bet(self, money: int, user: TGUser) -> Union["Bet", bool]:
        if user.balance >= money and Bet.objects.filter(user=user, team__event=self.event).count() == 0:
            user.balance = user.balance - money
            user.save()
            return Bet.objects.create(value=self.bet, money=money, user=user, team=self)
        return False


class Bet(models.Model):
    class Meta:
        verbose_name_plural = "Ставки"

    value = models.FloatField(default=1.0, verbose_name="Коэффициент")
    money = models.IntegerField(default=10, verbose_name="Сумма")
    user = models.ForeignKey(TGUser, on_delete=models.CASCADE,
                             related_name='bets', verbose_name="Пользователь")
    team = models.ForeignKey(TeamEvent, on_delete=models.CASCADE,
                             related_name='bets', verbose_name="Команда")
    winner = models.BooleanField(default=False, verbose_name="Выиграл ли")
    is_active = models.BooleanField(default=True, verbose_name="Активна ли ставка")
    payed = models.BooleanField(default=False, verbose_name="Оплачена ли ставка")
    created_date = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")

    objects = managers.DefaultManager()

    def win(self):
        if not self.is_active:
            return False
        self.winner = True
        self.user.balance = self.user.balance + self.value * self.money
        self.user.save()
        self.payed = True
        self.save()
        return True

    def lose(self):
        if not self.is_active:
            return False
        self.payed = True
        self.save()
        return True


class TeamModeration(models.Model):
    class Meta:
        verbose_name_plural = "Заявки"

    name = models.ForeignKey(TeamName, on_delete=models.CASCADE,
                             related_name='applications', verbose_name='Имя на заявку')
    message_id = models.IntegerField(default=0, verbose_name='ID сообщения')

    objects = managers.DefaultManager()
