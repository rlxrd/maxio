"""
guess_number_bot.py — игра «Угадай число».

Бот загадывает число от 1 до 100. Игрок угадывает.
Показывает: FSM, fsm.update_data, форматирование текста, InlineKeyboard.

Запуск:
    MAX_TOKEN=<токен> python examples/guess_number_bot.py
"""

from __future__ import annotations

import logging
import random

from maxio import (
    Bot,
    Callback,
    Command,
    F,
    FSMContext,
    InlineKeyboard,
    MaxBot,
    Message,
    State,
    StateFilter,
    StatesGroup,
    Update,
)
from maxio.enums import Intent, TextFormat
from maxio.keyboards import Button

logging.basicConfig(level=logging.INFO)

app = MaxBot("")

MAX_ATTEMPTS = 7


class Game(StatesGroup):
    guessing = State()


def _attempts_bar(attempts_left: int) -> str:
    filled = MAX_ATTEMPTS - attempts_left
    return "🟥" * filled + "🟩" * attempts_left


def _start_keyboard() -> InlineKeyboard:
    return InlineKeyboard().row(Button.callback("🎮 Играть", "play"))


def _hint_keyboard() -> InlineKeyboard:
    return (
        InlineKeyboard()
        .row(
            Button.callback("🔼 Больше", "hint:higher", intent=Intent.POSITIVE),
            Button.callback("🔽 Меньше", "hint:lower", intent=Intent.NEGATIVE),
        )
        .row(Button.callback("🏳 Сдаться", "give_up", intent=Intent.NEGATIVE))
    )


@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    if update.chat_id:
        await bot.send_message(
            "👋 **Привет!** Я загадаю число от **1 до 100**, а ты угадаешь.\n\n"
            f"У тебя будет **{MAX_ATTEMPTS} попыток**.",
            chat_id=update.chat_id,
            keyboard=_start_keyboard(),
            format=TextFormat.MARKDOWN,
        )


@app.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 **Привет!** Я загадаю число от **1 до 100**, а ты угадаешь.\n\n"
        f"У тебя будет **{MAX_ATTEMPTS} попыток**.",
        keyboard=_start_keyboard(),
        format=TextFormat.MARKDOWN,
    )


@app.callback(F.data == "play")
async def cb_play(callback: Callback, fsm: FSMContext) -> None:
    number = random.randint(1, 100)
    await fsm.set_state(Game.guessing)
    await fsm.update_data(number=number, attempts=MAX_ATTEMPTS)
    await callback.answer(notification="Игра началась!")
    if callback.message:
        await callback.message.answer(
            f"🎲 Число загадано! Попыток: **{MAX_ATTEMPTS}**\n\n"
            f"{_attempts_bar(MAX_ATTEMPTS)}\n\n"
            "Введи число от **1** до **100**:",
            format=TextFormat.MARKDOWN,
        )


@app.message(StateFilter(Game.guessing), F.text)
async def got_guess(message: Message, fsm: FSMContext) -> None:
    text = (message.text or "").strip()

    if not text.isdigit():
        await message.answer("Введи **целое число** от 1 до 100.", format=TextFormat.MARKDOWN)
        return

    guess = int(text)
    if not 1 <= guess <= 100:
        await message.answer("Число должно быть от **1** до **100**.", format=TextFormat.MARKDOWN)
        return

    data = await fsm.get_data()
    number: int = data["number"]
    attempts: int = data["attempts"] - 1
    await fsm.update_data(attempts=attempts)

    if guess == number:
        used = MAX_ATTEMPTS - attempts
        await fsm.clear()
        await message.answer(
            f"🎉 **Правильно!** Число было **{number}**.\n"
            f"Угадал с **{used}** {'попытки' if used == 1 else 'попыток'}!\n\n"
            f"{_attempts_bar(0)}",
            keyboard=_start_keyboard(),
            format=TextFormat.MARKDOWN,
        )
        return

    if attempts == 0:
        await fsm.clear()
        await message.answer(
            f"💀 **Попытки кончились!** Загаданное число — **{number}**.\n\n"
            f"{_attempts_bar(0)}",
            keyboard=_start_keyboard(),
            format=TextFormat.MARKDOWN,
        )
        return

    hint = "📈 Моё число **больше**" if number > guess else "📉 Моё число **меньше**"
    await message.answer(
        f"{hint} чем {guess}.\n\n"
        f"Осталось попыток: **{attempts}**\n"
        f"{_attempts_bar(attempts)}",
        keyboard=_hint_keyboard(),
        format=TextFormat.MARKDOWN,
    )


@app.callback(F.data.startswith("hint:"))
async def cb_hint(callback: Callback, fsm: FSMContext) -> None:
    data = await fsm.get_data()
    if not data:
        await callback.answer(notification="Сначала начни игру!")
        return
    number: int = data["number"]
    direction = (callback.payload or "").split(":")[1]
    if direction == "higher":
        hint = f"📈 Моё число **больше** {number // 2}"
    else:
        hint = f"📉 Моё число **меньше** {number // 2 + 50}"
    await callback.answer(notification="Подсказка!")
    if callback.message:
        await callback.message.answer(hint, format=TextFormat.MARKDOWN)


@app.callback(F.data == "give_up")
async def cb_give_up(callback: Callback, fsm: FSMContext) -> None:
    data = await fsm.get_data()
    number = data.get("number", "?")
    await fsm.clear()
    await callback.answer(notification="Игра окончена")
    if callback.message:
        await callback.message.answer(
            f"🏳 Сдался! Загаданное число было **{number}**.",
            keyboard=_start_keyboard(),
            format=TextFormat.MARKDOWN,
        )


@app.message(Command("stop"), StateFilter(Game.guessing))
async def cmd_stop(message: Message, fsm: FSMContext) -> None:
    data = await fsm.get_data()
    number = data.get("number", "?")
    await fsm.clear()
    await message.answer(
        f"🏳 Игра остановлена. Загаданное число было **{number}**.",
        keyboard=_start_keyboard(),
        format=TextFormat.MARKDOWN,
    )


@app.message(F.text)
async def fallback(message: Message, fsm: FSMContext) -> None:
    state = await fsm.get_state()
    if state is None:
        await message.answer(
            "Напиши /start чтобы начать игру.",
            keyboard=_start_keyboard(),
        )


if __name__ == "__main__":
    app.run()
