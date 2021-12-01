from io import StringIO

from aiogram import types
from aiogram.dispatcher import filters
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ForceReply
from aiogram.utils import exceptions
from django.utils import timezone

import config
from core.telegram import dp, bot
from data import models
from utils.decorators import RegisterMessageUser, FixParameterTypes
from .keyboards import *


cache = {}


async def team_moderation(message_id: int, flag: bool, call: types.CallbackQuery):
    try:
        await bot.delete_message(chat_id=config.CHAT_ID, message_id=message_id)
    except exceptions.BadRequest:
        return
    application: models.models.QuerySet = models.TeamModeration.objects.filter(
        message_id=message_id)
    if len(application):
        application: models.TeamModeration = application[0]
        if flag:
            if application.name.team.names.filter(name=application.name.name, verified=True).count() == 0:
                application.name.verified = True
                application.name.save()
                application.delete()
            else:
                application.name.delete()
        else:
            application.name.denied = True
            application.name.save()
            application.delete()
        text = "Спасибо, учтено"
    else:
        text = "Спасибо, эта заявка была утверждена ранее"
    await call.answer(text=text, show_alert=True)


@dp.message_handler(commands=['start'])
async def start_function(msg: Message, **kwargs):
    if msg.text != '/start':
        payload = msg.text.replace('/start ', '')
        if payload.startswith('event'):
            eventID = payload[5:]
            try:
                eventID = int(eventID)
                event = models.Event.objects.get(pk=eventID)
                if event.ended or event.start_time < timezone.now() or event.sports_ru_link == '':
                    raise ValueError
                kwargs = {'category': event.tournament.subcategory.category.pk,
                          'subcategory': event.tournament.subcategory.pk,
                          'tournament': event.tournament.pk,
                          'event': event.pk}
                return await get_bet(msg, **kwargs)
            except [ValueError, models.Event.DoesNotExist]:
                pass
        elif payload.startswith('user'):
            pass
    kb = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    kb.add(KeyboardButton("Меню"))
    kb.add(InlineKeyboardButton("Сделать ставку"))
    c = models.TGUser.objects.filter(id=msg.from_user.id).count()
    if c == 0:
        user = models.TGUser.objects.create(id=msg.from_user.id)
        user.save()
        await msg.answer(
            'Добро пожаловать!\n\nЯ бот, принимающий ставки на спорт.\nСтавить можно только мою валюту - 💴. '
            '\nДля старта я дам тебе 💴 1000, дальше уже сам. Сделай свою первую ставку, только не ошибись, '
            'валюта не бесконечная.',
            reply_markup=kb
        )
    else:
        await msg.answer(
            'Ты уже зарегистрирован в моей системе, с возвращением!\n\nС удовольствием приму твою ставку на спорт',
            reply_markup=kb
        )


@dp.message_handler(commands=['menu', 'меню'])
@RegisterMessageUser
async def menu(msg: Message, user: models.TGUser, **kwargs):
    await bot.send_message(user.id, "Жду вашей ставки", reply_markup=menuKeyboard)


@dp.message_handler(commands=['balance', 'баланс'])
@RegisterMessageUser
async def balance(user: models.TGUser, msg: Message = None, message_id: int = None, **kwargs):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('💴 Сделать ставку', callback_data='commands.bet')]])
    if models.Bet.objects.filter(user=user, is_active=True, payed=False).count() == 0 and user.balance <= 500:
        kb.row(InlineKeyboardButton('➕ Добавить валюту', callback_data='commands.player.balance.add'))
    await bot.send_message(user.id, f"Ваш баланс: 💴 {user.balance}", reply_markup=kb)


@RegisterMessageUser
@dp.message_handler(commands=['add_balance', 'добавить_баланс'])
async def addBalance(user: models.TGUser, msg: Message = None, message_id: int = None, **kwargs):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('💴 Сделать ставку', callback_data='commands.bet')]])
    if models.Bet.objects.filter(user=user, is_active=True, payed=False).count() == 0 and user.balance <= 500:
        user.balance += 500
        user.save()
        message = "❕ Баланс пополнен на 💴 500\n"
    else:
        message = ""
    await bot.send_message(user.id, f"{message}Ваш баланс: 💴 {user.balance}", reply_markup=kb,
                           parse_mode=types.ParseMode.HTML,)


@dp.message_handler(commands=['rating', 'рейтинг'])
@RegisterMessageUser
async def rating(user: models.TGUser, msg: Message = None, message_id: int = None, **kwargs):
    message = "Рейтинг игроков:\n"
    users: list[models.TGUser] = models.TGUser.objects.filter().order_by('-balance').all()
    flag = True
    for number, _ in enumerate(users[:10]):
        _user = await bot.get_chat(_.id)
        _user = _user.values.get('username', f'user{_.id}')
        if _.id == user.id:
            flag = False
        message += f"\n{number+1}) {_user} - {_.balance}"
    if flag:
        message += f"\n\nВаше место в рейтинге - {1 + users.index(user)}"
    await bot.send_message(user.id, message, reply_markup=menuKeyboard)


@dp.message_handler(commands=['bets', 'ставки'])
@RegisterMessageUser
async def bets(user: models.TGUser, msg: Message = None, message_id: int = None, **kwargs):
    def get_info(item: models.Bet, active: bool = False) -> str:
        team: str = item.team.team.get_name()
        if team != 'Ничья':
            team = f"Победа команды {team}"
        if active:
            if not item.is_active or item.payed:
                return ""
        _header = f"Ставка#{item.pk}"
        if item.is_active is False:
            _header += " (Отменён пользователем)"
        if item.payed:
            _header += " (Оплачено)"
        return f"{_header}\n" \
               f"- Вид спорта: {item.team.event.tournament.subcategory.category.name!r}\n" \
               f"- Подкатегория: {item.team.event.tournament.subcategory.name!r}\n" \
               f"- Турнир: {item.team.event.tournament.name!r}\n" \
               f"- Событие: {item.team.event.name!r}\n" \
               f"- Исход на {team!r} с коэфициентом {bet.value}\n" \
               f"- Дата события: {item.team.event.start_time}\n" \
               f"- Дата создания: {item.created_date}\n\n"

    header = "<b>Ваши ставки:</b>\n\n"
    message = ""
    queryBets = models.Bet.objects.filter(user=user).order_by('-pk')
    for bet in queryBets:
        message += get_info(bet)
    if bets:
        file = StringIO(message)
        file.name = f'bets_{user}_{timezone.now()}.txt'
        await bot.send_document(user.id, file)
        message = ""
        for bet in queryBets:
            message += get_info(bet, active=True)
    else:
        header = ""
        message = "Ставки от вашего имени отсутствуют.\nСделаем ставку?"
    await bot.send_message(user.id, header+message, reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton('💴 Баланс', callback_data='commands.player.balance')],
                    [InlineKeyboardButton('💴 Сделать ставку', callback_data='commands.bet')],
                ]
            ), parse_mode=types.ParseMode.HTML,)


@dp.message_handler(commands=['get_id'])
@RegisterMessageUser
async def get_id(msg: Message, **kwargs):
    await msg.answer("Your Telegram ID: `{user_id}`".format(user_id=msg.from_user.id))


@dp.message_handler(commands=['make_bet', 'сделать_ставку'])
@RegisterMessageUser
async def get_bet(msg: Message, user: models.TGUser = None, **kwargs):
    kb = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    category = kwargs.get('category', None)
    subcategory = kwargs.get('subcategory', None)
    tournament = kwargs.get('tournament', None)
    event = kwargs.get('event', None)
    team = kwargs.get('team', None)
    if category is None:
        text = "Выберите категорию событий"
        categories = models.Category.objects.all()
        for tmpCategory in categories:
            if tmpCategory.subcategories.filter(tournaments__events__ended=False).count():
                kb.row(InlineKeyboardButton(tmpCategory.name.upper(),
                                            callback_data=f'commands.bet.{tmpCategory.pk}'))
        kb.row(InlineKeyboardButton("◀️ Назад в меню",
                                    callback_data=f'commands.menu'))
    elif subcategory is None:
        text = "Выберите подкатегорию событий"
        subcategories = models.Category.objects.get(pk=category).subcategories.all()
        for tmpSubCategory in subcategories:
            if tmpSubCategory.tournaments.filter(events__ended=False).count():
                kb.row(InlineKeyboardButton(tmpSubCategory.name.upper(),
                                            callback_data=f'commands.bet.{category}.{tmpSubCategory.pk}'))
        kb.row(InlineKeyboardButton("◀️ Назад",
                                    callback_data=f'commands.bet'))
    elif tournament is None:
        text = "Выберите турнир"
        subcategories = models.SubCategory.objects.get(pk=subcategory).tournaments.all()
        for tmpSubCategory in subcategories:
            if tmpSubCategory.events.filter(ended=False).count():
                kb.row(InlineKeyboardButton(tmpSubCategory.name.upper(),
                                            callback_data=f'commands.bet.{category}.{subcategory}.{tmpSubCategory.pk}'))
        kb.row(InlineKeyboardButton("◀️ Назад",
                                    callback_data=f'commands.bet.{category}'))
    elif event is None:
        text = "Выберите событие:"
        subcategories = models.Tournament.objects.get(pk=tournament).events.filter(
            ~models.models.Q(sports_ru_link="") & ~models.models.Q(parimatch_link=""),
            start_time__gte=timezone.now(),
            ended=False)
        for tmpSubCategory in subcategories:
            kb.row(InlineKeyboardButton(tmpSubCategory.name.upper(),
                                        callback_data=f'commands.bet.{category}.{subcategory}.{tournament}.'
                                                      f'{tmpSubCategory.pk}'))
        kb.row(InlineKeyboardButton("◀️ Назад",
                                    callback_data=f'commands.bet.{category}.{subcategory}'))
    elif team is None:
        _event: models.Event = models.Event.objects.get(pk=event)
        text = "<u>Выберите победителя встречи</u>\n\n"\
               "Информация по событию:\n\n" \
               f"- Вид спорта: {_event.tournament.subcategory.category.name!r}\n" \
               f"- Подкатегория: {_event.tournament.subcategory.name!r}\n" \
               f"- Турнир: {_event.tournament.name!r}\n" \
               f"- Событие: {_event.name!r}\n" \
               f"- Дата: {_event.start_time}"
        subcategories = _event.teams.all()
        for tmpSubCategory in subcategories:
            kb.row(InlineKeyboardButton(f"{tmpSubCategory}",
                                        callback_data=f'commands.bet.{category}.{subcategory}.{tournament}.'
                                                      f'{event}.{tmpSubCategory.pk}'))
        kb.row(InlineKeyboardButton(text='🔗 PariMatch', url=_event.parimatch_link),
               InlineKeyboardButton(text='🔗 Sports.Ru', url=_event.sports_ru_link))
        kb.row(InlineKeyboardButton("◀️ Назад",
                                    callback_data=f'commands.bet.{category}.{subcategory}.{tournament}'))
    else:
        text = f"Введите сумму ставки.\nНапомню, у вас сейчас 💴 {user.balance}:"
        cache[user.id] = kwargs
        await bot.send_message(user.id, text, reply_markup=ForceReply.create(selective=True))
        return
    try:
        message_id = msg.message.message_id
        await bot.delete_message(user.id, message_id)
    except AttributeError:
        pass
    await bot.send_message(user.id, text, reply_markup=kb, parse_mode=types.ParseMode.HTML)


@dp.message_handler(commands=['settings', 'настройки'])
@RegisterMessageUser
async def player_settings(msg: Message, user: models.TGUser, **kwargs):
    await bot.send_message(user.id, "Настройки пока не работают, извините(")


@dp.message_handler()
@RegisterMessageUser
async def custom_message(msg: Message, user: models.TGUser, **kwargs):
    if msg.reply_to_message:
        data = cache.get(user.id, None)
        if data is None:
            return
        try:
            money = float(msg.text.replace(',', '.'))
            if money - int(money*100)/100:
                raise ValueError
            money = int(money)
            if user.balance < money:
                await bot.send_message(user.id, f"У вас на счету нет такой ставки. Введите сумму ставки.\n"
                                                f"Напомню, у вас сейчас 💴 {user.balance}:",
                                       reply_markup=ForceReply.create(selective=True))
                return
            if money < 100:
                await bot.send_message(user.id, f"Минимальная ставка - 💴 100. Введите сумму ставки.\n"
                                                f"Напомню, у вас сейчас 💴 {user.balance}:",
                                       reply_markup=ForceReply.create(selective=True))
                return
        except ValueError:
            await bot.send_message(user.id, f"Сумма ставки должна быть целым числом. Введите сумму ставки.\n"
                                            f"Напомню, у вас сейчас 💴 {user.balance}:",
                                   reply_markup=ForceReply.create(selective=True))
            return
        del cache[user.id]
        team: models.TeamEvent = models.TeamEvent.objects.get(pk=data['team'])
        if bet := team.create_bet(money, user):
            team: str = team.team.get_name()
            if team != 'Ничья':
                team = f"Победа команды {team}"
            await bot.send_message(
                user.id,
                f"✅ <b>Ставка#{bet.pk} успешно сделана!</b>\n\n"
                f"Исход на {team!r} с коэфициентом {bet.value}\n"
                f"Возможный выигрыш <b>💴 {int(bet.money*bet.value)}</b>\n\n"
                f"<code>Подробнее:\n"
                f"- Вид спорта: {bet.team.event.tournament.subcategory.category.name!r}\n"
                f"- Подкатегория: {bet.team.event.tournament.subcategory.name!r}\n"
                f"- Турнир: {bet.team.event.tournament.name!r}\n"
                f"- Событие: {bet.team.event.name!r}\n"
                f"- Дата: {bet.team.event.start_time.strftime('%c')}\n"
                f"- Ставка#{bet.pk}. Исход на {team!r} с коэфициентом {bet.value}</code>",
                parse_mode=types.ParseMode.HTML,
            )
            message = f"Ставка#{bet.pk} успешно сделана!\n" \
                      f"Ваш баланс: 💴 {user.balance}\n" \
                      f"Сделаем ещё ставку?"
        else:
            message = "Извините, Ваша ставка на это событие уже была зарегистрирована.\n" \
                      "Найдем другое событие?"
        await bot.send_message(
            user.id,
            message,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton('💴 Сделать ставку', callback_data='commands.bet')]]
            )
        )
    elif msg.text.lower() in ['сделать ставку']:
        return await get_bet(msg)
    elif msg.text.lower() in ['настройки']:
        return await player_settings(msg)
    elif msg.text.lower() in ['ставки', 'bets']:
        return await bets(msg)
    elif msg.text.lower() in ['rating', 'рейтинг']:
        return await rating(msg)
    elif msg.text.lower() in ['баланс', 'balance']:
        return await balance(msg)
    elif msg.text.lower() in ['меню', 'menu']:
        return await menu(msg)
