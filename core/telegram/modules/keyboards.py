from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

menuKeyboard = InlineKeyboardMarkup(resize_keyboard=True, inline_keyboard=[
    [
        InlineKeyboardButton(text='💴 Сделать ставку', callback_data='commands.bet'),
    ], [
        InlineKeyboardButton(text='💴 Баланс', callback_data='commands.player.balance'),
        InlineKeyboardButton(text='💼 Ставки', callback_data='commands.bets'),
    ], [
        InlineKeyboardButton(text='🔝 Рейтинг', callback_data='commands.rating'),
        InlineKeyboardButton(text='⚙ Настройки', callback_data='commands.player.settings'),
    ]])
