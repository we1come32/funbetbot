import json

from aiogram.types import Message, ContentTypes
import loguru
from pprint import pprint
from utils.decorators import FixParameterTypes, Timer, SpecialTypesOfUsers
from core import ds, run


@ds.message_handler(commands=['start'])
@Timer()
@FixParameterTypes(Message)
async def start_function(msg: Message):
    pprint(json.loads(msg.as_json()))
    await msg.answer('Привет, как жизнь друк?')


@ds.message_handler(content_types=ContentTypes.TEXT)
@Timer()
@FixParameterTypes(Message)
@SpecialTypesOfUsers(user=True)
async def function(msg: Message):
    loguru.logger.debug(f"Msg: {msg.text!r} from id{msg.chat.id}")
    await msg.answer("Hello", reply=False)

if __name__ == "__main__":
    run()
