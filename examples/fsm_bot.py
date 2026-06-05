"""
fsm_bot.py — пример многошагового диалога через FSM.

Бот проводит пользователя через анкету: имя → возраст → город.
Показывает: StatesGroup, StateFilter, fsm.update_data, fsm.clear.

Запуск:
    MAX_TOKEN=<токен> python examples/fsm_bot.py
"""

from __future__ import annotations

import logging
import os

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
from maxio.keyboards import Button

logging.basicConfig(level=logging.INFO)

app = MaxBot(os.environ["MAX_TOKEN"])


# --- Состояния ---

class Form(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_city = State()


# --- Старт анкеты ---

@app.bot_started()
async def on_start(update: Update, bot: Bot) -> None:
    if update.chat_id:
        await bot.send_message(
            "Привет! Напиши /register чтобы заполнить анкету.",
            chat_id=update.chat_id,
        )


@app.message(Command("register"))
async def cmd_register(message: Message, fsm: FSMContext) -> None:
    await fsm.set_state(Form.waiting_name)
    await message.answer("Шаг 1/3 — Как тебя зовут?")


# --- Шаги анкеты ---

@app.message(StateFilter(Form.waiting_name))
async def got_name(message: Message, fsm: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Введи имя текстом.")
        return
    await fsm.update_data(name=name)
    await fsm.set_state(Form.waiting_age)
    await message.answer(f"Отлично, {name}! Шаг 2/3 — Сколько тебе лет?")


@app.message(StateFilter(Form.waiting_age))
async def got_age(message: Message, fsm: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or not (1 <= int(text) <= 120):
        await message.answer("Введи число от 1 до 120.")
        return
    await fsm.update_data(age=int(text))
    await fsm.set_state(Form.waiting_city)
    await message.answer("Шаг 3/3 — Из какого ты города?")


@app.message(StateFilter(Form.waiting_city))
async def got_city(message: Message, fsm: FSMContext) -> None:
    city = (message.text or "").strip()
    if not city:
        await message.answer("Введи название города.")
        return

    data = await fsm.get_data()
    await fsm.clear()

    kb = InlineKeyboard().row(
        Button.callback("✅ Верно", "confirm"),
        Button.callback("🔄 Заново", "restart"),
    )
    await message.answer(
        f"Готово! Вот что получилось:\n\n"
        f"Имя: {data.get('name')}\n"
        f"Возраст: {data.get('age')}\n"
        f"Город: {city}",
        keyboard=kb,
    )


# --- Подтверждение / рестарт после заполнения ---

@app.callback(F.data == "confirm")
async def cb_confirm(callback: Callback) -> None:
    await callback.answer(notification="Сохранено!")
    if callback.message:
        await callback.message.answer("Анкета сохранена. Напиши /register чтобы заполнить снова.")


@app.callback(F.data == "restart")
async def cb_restart(callback: Callback, fsm: FSMContext) -> None:
    await callback.answer(notification="Начинаем заново!")
    await fsm.set_state(Form.waiting_name)
    if callback.message:
        await callback.message.answer("Начинаем заново. Как тебя зовут?")


@app.message(
    Command("cancel"),
    StateFilter(Form.waiting_name, Form.waiting_age, Form.waiting_city),
)
async def cmd_cancel(message: Message, fsm: FSMContext) -> None:
    await fsm.clear()
    await message.answer("Анкета отменена. Напиши /register чтобы начать заново.")


# --- Fallback: не в состоянии FSM ---

@app.message(F.text)
async def fallback(message: Message) -> None:
    await message.answer("Напиши /register чтобы начать анкету.")


if __name__ == "__main__":
    app.run()
