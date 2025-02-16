import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters.command import Command
from aiogram.types import BotCommand, Message

import routers.assistant as assistant
# import routers.payments as payments
from config import CONFIG
from core.auth import check_user, free_bonus, registration
from core.logger import ExceptionLoggingMiddleware
from core.utils import COMMAND_LIST, description_meta

bot = Bot(token=CONFIG.TG_TOKEN)
dp = Dispatcher()

dp.message.middleware(ExceptionLoggingMiddleware())

# dp.include_router(payments.router)
dp.include_router(assistant.router)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if not (await check_user(user_id)):
        await registration(user_id)
        await free_bonus(user_id)
        await message.answer(
            """Поздравляю, вы успешно прошли регистрацию! Теперь вам доступно 10 тестовых запросов, увеличить их число вы сможете, оформив подписку.\nCongratulations, you have successfully registered! There are now 10 test queries available to you, and you can increase their number by subscribing."""
        )
    await message.answer(
        """Укажите в одном сообщении тип работ, назначение и площадь объекта. Для внесения дополнительной информации отправьте дополненный запрос заново. 
Вот пример запроса: Нужен проект интерьера лобби для офисного здания площадью 170 кв.м.

Write in one message the type of work, the purpose and the area of the object. To add additional information, send the updated request again.
Here is an example request: We need a lobby interior design for an office building with an area of 170sq.m."""
    )


@dp.message(Command("bonus"))
@description_meta("bonus", "Пароль для новых запросов.\nPassword for new requests.")
async def bonus_command(message: Message):
    if len(inp := message.text.split(" ")) > 1:
        password = inp[1]
        await message.answer(await free_bonus(message.from_user.id, password))
    else:
        await message.answer("Ошибка!\nВведите пароль в сообщении с командой!\n\nWrong!\nEnter the password according to the command! ")


@dp.message(Command("balance"))
@description_meta("balance", "Ваш баланс и тип подписки\nYour balance and subscription type.")
async def balance_command(message: Message):
    result = await check_user(message.from_user.id)
    await message.answer(
        f"Подписка: {result['subscription']}\nКоличество запросов: {result['available_requests']}\n\nSubscription: {result['subscription']}\nNumber of requests: {result['available_requests']}"
    )

@dp.message(Command("my_lang"))
async def get_my_lang(message: Message):
    lang = message.from_user.language_code
    await message.answer(f"Ваш язык -- {lang}")

async def set_command_desc(bot: Bot):
    commands = [BotCommand(command=k, description=v) for k, v in COMMAND_LIST.items()]
    await bot.set_my_commands(commands)
    await bot.set_my_description(
        """Привет, я ассистент AID!
Я помогаю искать талантливых специалистов из мира дизайна и архитектуры.
Просто напишите свой запрос, и я предложу вам подходящих специалистов.

Hi, I'm assistant AID!
I help you find talented specialists from the world of design and architecture.
Just write your request and I will suggest the right specialists for you."""
    )


async def main():
    await set_command_desc(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
