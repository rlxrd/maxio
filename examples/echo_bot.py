"""
echo_bot.py — минимальный рабочий бот на maxio.

Запуск:
    MAX_TOKEN=<токен> python examples/echo_bot.py
"""

import logging

from maxio import Bot, Callback, Command, F, InlineKeyboard, MaxBot, Message, Update
from maxio.fsm.context import FSMContext
from maxio.keyboards import Button

logging.basicConfig(level=logging.INFO)

app = MaxBot(
    token=""
)


# Кнопка «Начать» шлёт отдельное событие bot_started, а не сообщение /start.
@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    keyboard = InlineKeyboard().row(Button.callback("Пинг", "ping"))
    await bot.send_message(
        f"Привет, {update.user.full_name if update.user else 'друг'}!",
        chat_id=update.chat_id,
        keyboard=keyboard,
    )


@app.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer("Это эхо-бот на maxio. Напиши что-нибудь!")


@app.callback(F.data == "ping")
async def on_ping(callback: Callback) -> None:
    await callback.answer(notification="Понг!")
    if callback.message:
        await callback.message.answer("Ты нажал кнопку!")


# Ловит всё остальное и повторяет
@app.message()
async def handler(message: Message, bot: Bot, fsm: FSMContext) -> None:
    me = await bot.get_me()
    await message.answer(f"Привет от @{me.full_name}")


if __name__ == "__main__":
    app.run()
