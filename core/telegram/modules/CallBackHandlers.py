import loguru
from aiogram.utils.exceptions import InvalidQueryID

from .textHandlers import *


@dp.callback_query_handler()
@RegisterMessageUser
async def callback_function(call: types.CallbackQuery, user: models.TGUser, **kwargs):
    loguru.logger.debug(f"Data: {call.data!r}")
    data = call.data.split('.')
    try:
        await bot.answer_callback_query(call.id)
    except InvalidQueryID:
        pass
    try:
        message_id = call.message.message_id
        await bot.delete_message(user.id, message_id)
    except AttributeError:
        pass
    match data:
        case ['commands', 'menu']:
            return await menu(call)
        case ['commands', 'player', 'balance', 'add']:
            return await addBalance(call)
        case ['commands', 'player', 'balance']:
            return await balance(call)
        case ['commands', 'player', 'settings', *params]:
            return await player_settings(call, params=params)
        case ['commands', 'rating']:
            return await rating(call)
        case ['commands', 'bets']:
            return await bets(call)
        case ['commands', 'bet']:
            return await get_bet(call)
        case ['commands', 'bet', *params]:
            params = list(map(int, params))
            keys = ['category', 'subcategory', 'tournament', 'event', 'team']
            params = {key: value for key, value in zip(keys, params)}
            result = await get_bet(call, **params)
            return result
        case ['moderation', 'confirm']:
            return await team_moderation(call.message.message_id, True, call)
        case ['moderation', 'deny']:
            return await team_moderation(call.message.message_id, False, call)
        case [_]:
            return await bot.send_message(
                call.from_user.id,
                text=f'А вот это я точно не знаю что такое. {data[1:]}'
            )
    await bot.send_message(call.from_user.id,
                           text='Извини, я не нашел зарегистрированную функцию, '
                                f'отвечающую за callback-data={call.data!r}')
