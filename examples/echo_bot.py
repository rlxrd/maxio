"""Пример эхо-бота на maxio.

Запуск:
    MAX_TOKEN=<ваш токен от @MasterBot> python examples/echo_bot.py
"""

from __future__ import annotations

import logging
import os

from maxio import Bot, CallbackQuery, Command, InlineKeyboard, MaxBot, Message
from maxio.keyboards import Button

logging.basicConfig(level=logging.INFO)

app = MaxBot(os.environ["MAX_TOKEN"])


@app.message(Command("start"))
async def start(message: Message, bot: Bot) -> None:
    keyboard = InlineKeyboard().row(Button.callback("Пинг", "ping"))
    await message.answer(
        f"Привет, {message.from_user.full_name if message.from_user else 'друг'}!",
        keyboard=keyboard,
    )


@app.callback()
async def on_ping(query: CallbackQuery) -> None:
    await query.answer(notification="Понг!")


@app.message()
async def echo(message: Message) -> None:
    await message.reply(message.text or "(пустое сообщение)")


if __name__ == "__main__":
    app.run()
