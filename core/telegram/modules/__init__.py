import asyncio

import loguru
from aiogram import types
from aiogram.dispatcher import FSMContext, filters
from aiogram.types import KeyboardButton, InlineKeyboardMarkup, Message, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import exceptions
from aiogram.utils.exceptions import InvalidQueryID
from aiogram.utils.helper import ListItem, HelperMode, Helper

from core.telegram import dp, bot
from data import models
from utils.decorators import RegisterMessageUser, FixParameterTypes


class States(Helper):
    mode = HelperMode.snake_case

    MENU = ListItem()
    TYPES = ListItem()
    GAMES = ListItem()
    TOURNAMENT = ListItem()
    MAPS = ListItem()
    SIDE = ListItem()


loop = asyncio.get_event_loop()


menuKeyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
menuKeyboard.add(InlineKeyboardButton(text='Баланс', callback_data='commands.player.balance'))
menuKeyboard.add(InlineKeyboardButton(text='Сделать ставку', callback_data='commands.bet'))
menuKeyboard.add(InlineKeyboardButton(text='Рейтинг', callback_data='commands.rating'))
menuKeyboard.add(InlineKeyboardButton(text='Настройки', callback_data='commands.player.settings'))


async def team_moderation(message_id: int, flag: bool, call: types.CallbackQuery):
    try:
        await bot.delete_message(chat_id=621629634, message_id=message_id)
    except exceptions.BadRequest:
        return
    application: models.models.QuerySet = models.TeamModeration.objects.filter(
        message_id=message_id)
    if len(application):
        application: models.TeamModeration = application[0]
        application.name.verified = True
        application.name.save()
        application.delete()
        text = "Спасибо, учтено"
    else:
        text = "Спасибо, эта заявка была утверждена ранее"
    await call.answer(text=text, show_alert=True)


@dp.message_handler(commands=['start'])
async def start_function(msg: Message):
    kb = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    kb.add(KeyboardButton("Меню"))
    kb.add(InlineKeyboardButton("Сделать ставку"))
    c = models.TGUser.objects.filter(id=msg.from_user.id).count()
    if c == 0:
        user = models.TGUser.objects.create(id=msg.from_user.id)
        user.save()
        await msg.answer(
            'Добро пожаловать!\n\nЯ бот, принимающий ставки на спорт.\nСтавить можно только мою валюту - "Вирт". '
            '\nДля старта я дам тебе 1000 Вирт, дальше уже сам. Сделай свою первую ставку, только не ошибись, '
            'валюта не бесконечная.',
            reply_markup=kb
        )
    else:
        await msg.answer(
            'Ты уже зарегистрирован в моей системе, с возвращением!\n\nС удовольствием приму твою ставку на спорт',
            reply_markup=kb
        )


@dp.message_handler(filters.Text(equals=['меню', 'menu'], ignore_case=True), state='*')
@dp.message_handler(commands=['menu', 'меню'], state='*')
@FixParameterTypes(Message)
@RegisterMessageUser
async def menu(msg: Message, user: models.TGUser, state: FSMContext):
    global menuKeyboard
    await state.set_state('menu')
    await msg.answer('Жду вашей ставки', reply_markup=menuKeyboard)


@dp.message_handler(filters.Text(equals=['баланс', 'balance'], ignore_case=True), state='*')
@RegisterMessageUser
async def balance(user: models.TGUser, state: FSMContext, msg: Message = None, message_id: int = None):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('Сделать ставку', callback_data='commands.bet'))
    await bot.send_message(user.id, f"Ваш баланс: {user.balance} Вирт", reply_markup=kb)


@dp.message_handler(filters.Text(equals=['rating', 'рейтинг'], ignore_case=True), state='*')
@RegisterMessageUser
async def rating(user: models.TGUser, state: FSMContext, msg: Message = None, message_id: int = None):
    message = "Рейтинг игроков:\n"
    users: list[models.TGUser] = models.TGUser.objects.filter().order_by('balance').all()
    flag = True
    for number, _ in enumerate(users[:10]):
        _user = await bot.get_chat(_.id)
        _user = _user.values.get('username', f'user{_.id}')
        if _.id == user.id:
            flag = False
        message += f"\n{number+1}) {_user}"
    if flag:
        message += f"\n\nВаше место в рейтинге - {1 + users.index(user)}"
    await bot.send_message(user.id, message, reply_markup=menuKeyboard)


@dp.message_handler(commands=['get_id'])
@RegisterMessageUser
async def get_id(msg: Message, **kwargs):
    await msg.answer("Your id: {user_id}".format(user_id=msg.from_user.id))


@dp.message_handler(commands=['get_state'])
@RegisterMessageUser
async def get_id(msg: Message, **kwargs):
    state = dp.current_state(user=msg.from_user.id)
    await msg.answer("Your state: {state}".format(state=await state.get_state()))


@dp.message_handler(filters.Text(equals=["сделать ставку", "ставку"], ignore_case=True))
@RegisterMessageUser
async def get_bet(msg: Message, user: models.TGUser, state: FSMContext):
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state('types')
    kb = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row(InlineKeyboardButton('Баланс', callback_data='commands.player.balance'))
    await bot.send_message(user.id, "А ок ща", reply_markup=kb)


@dp.message_handler(filters.Text(equals=['настройки'], ignore_case=True), state=0)
@RegisterMessageUser
async def player_settings(msg: Message, user: models.TGUser, state: FSMContext):
    await bot.send_message(user.id, "Настройки пока не работают, извините(")


@dp.callback_query_handler()
async def callback_function(call: types.CallbackQuery):
    loguru.logger.debug(f"Data: {call.data!r}")
    data = call.data.split('.')
    try:
        await bot.answer_callback_query(call.id)
    except InvalidQueryID:
        pass
    match data:
        case ['commands', 'player', 'balance']:
            return await balance(call)
        case ['commands', 'player', 'settings']:
            return await player_settings(call)
        case ['commands', 'rating']:
            return await rating(call)
        case ['commands', 'bet']:
            return await get_bet(call)
        case ['commands', 'bet', category]:
            return await bot.send_message(
                call.from_user.id,
                text='Я не знаю что это такое. '
                     'Если бы я знал что это такое... '
                     f'Я не знаю что это такое\n\n{category}'
            )
        case ['moderation', 'confirm']:
            return await team_moderation(call.message.message_id, True, call)
        case ['moderation', 'deny']:
            return await team_moderation(call.message.message_id, False, call)
        case [_]:
            return await bot.send_message(
                call.from_user.id,
                text=f'А вот это я точно не знаю что такое. {data[1:]}'
            )
    await bot.send_message(
        call.from_user.id,
        text=f'Извини, я не нашел зарегистрированную функцию, отвечающую за callback-data={call.data!r}'
    )

loguru.logger.debug("Функции в Dispatcher зарегистрировано "
                    f"Callback handlers - {len(dp.callback_query_handlers.handlers)}, "
                    f"Message handler - {len(dp.message_handlers.handlers)}")
